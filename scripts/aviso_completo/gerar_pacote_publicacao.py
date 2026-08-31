#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_pacote_publicacao.py — PDF, anexos separados e ZIP de publicação.

A conversão para PDF é OPCIONAL por decisão de projeto: o repositório roda com a
biblioteca padrão do Python mais `python-docx`/`docxcompose`, e nenhum conversor
é dependência. Quando há LibreOffice ou Word na máquina, o PDF sai; quando não
há, o pacote é gerado só em DOCX e o relatório diz que não houve conversão — o
que não pode acontecer é o relatório afirmar um PDF que não existe.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docx_cmi"))

from numerar_anexos import PlanoAnexos
from ocorrencias import Registro

# A detecção do conversor e a conversão em si moram em `docx_cmi`, camada de
# baixo deste módulo, e são compartilhadas com a validação visual da
# padronização documental — havia duas cópias da mesma lista de caminhos, e
# corrigir uma delas (perfil isolado do LibreOffice) não alcançava a outra.
from validacao_visual_docx import (  # noqa: F401  (reexportados para quem importa daqui)
    CAMINHOS_LIBREOFFICE,
    SCRIPT_WORD,
    Conversor,
    _converter_libreoffice,
    _converter_word,
    detectar_conversor,
)

ETAPA = "pacote de publicação"

NOME_DOCUMENTO_UNICO = "AVISO_DISPENSA_COMPLETO"
NOME_AVISO_PUBLICACAO = "AVISO_DE_CONTRATACAO_DIRETA"


@dataclass
class Pacote:
    """Arquivos produzidos para publicação."""

    documento_unico_docx: Optional[Path] = None
    documento_unico_pdf: Optional[Path] = None
    componentes_docx: list[Path] = field(default_factory=list)
    componentes_pdf: list[Path] = field(default_factory=list)
    zip: Optional[Path] = None
    manifesto_arquivos: Optional[Path] = None
    conversor: str = "nenhum"

    def como_dicionario(self) -> dict[str, object]:
        return {
            "documento_unico_docx": _texto(self.documento_unico_docx),
            "documento_unico_pdf": _texto(self.documento_unico_pdf),
            "componentes_docx": [_texto(p) for p in self.componentes_docx],
            "componentes_pdf": [_texto(p) for p in self.componentes_pdf],
            "zip": _texto(self.zip),
            "conversor_pdf": self.conversor,
        }


def _texto(caminho: Optional[Path]) -> Optional[str]:
    return str(caminho) if caminho else None


# --------------------------------------------------------------------------- #
# Conversão para PDF
# --------------------------------------------------------------------------- #

def converter_pdf(entrada: Path, destino: Path, conversor: Conversor,
                  registro: Registro) -> Optional[Path]:
    """Converte um DOCX em PDF. Falha de conversão é alerta, nunca bloqueio."""
    if not conversor.disponivel():
        return None
    try:
        if conversor.nome == "libreoffice":
            gerado = _converter_libreoffice(conversor, entrada, destino.parent)
            if gerado and gerado != destino:
                shutil.move(str(gerado), str(destino))
                gerado = destino
        else:
            gerado = _converter_word(entrada, destino)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as erro:
        registro.alerta(
            ETAPA,
            f"Conversão para PDF de '{entrada.name}' falhou ({conversor.nome}): "
            f"{erro}. O DOCX foi mantido.",
            origem=entrada.name,
        )
        return None
    if gerado is None:
        registro.alerta(
            ETAPA, f"Conversão para PDF de '{entrada.name}' não produziu arquivo.",
            origem=entrada.name)
    return gerado


# --------------------------------------------------------------------------- #
# Pacote
# --------------------------------------------------------------------------- #

def _nomes_de_publicacao(plano: PlanoAnexos) -> list[tuple[str, str]]:
    """(chave do componente, nome de publicação) na ordem do pacote."""
    nomes = [("aviso", f"01_{NOME_AVISO_PUBLICACAO}")]
    for anexo in plano.anexos:
        nomes.append((anexo.chave, f"{anexo.ordem + 1:02d}_{anexo.nome_publicacao}"))
    return nomes


def gerar(documento_unico: Path, componentes: dict[str, Path], plano: PlanoAnexos,
          pasta_saida: Path, relatorio_md: Optional[Path], registro: Registro,
          converter: bool = True) -> Pacote:
    """Monta a pasta de saída e o ZIP de publicação com nomes autoexplicativos."""
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    pacote = Pacote(documento_unico_docx=Path(documento_unico))

    conversor = detectar_conversor() if converter else Conversor("nenhum")
    pacote.conversor = conversor.nome
    if not converter:
        registro.informacao(
            ETAPA,
            "Conversão para PDF não solicitada (--sem-pdf): o pacote saiu "
            "somente em DOCX.",
        )
    elif not conversor.disponivel():
        registro.alerta(
            ETAPA,
            "Nenhum conversor de PDF disponível no ambiente (LibreOffice ou "
            "Word). O pacote foi gerado somente em DOCX e a conversão para PDF "
            "não foi executada.",
        )

    pdf_unico = pasta_saida / f"{NOME_DOCUMENTO_UNICO}.pdf"
    pacote.documento_unico_pdf = converter_pdf(
        Path(documento_unico), pdf_unico, conversor, registro)

    pasta_anexos = pasta_saida / "anexos_separados"
    pasta_anexos.mkdir(parents=True, exist_ok=True)
    mapa_publicacao: dict[str, tuple[Path, Optional[Path]]] = {}

    for chave, nome in _nomes_de_publicacao(plano):
        origem = componentes.get(chave)
        if origem is None or not Path(origem).exists():
            continue
        docx_destino = pasta_anexos / f"{nome}.docx"
        shutil.copyfile(origem, docx_destino)
        pacote.componentes_docx.append(docx_destino)
        pdf_destino = converter_pdf(
            docx_destino, pasta_anexos / f"{nome}.pdf", conversor, registro)
        if pdf_destino:
            pacote.componentes_pdf.append(pdf_destino)
        mapa_publicacao[chave] = (docx_destino, pdf_destino)

    manifesto = {
        "documento_unico": {
            "docx": Path(documento_unico).name,
            "pdf": pdf_unico.name if pacote.documento_unico_pdf else None,
        },
        "anexos": [
            {
                "ordem": anexo.ordem,
                "rotulo": anexo.rotulo,
                "docx": mapa_publicacao[anexo.chave][0].name,
                "pdf": (mapa_publicacao[anexo.chave][1].name
                        if mapa_publicacao[anexo.chave][1] else None),
            }
            for anexo in plano.anexos if anexo.chave in mapa_publicacao
        ],
        "conversor_pdf": conversor.nome,
        "relatorio_validacao": relatorio_md.name if relatorio_md else None,
    }
    pacote.manifesto_arquivos = pasta_saida / "MANIFESTO_ARQUIVOS.json"
    pacote.manifesto_arquivos.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")

    pacote.zip = _compactar(pacote, plano, mapa_publicacao, pasta_saida,
                            relatorio_md, registro)
    return pacote


def _compactar(pacote: Pacote, plano: PlanoAnexos,
               mapa: dict[str, tuple[Path, Optional[Path]]], pasta_saida: Path,
               relatorio_md: Optional[Path], registro: Registro) -> Path:
    """Empacota com os nomes de publicação; PDF quando existe, DOCX sempre."""
    destino = pasta_saida / "PACOTE_PUBLICACAO.zip"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zip_saida:
        for chave, nome in _nomes_de_publicacao(plano):
            if chave not in mapa:
                continue
            docx, pdf = mapa[chave]
            if pdf:
                zip_saida.write(pdf, f"{nome}.pdf")
            zip_saida.write(docx, f"{nome}.docx")
        if pacote.documento_unico_pdf:
            zip_saida.write(pacote.documento_unico_pdf,
                            f"{NOME_DOCUMENTO_UNICO}.pdf")
        if pacote.documento_unico_docx:
            zip_saida.write(pacote.documento_unico_docx,
                            f"{NOME_DOCUMENTO_UNICO}.docx")
        if pacote.manifesto_arquivos:
            zip_saida.write(pacote.manifesto_arquivos, "MANIFESTO_ARQUIVOS.json")
        if relatorio_md and Path(relatorio_md).exists():
            zip_saida.write(relatorio_md, "RELATORIO_VALIDACAO.md")
    registro.informacao(
        ETAPA, f"Pacote de publicação gerado: {destino.name}.", origem=destino.name)
    return destino


def anexar_relatorio(caminho_zip: Optional[Path], relatorio_md: Path,
                     registro: Registro) -> None:
    """
    Acrescenta o relatório ao ZIP depois que ele é escrito.

    O relatório precisa citar os arquivos produzidos, e o ZIP precisa conter o
    relatório: a ordem é gerar o pacote, escrever o relatório e então anexá-lo.
    """
    if caminho_zip is None or not Path(caminho_zip).exists():
        return
    if not Path(relatorio_md).exists():
        return
    with zipfile.ZipFile(caminho_zip, "a", zipfile.ZIP_DEFLATED) as zip_saida:
        if "RELATORIO_VALIDACAO.md" in zip_saida.namelist():
            return
        zip_saida.write(relatorio_md, "RELATORIO_VALIDACAO.md")
    registro.informacao(
        ETAPA, "Relatório de validação incluído no pacote de publicação.",
        origem=Path(caminho_zip).name)
