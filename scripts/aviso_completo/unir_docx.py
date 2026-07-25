#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unir_docx.py — separação do Anexo I, titulação dos anexos e união dos DOCX.

Por que docxcompose e não concatenação de XML: unir dois DOCX exige remapear
relacionamentos de imagem, definições de numeração, estilos homônimos e ids de
seção. Emendar `word/document.xml` "na mão" quebra exatamente o que este módulo
existe para proteger — o brasão do cabeçalho, as listas numeradas do aviso e as
tabelas do TR. docxcompose faz esse remapeamento; o que ele não faz (unificar o
timbre entre partes de origens diferentes) está resolvido aqui em
`unificar_timbre`, e não por edição bruta de texto.

Nenhuma função grava sobre arquivo de entrada: tudo sai em caminho novo.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docx_cmi"))

from ocorrencias import Registro
from util_ooxml import (
    W_NS,
    assinatura_semantica_cabecalho,
    exigir_python_docx,
    qn,
    texto_paragrafo,
)

ETAPA = "montagem do DOCX"

MSG_SEM_COMPOSE = (
    "A biblioteca docxcompose não está instalada. A união dos DOCX do aviso "
    "completo depende dela.\n"
    "Instale com:  python -m pip install -r requirements-docx.txt"
)

# Título do Anexo I na minuta-mãe do aviso: vive dentro de uma caixa de texto.
RE_TITULO_HABILITACAO = re.compile(
    r"DOCUMENTA[ÇC][ÃA]O\s+EXIGIDA\s+PARA\s+HABILITA[ÇC][ÃA]O|^\s*ANEXO\s+I\b",
    re.IGNORECASE)

ESTILOS_TITULO_ANEXO = ("CMI Titulo do Documento", "CMI Titulo 1", "Heading 1",
                        "Título 1")


def exigir_docxcompose():
    try:
        from docxcompose.composer import Composer  # noqa: F401
    except ImportError as erro:  # pragma: no cover - depende do ambiente
        raise RuntimeError(MSG_SEM_COMPOSE) from erro
    from docxcompose.composer import Composer
    return Composer


# --------------------------------------------------------------------------- #
# Separação do Anexo I
# --------------------------------------------------------------------------- #

def _texto_completo(elemento) -> str:
    """Texto de um bloco, inclusive o que está dentro de caixas de texto."""
    return "".join(t.text or "" for t in elemento.iter(qn("w:t")))


def _indice_do_anexo_i(body) -> Optional[int]:
    """Posição do bloco que abre o Anexo I dentro do corpo do aviso."""
    for indice, filho in enumerate(body):
        if filho.tag != qn("w:p"):
            continue
        if RE_TITULO_HABILITACAO.search(_texto_completo(filho).strip()):
            return indice
    return None


def _remover_intervalo(documento, inicio: int, fim: Optional[int]) -> None:
    """Remove blocos do corpo, preservando sempre o `w:sectPr` final."""
    body = documento.element.body
    filhos = list(body)
    fim = len(filhos) if fim is None else fim
    for filho in filhos[inicio:fim]:
        if filho.tag == qn("w:sectPr"):
            continue
        body.remove(filho)


def dividir_aviso(aviso: Path, destino_aviso: Path, destino_habilitacao: Path,
                  registro: Registro) -> tuple[Path, Optional[Path]]:
    """
    Separa a minuta do aviso em duas peças: o aviso e o Anexo I de habilitação.

    O Anexo I já está incorporado à minuta-mãe. Ele não é recriado nem duplicado:
    é apenas recortado, para que possa ser publicado também como arquivo próprio.
    Se o ponto de corte não for reconhecido, o Anexo I permanece dentro do aviso —
    é melhor um anexo sem arquivo separado do que um corte no lugar errado.
    """
    exigir_python_docx()
    from docx import Document

    documento = Document(str(aviso))
    indice = _indice_do_anexo_i(documento.element.body)
    if indice is None:
        registro.alerta(
            ETAPA,
            "O início do Anexo I não foi reconhecido na minuta do aviso. O anexo "
            "de habilitação segue incorporado ao aviso no documento único, e o "
            "arquivo separado do Anexo I não foi gerado.",
            origem=aviso.name,
        )
        destino_aviso.parent.mkdir(parents=True, exist_ok=True)
        documento.save(str(destino_aviso))
        return destino_aviso, None

    _remover_intervalo(documento, indice, None)
    destino_aviso.parent.mkdir(parents=True, exist_ok=True)
    documento.save(str(destino_aviso))

    habilitacao = Document(str(aviso))
    _remover_intervalo(habilitacao, 0, indice)
    destino_habilitacao.parent.mkdir(parents=True, exist_ok=True)
    habilitacao.save(str(destino_habilitacao))

    registro.informacao(
        ETAPA,
        "Anexo I separado do corpo do aviso a partir da própria minuta-mãe "
        "(nenhum Anexo I novo foi criado).",
        origem=aviso.name,
    )
    registro.informacao(
        ETAPA,
        "O Anexo I mantém o título que a minuta-mãe já traz ('DOCUMENTAÇÃO "
        "EXIGIDA PARA HABILITAÇÃO', em caixa de texto) e não recebe o rótulo "
        "'ANEXO I — ...' aplicado aos demais anexos: acrescentá-lo duplicaria o "
        "título do anexo. Uniformizar isso depende de revisão da minuta-mãe.",
        origem=aviso.name,
    )
    return destino_aviso, destino_habilitacao


# --------------------------------------------------------------------------- #
# Titulação dos anexos
# --------------------------------------------------------------------------- #

def _estilo_disponivel(documento, preferidos: Iterable[str]) -> Optional[str]:
    nomes = {estilo.name for estilo in documento.styles}
    return next((nome for nome in preferidos if nome in nomes), None)


def inserir_titulo_anexo(caminho: Path, destino: Path, rotulo: str,
                         registro: Registro) -> Path:
    """
    Insere o rótulo do anexo no topo do componente, iniciando em nova página.

    Esse rótulo é estrutura de MONTAGEM, não conteúdo do documento anexado: sem
    ele o leitor do aviso não sabe qual anexo está lendo. Ele é acrescentado
    apenas na cópia usada na montagem — a minuta e o TR de origem não são
    tocados — e fica registrado no relatório como acréscimo autorizado.
    """
    exigir_python_docx()
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    documento = Document(str(caminho))
    if _ja_titulado(documento, rotulo):
        registro.informacao(
            ETAPA, f"'{rotulo}' já constava do componente; título não duplicado.",
            origem=caminho.name)
        destino.parent.mkdir(parents=True, exist_ok=True)
        documento.save(str(destino))
        return destino

    paragrafo = documento.add_paragraph(rotulo)
    documento.element.body.insert(0, paragrafo._p)

    estilo = _estilo_disponivel(documento, ESTILOS_TITULO_ANEXO)
    if estilo:
        paragrafo.style = documento.styles[estilo]
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.page_break_before = True
    paragrafo.paragraph_format.keep_with_next = True
    for run in paragrafo.runs:
        run.bold = True

    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.save(str(destino))
    return destino


def _ja_titulado(documento, rotulo: str) -> bool:
    """Evita rótulo duplicado quando o componente já abre com o próprio anexo."""
    alvo = re.sub(r"\s+", " ", rotulo).strip().upper()
    numeral = alvo.split("—")[0].strip()
    for paragrafo in list(documento.paragraphs)[:3]:
        texto = re.sub(r"\s+", " ", texto_paragrafo(paragrafo)).strip().upper()
        if texto.startswith(numeral) and numeral:
            return True
    return False


# --------------------------------------------------------------------------- #
# Timbre
# --------------------------------------------------------------------------- #

@dataclass
class DivergenciaTimbre:
    arquivo: str
    detalhe: str


def _assinatura_do_timbre(caminho: Path) -> dict[str, str]:
    import zipfile
    assinaturas: dict[str, str] = {}
    with zipfile.ZipFile(caminho, "r") as pacote:
        for nome in sorted(pacote.namelist()):
            if re.fullmatch(r"word/(header|footer)\d*\.xml", nome):
                assinaturas[nome] = assinatura_semantica_cabecalho(pacote.read(nome))
    return assinaturas


def _midia_do_timbre(pacote) -> set[str]:
    """Imagens referenciadas pelos `.rels` de cabeçalho e rodapé — o brasão."""
    alvos: set[str] = set()
    for nome in pacote.namelist():
        if not re.fullmatch(r"word/_rels/(header|footer)\d*\.xml\.rels", nome):
            continue
        xml = pacote.read(nome).decode("utf-8", "ignore")
        for alvo in re.findall(r'Target="([^"]*media/[^"]+)"', xml):
            alvos.add("word/media/" + alvo.split("media/")[-1])
    return alvos


def timbre_intacto(origem: Path, destino: Path) -> tuple[bool, list[str]]:
    """
    Compara o TIMBRE do documento montado com o da minuta do aviso.

    Diferente da checagem do módulo de padronização, esta ignora as imagens do
    corpo. No aviso completo elas crescem por construção: o TR e a minuta de
    contrato trazem as suas. Tratar imagem nova do corpo como violação do timbre
    bloquearia toda montagem com anexo ilustrado — o que importa aqui é que
    cabeçalho, rodapé e brasão continuem sendo os da Câmara.
    """
    import zipfile

    divergencias: list[str] = []
    with zipfile.ZipFile(origem) as pacote_origem, \
            zipfile.ZipFile(destino) as pacote_destino:
        assinaturas_origem = {
            nome: assinatura_semantica_cabecalho(pacote_origem.read(nome))
            for nome in pacote_origem.namelist()
            if re.fullmatch(r"word/(header|footer)\d*\.xml", nome)
        }
        assinaturas_destino = {
            nome: assinatura_semantica_cabecalho(pacote_destino.read(nome))
            for nome in pacote_destino.namelist()
            if re.fullmatch(r"word/(header|footer)\d*\.xml", nome)
        }
        for nome, assinatura in assinaturas_origem.items():
            if nome not in assinaturas_destino:
                divergencias.append(f"Cabeçalho/rodapé ausente no montado: {nome}")
            elif assinaturas_destino[nome] != assinatura:
                divergencias.append(f"Cabeçalho/rodapé alterado: {nome}")

        midia_origem = _midia_do_timbre(pacote_origem)
        midia_destino = _midia_do_timbre(pacote_destino)
        for nome in sorted(midia_origem):
            if nome not in midia_destino:
                divergencias.append(f"Imagem do timbre ausente: {nome}")
                continue
            if pacote_origem.read(nome) != pacote_destino.read(nome):
                divergencias.append(f"Imagem do timbre alterada: {nome}")
    return not divergencias, divergencias


def conferir_timbres(referencia: Path, partes: Iterable[Path],
                     registro: Registro) -> list[DivergenciaTimbre]:
    """
    Compara o timbre de cada componente com o do aviso.

    Componente com timbre diferente não é rejeitado — as minutas da Câmara têm
    gerações diferentes de cabeçalho —, mas a divergência é reportada e o timbre
    do aviso prevalece no documento único (ver `unificar_timbre`). Timbre de
    outro órgão é achado grave e precisa aparecer no relatório.
    """
    esperadas = set(_assinatura_do_timbre(referencia).values())
    divergencias: list[DivergenciaTimbre] = []
    for parte in partes:
        if Path(parte).resolve() == Path(referencia).resolve():
            continue
        assinaturas = set(_assinatura_do_timbre(Path(parte)).values())
        if assinaturas and not (assinaturas & esperadas):
            divergencia = DivergenciaTimbre(
                Path(parte).name,
                "cabeçalho/rodapé diferente do timbre do aviso",
            )
            divergencias.append(divergencia)
            registro.alerta(
                ETAPA,
                f"O componente '{Path(parte).name}' traz cabeçalho/rodapé "
                "diferente do timbre da minuta do aviso. No documento único "
                "prevalece o timbre do aviso; confira se o componente veio de "
                "modelo da Câmara.",
                origem=Path(parte).name,
            )
    return divergencias


def unificar_timbre(documento, registro: Registro) -> int:
    """
    Faz todas as seções herdarem o cabeçalho e o rodapé da primeira.

    Cada componente traz suas próprias referências de cabeçalho. Mantidas, o
    documento final alternaria timbres de gerações diferentes página a página.
    Seção sem referência herda a anterior (ECMA-376), então remover as
    referências das seções seguintes é o caminho que deixa o timbre oficial do
    aviso valendo do começo ao fim, sem tocar em `header*.xml`.
    """
    body = documento.element.body
    secoes = list(body.iter(qn("w:sectPr")))
    removidas = 0
    for secao in secoes[1:]:
        for tag in ("w:headerReference", "w:footerReference"):
            for referencia in list(secao.findall(qn(tag))):
                secao.remove(referencia)
                removidas += 1
    if removidas:
        registro.informacao(
            ETAPA,
            f"{removidas} referência(s) de cabeçalho/rodapé de seções anexas "
            "removida(s): todas as seções passam a usar o timbre oficial do "
            "aviso.",
        )
    return removidas


# --------------------------------------------------------------------------- #
# União
# --------------------------------------------------------------------------- #

def _fechar_secao(caminho: Path, destino: Path) -> Path:
    """
    Copia o componente fixando a própria configuração de página em uma quebra
    de seção de parágrafo.

    Necessário porque o docxcompose descarta o `w:sectPr` de corpo do documento
    anexado e mantém só o do mestre: sem este passo, um anexo em paisagem — um
    quadro de itens largo, por exemplo — sairia em retrato no documento único,
    com a tabela cortada. Levando o `sectPr` para dentro do `w:pPr` do último
    parágrafo, a configuração passa a valer para o conteúdo daquele componente e
    sobrevive à união (ECMA-376, §17.6.17).
    """
    import copy

    from docx import Document

    documento = Document(str(caminho))
    body = documento.element.body
    sectPr = body.find(qn("w:sectPr"))
    if sectPr is None:
        return caminho

    ultimos = [filho for filho in body if filho.tag == qn("w:p")]
    if ultimos:
        paragrafo = ultimos[-1]
    else:
        paragrafo = documento.add_paragraph()._p
    pPr = paragrafo.find(qn("w:pPr"))
    if pPr is None:
        pPr = paragrafo.makeelement(qn("w:pPr"), {})
        paragrafo.insert(0, pPr)
    if pPr.find(qn("w:sectPr")) is None:
        pPr.append(copy.deepcopy(sectPr))

    documento.save(str(destino))
    return destino


def unir(mestre: Path, partes: list[Path], destino: Path,
         registro: Registro) -> Path:
    """Une o aviso e os anexos em um único DOCX, preservando o timbre do aviso."""
    import tempfile

    Composer = exigir_docxcompose()
    exigir_python_docx()
    from docx import Document

    mestre = Path(mestre)
    with tempfile.TemporaryDirectory() as temporario:
        area = Path(temporario)
        preparado = _fechar_secao(mestre, area / f"00_{mestre.name}")
        documento = Document(str(preparado))
        composer = Composer(documento)
        for indice, parte in enumerate(partes, start=1):
            parte = Path(parte)
            composer.append(Document(str(
                _fechar_secao(parte, area / f"{indice:02d}_{parte.name}"))))

        unificar_timbre(composer.doc, registro)

        destino.parent.mkdir(parents=True, exist_ok=True)
        composer.save(str(destino))

    registro.informacao(
        ETAPA,
        f"Documento único montado com {len(partes) + 1} componente(s): "
        + ", ".join([mestre.name] + [Path(p).name for p in partes]),
        origem=destino.name,
    )
    return destino


def marcar_rascunho(caminho: Path, texto: str, registro: Registro) -> None:
    """
    Carimba o aviso de trabalho no topo do documento e no rodapé de cada seção.

    Usado só quando o usuário pede expressamente um rascunho apesar das
    pendências. Rascunho sem marca é o pior resultado possível: um documento com
    defeito conhecido circulando como se estivesse pronto.
    """
    exigir_python_docx()
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    documento = Document(str(caminho))
    paragrafo = documento.add_paragraph()
    documento.element.body.insert(0, paragrafo._p)
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragrafo.add_run(texto)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    documento.save(str(caminho))
    registro.informacao(
        ETAPA, f"Documento marcado como rascunho: '{texto}'.", origem=caminho.name)
