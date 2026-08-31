#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar_aviso_completo.py — validação cruzada entre o aviso e seus anexos.

Um aviso de dispensa não erra "em um documento": ele erra na diferença entre
documentos — o TR que pede atestado e o Anexo I que não pede, o modelo de
proposta com um item a menos, a relação que chama de Anexo III o que o corpo
numera como IV. É essa diferença que este módulo procura.

Também roda sozinho, em modo auditoria, antes de qualquer montagem:

    python scripts/aviso_completo/validar_aviso_completo.py \
        --processo 08_processos_em_andamento/PA_031_2026/ --somente-auditoria
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docx_cmi"))

import extrair_dados_tr
import localizar_componentes
import numerar_anexos
import unir_docx
from extrair_dados_tr import DadosTR
from numerar_anexos import PlanoAnexos
from ocorrencias import Registro, decidir_status
from util_ooxml import (
    BLOCO_OU_RE,
    exigir_python_docx,
    iter_paragrafos_corpo,
    marcadores_pendentes,
    normalizar_texto,
    texto_paragrafo,
)
import cabecalho_rodape_docx
import validar_conteudo_docx

RAIZ = Path(__file__).resolve().parents[2]
ETAPA = "validação cruzada"

# Prazo mínimo de divulgação: art. 75, §3º, da Lei nº 14.133/2021 e
# Portaria nº 06/2024 da Câmara, art. 5º, §1º (3 dias úteis).
DIAS_UTEIS_MINIMOS = 3

RE_NUMERO = re.compile(r"\d{1,4}\s*/\s*\d{4}")


def _normalizar_numero(valor: Optional[str]) -> Optional[str]:
    if not valor:
        return None
    achado = RE_NUMERO.search(str(valor))
    return re.sub(r"\s+", "", achado.group(0)) if achado else None


# --------------------------------------------------------------------------- #
# Identificação do processo
# --------------------------------------------------------------------------- #

def validar_identificacao(manifesto: dict[str, Any], dados_tr: Optional[DadosTR],
                          registro: Registro) -> None:
    """Confere que o TR anexado é mesmo o TR deste processo (item 6.5 do escopo)."""
    processo = manifesto.get("processo", {})
    numero = _normalizar_numero(processo.get("numero"))
    dispensa = _normalizar_numero(processo.get("dispensa"))

    for rotulo, valor in (("numero", processo.get("numero")),
                          ("dispensa", processo.get("dispensa"))):
        if not valor:
            registro.bloqueante(
                ETAPA, f"O manifesto não informa processo.{rotulo}.")

    if dados_tr is None:
        return

    if numero and dados_tr.numero_processo:
        if numero != dados_tr.numero_processo:
            registro.bloqueante(
                ETAPA,
                f"O Termo de Referência identifica o processo "
                f"{dados_tr.numero_processo} e o manifesto informa {numero}. "
                "TR de processo diferente não pode ser anexado.",
                origem=dados_tr.caminho.name,
            )
        else:
            registro.informacao(
                ETAPA, f"TR confirmado como do processo {numero}.",
                origem=dados_tr.caminho.name)
    elif numero:
        registro.alerta(
            ETAPA,
            "Não foi possível ler o número do processo no TR; a correspondência "
            f"com o processo {numero} depende de conferência humana.",
            origem=dados_tr.caminho.name,
        )

    if dispensa and dados_tr.numero_dispensa and dispensa != dados_tr.numero_dispensa:
        registro.bloqueante(
            ETAPA,
            f"O TR menciona a dispensa {dados_tr.numero_dispensa} e o manifesto "
            f"informa {dispensa}.",
            origem=dados_tr.caminho.name,
        )

    objeto = (processo.get("objeto") or "").strip()
    if objeto and dados_tr.objeto:
        palavras = {p for p in re.findall(r"\w{5,}", objeto.lower())}
        do_tr = dados_tr.objeto.lower()
        if palavras and not any(p in do_tr for p in palavras):
            registro.alerta(
                ETAPA,
                "O objeto do manifesto e o objeto do TR não têm termos em comum. "
                f"Manifesto: '{objeto[:80]}'. TR: '{dados_tr.objeto[:80]}'.",
            )
    if not objeto:
        registro.bloqueante(ETAPA, "O manifesto não informa processo.objeto.")
    for campo in ("criterio_julgamento", "fundamento_legal"):
        if not (processo.get(campo) or "").strip():
            registro.bloqueante(ETAPA, f"O manifesto não informa processo.{campo}.")


# --------------------------------------------------------------------------- #
# Datas de recebimento
# --------------------------------------------------------------------------- #

def _data(valor: Any) -> Optional[date]:
    if not valor:
        return None
    try:
        return datetime.strptime(str(valor).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def dias_uteis(inicio: date, fim: date) -> int:
    """Dias úteis entre duas datas, contando o dia final. Feriados não entram."""
    if fim < inicio:
        return 0
    total = 0
    atual = inicio
    while atual <= fim:
        if atual.weekday() < 5:
            total += 1
        atual += timedelta(days=1)
    return total


def validar_datas(manifesto: dict[str, Any], registro: Registro) -> None:
    """Valida o período de recebimento das propostas e o prazo mínimo legal."""
    bloco = manifesto.get("recebimento_propostas") or {}
    if not bloco:
        registro.bloqueante(
            ETAPA, "O manifesto não traz o bloco recebimento_propostas.")
        return

    inicio, fim = _data(bloco.get("data_inicio")), _data(bloco.get("data_fim"))
    if inicio is None or fim is None:
        registro.bloqueante(
            ETAPA,
            "Datas de recebimento inválidas ou ausentes (esperado AAAA-MM-DD): "
            f"início='{bloco.get('data_inicio')}', fim='{bloco.get('data_fim')}'.",
        )
        return
    if fim < inicio:
        registro.bloqueante(
            ETAPA,
            f"A data final de recebimento ({fim}) é anterior à inicial ({inicio}).",
        )
        return

    for campo in ("hora_inicio", "hora_fim"):
        valor = str(bloco.get(campo) or "").strip()
        if not re.fullmatch(r"\d{1,2}:\d{2}", valor):
            registro.bloqueante(
                ETAPA, f"Horário inválido em recebimento_propostas.{campo}: "
                       f"'{bloco.get(campo)}' (esperado HH:MM).")

    uteis = dias_uteis(inicio, fim)
    if uteis < DIAS_UTEIS_MINIMOS:
        registro.bloqueante(
            ETAPA,
            f"O período de recebimento tem {uteis} dia(s) útil(eis) e o mínimo é "
            f"{DIAS_UTEIS_MINIMOS} (art. 75, §3º, da Lei nº 14.133/2021; Portaria "
            "nº 06/2024 da Câmara, art. 5º, §1º).",
        )
    else:
        registro.informacao(
            ETAPA,
            f"Período de recebimento: {inicio} a {fim} — {uteis} dias úteis "
            "(feriados municipais não são considerados no cálculo automático; "
            "confira o calendário local).",
        )

    email = str(bloco.get("email") or "").strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        registro.bloqueante(
            ETAPA,
            f"Endereço eletrônico de recebimento inválido ou ausente: '{email}'.")

    assinatura = manifesto.get("assinatura") or {}
    if not (assinatura.get("nome") or "").strip():
        registro.bloqueante(
            ETAPA, "O manifesto não informa o responsável pela assinatura do aviso.")


# --------------------------------------------------------------------------- #
# Habilitação proporcional
# --------------------------------------------------------------------------- #

EXIGENCIAS_ANEXO = {
    "qualificacao_tecnica": re.compile(
        r"(atestado\s+de\s+capacidade\s+t[ée]cnica|qualifica[çc][ãa]o\s+t[ée]cnica)",
        re.IGNORECASE),
    "qualificacao_economica": re.compile(
        r"(balan[çc]o\s+patrimonial|certid[ãa]o\s+negativa\s+de\s+fal[êe]ncia"
        r"|qualifica[çc][ãa]o\s+econ[ôo]mic)", re.IGNORECASE),
}

ROTULOS = {
    "qualificacao_tecnica": "qualificação técnica",
    "qualificacao_economica": "qualificação econômico-financeira",
}


def validar_habilitacao(texto_habilitacao: str, dados_tr: Optional[DadosTR],
                        registro: Registro) -> None:
    """
    Compara o que o TR exige com o que o Anexo I cobra.

    As duas direções são reportadas, e nenhuma é resolvida sozinha: acrescentar
    exigência ao Anexo I restringe a competição, e retirar do TR muda a regra do
    julgamento. Ambas são decisão do setor responsável.
    """
    if dados_tr is None:
        return
    for chave, padrao in EXIGENCIAS_ANEXO.items():
        no_tr = dados_tr.sinais.get(chave, False)
        no_anexo, _ = extrair_dados_tr._exigencia_afirmativa(texto_habilitacao, padrao)
        rotulo = ROTULOS[chave]
        evidencia = dados_tr.evidencias.get(chave, "")
        if no_tr and not no_anexo:
            registro.pendencia(
                ETAPA,
                f"DIVERGÊNCIA: o Termo de Referência prevê {rotulo}, mas o Anexo "
                "I não apresenta o documento correspondente. Incluir a exigência "
                "depende de previsão no TR, justificativa de proporcionalidade e "
                "confirmação do setor responsável."
                + (f" Trecho do TR: \"...{evidencia[:180]}...\"" if evidencia else ""),
            )
        elif no_anexo and not no_tr:
            registro.pendencia(
                ETAPA,
                f"DIVERGÊNCIA: o Anexo I exige {rotulo} sem previsão "
                "correspondente no Termo de Referência. Exigência sem "
                "justificativa no processo restringe a competição indevidamente.",
            )
    for chave, rotulo in (("amostra", "apresentação de amostra"),
                          ("catalogo", "catálogo ou ficha técnica")):
        if dados_tr.sinais.get(chave):
            registro.informacao(
                ETAPA,
                f"O TR menciona {rotulo}. Confira se o aviso e o Anexo I tratam "
                "da exigência de forma coerente.",
            )


# --------------------------------------------------------------------------- #
# Documento montado
# --------------------------------------------------------------------------- #

def _linhas(documento) -> list[str]:
    return [texto_paragrafo(p).strip() for p in iter_paragrafos_corpo(documento)]


RE_LINHA_DE_ASSINATURA = re.compile(r"^[_\s]{4,}$")


def _pendencias_da_linha(linha: str) -> list[str]:
    """
    Campos pendentes de uma linha, sem confundir traço de assinatura com lacuna.

    Uma linha formada só por sublinhados é a régua sobre a qual o fornecedor
    assina — está no modelo de proposta e na declaração por construção. Já
    sublinhado no meio de uma frase ("CNPJ: ______") é campo por preencher e
    continua bloqueando.
    """
    if RE_LINHA_DE_ASSINATURA.match(linha):
        return []
    return marcadores_pendentes(linha)


def validar_documento_final(caminho: Path, plano: PlanoAnexos,
                            minuta_aviso: Optional[Path],
                            registro: Registro,
                            lacunas_autorizadas: Optional[list[str]] = None
                            ) -> dict[str, Any]:
    """Varredura final: campos pendentes, blocos 'OU', referências e timbre."""
    exigir_python_docx()
    from docx import Document

    try:
        documento = Document(str(caminho))
    except Exception as erro:  # pragma: no cover - só em pacote corrompido
        registro.bloqueante(
            ETAPA, f"O documento montado não pôde ser aberto: {erro}",
            origem=caminho.name)
        return {"aberto": False}

    autorizadas = {normalizar_texto(linha)
                   for linha in (lacunas_autorizadas or []) if linha.strip()}
    linhas = _linhas(documento)
    pendentes: list[str] = []
    reservadas = 0
    for linha in linhas:
        if normalizar_texto(linha) in autorizadas:
            reservadas += 1
            continue
        pendentes += _pendencias_da_linha(linha)
    pendentes = sorted(set(pendentes))
    if pendentes:
        registro.bloqueante(
            ETAPA,
            f"{len(pendentes)} campo(s) pendente(s) no documento montado: "
            + ", ".join(pendentes[:10])
            + ("..." if len(pendentes) > 10 else ""),
            origem=caminho.name,
        )
    if reservadas:
        registro.informacao(
            ETAPA,
            f"{reservadas} linha(s) com lacuna reservada ao proponente (modelo "
            "de proposta, declaração e minuta de contrato) — espaço legítimo de "
            "preenchimento, não campo esquecido.",
            origem=caminho.name,
        )

    blocos_ou = [linha for linha in linhas if BLOCO_OU_RE.match(linha)]
    if blocos_ou:
        registro.bloqueante(
            ETAPA,
            f"{len(blocos_ou)} bloco(s) alternativo(s) 'OU' não resolvido(s) no "
            "documento montado.",
            origem=caminho.name,
        )

    numerar_anexos.verificar_referencias(
        iter_paragrafos_corpo(documento), plano, registro, origem=caminho.name)

    timbre = {}
    if minuta_aviso is not None and Path(minuta_aviso).exists():
        intactas, divergencias = unir_docx.timbre_intacto(
            Path(minuta_aviso), Path(caminho))
        timbre = {"intacto": intactas, "divergencias": divergencias}
        if not intactas:
            registro.bloqueante(
                ETAPA,
                "O cabeçalho/rodapé do documento montado divergiu do timbre da "
                "minuta do aviso: " + "; ".join(divergencias[:5]),
                origem=caminho.name,
            )

    resumo = cabecalho_rodape_docx.resumir(documento, Path(caminho))
    return {
        "aberto": True,
        "paragrafos": len(linhas),
        "campos_pendentes": pendentes,
        "blocos_ou": len(blocos_ou),
        "timbre": timbre,
        "secoes": getattr(resumo, "secoes", None),
    }


def validar_preservacao(partes: list[Path], final: Path, registro: Registro,
                        acrescimos_autorizados: Optional[list[str]] = None
                        ) -> dict[str, Any]:
    """
    Confere que nenhuma linha dos componentes se perdeu na união.

    O sentido da comparação é deliberado: exige-se que o documento final CONTENHA
    tudo o que veio das partes. Acréscimo é esperado (os rótulos de anexo); perda
    é sempre defeito — cláusula, requisito ou item que sumiu na montagem.
    """
    exigir_python_docx()
    from docx import Document

    autorizados = {normalizar_texto(t) for t in (acrescimos_autorizados or [])}
    do_final = {normalizar_texto(linha)
                for linha in _linhas(Document(str(final))) if linha.strip()}

    perdidas: list[tuple[str, str]] = []
    total = 0
    for parte in partes:
        for linha in _linhas(Document(str(parte))):
            if not linha.strip():
                continue
            total += 1
            normalizada = normalizar_texto(linha)
            if normalizada not in do_final and normalizada not in autorizados:
                perdidas.append((Path(parte).name, linha))

    if perdidas:
        amostra = "; ".join(f"{arquivo}: '{linha[:70]}'"
                            for arquivo, linha in perdidas[:5])
        registro.bloqueante(
            ETAPA,
            f"{len(perdidas)} linha(s) de conteúdo não foram encontradas no "
            f"documento montado. Amostra — {amostra}",
            origem=Path(final).name,
        )
    else:
        registro.informacao(
            ETAPA,
            f"Conteúdo preservado: {total} linha(s) dos componentes localizadas "
            "no documento único.",
            origem=Path(final).name,
        )
    return {"linhas_conferidas": total, "linhas_perdidas": len(perdidas)}


def levantar_pendencias(caminho: Path) -> dict[str, Any]:
    """Pendências e marcas de revisão do documento, via módulo de padronização."""
    exigir_python_docx()
    from docx import Document

    documento = Document(str(caminho))
    pendencias = validar_conteudo_docx.levantar_pendencias(documento)
    return {
        "campos_pendentes": pendencias.campos_pendentes,
        "blocos_ou": pendencias.blocos_ou,
        "opcoes_nao_marcadas": pendencias.opcoes_nao_marcadas,
        "texto_destacado": pendencias.texto_destacado,
        "total": pendencias.total,
    }


# --------------------------------------------------------------------------- #
# Modo auditoria (sem montar)
# --------------------------------------------------------------------------- #

def auditar(pasta_processo: Optional[Path], caminho_manifesto: Optional[Path],
            tr: Optional[Path] = None,
            decisao_contrato: Optional[bool] = None,
            contrato: Optional[Path] = None,
            autorizar_tr_rascunho: bool = False) -> dict[str, Any]:
    """Executa as validações que não dependem de montagem. Nada é gravado."""
    registro = Registro()

    if caminho_manifesto is None and pasta_processo is not None:
        caminho_manifesto = localizar_componentes.descobrir_manifesto(pasta_processo)
    if caminho_manifesto is None:
        registro.bloqueante(
            ETAPA,
            "Manifesto do aviso completo não encontrado. Informe --manifesto ou "
            f"crie {localizar_componentes.MANIFESTO_PADRAO} na pasta do processo.")
        return _resultado_auditoria(registro, None, None, None)

    manifesto = localizar_componentes.carregar_manifesto(caminho_manifesto)

    componentes = localizar_componentes.localizar(
        manifesto, registro,
        pasta_processo=pasta_processo,
        caminho_manifesto=caminho_manifesto,
        tr_explicito=tr,
        contrato_explicito=contrato,
        decisao_contrato=decisao_contrato,
        autorizar_tr_rascunho=autorizar_tr_rascunho,
    )

    dados_tr = None
    componente_tr = componentes.obter("tr")
    if componente_tr is not None and componente_tr.caminho is not None:
        dados_tr = extrair_dados_tr.extrair(componente_tr.caminho, registro)
        if not componentes.instrumento.definido and dados_tr.texto:
            componentes.instrumento = localizar_componentes.decidir_instrumento(
                manifesto, registro, texto_tr=dados_tr.texto,
                decisao_usuario=decisao_contrato, minuta_usuario=contrato)

    validar_identificacao(manifesto, dados_tr, registro)
    validar_datas(manifesto, registro)

    plano = numerar_anexos.planejar(componentes, registro)

    aviso = componentes.obter("aviso")
    if aviso is not None and aviso.caminho is not None:
        exigir_python_docx()
        from docx import Document
        documento = Document(str(aviso.caminho))
        texto = "\n".join(_linhas(documento))
        validar_habilitacao(texto, dados_tr, registro)
        numerar_anexos.verificar_referencias(
            iter_paragrafos_corpo(documento), plano, registro,
            origem=aviso.caminho.name)

    return _resultado_auditoria(registro, manifesto, dados_tr, plano)


def _resultado_auditoria(registro: Registro, manifesto, dados_tr, plano
                         ) -> dict[str, Any]:
    return {
        "modo": "auditoria",
        "status": decidir_status(registro),
        "processo": (manifesto or {}).get("processo", {}),
        "termo_referencia": dados_tr.como_dicionario() if dados_tr else None,
        "anexos": plano.como_lista() if plano else [],
        "ocorrencias": registro.como_lista(),
        "contagem": registro.contagem(),
    }


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validação cruzada do Aviso de Dispensa Completo.")
    parser.add_argument("--processo", type=Path,
                        help="pasta do processo em 08_processos_em_andamento/")
    parser.add_argument("--manifesto", type=Path,
                        help="manifesto_aviso_completo.json")
    parser.add_argument("--tr", type=Path, help="Termo de Referência final")
    parser.add_argument("--contrato", type=Path, help="minuta de contrato oficial")
    parser.add_argument("--incluir-contrato", dest="incluir_contrato",
                        action="store_true", default=None,
                        help="determinação expressa: haverá Termo de Contrato")
    parser.add_argument("--sem-contrato", dest="incluir_contrato",
                        action="store_false",
                        help="determinação expressa: instrumento equivalente")
    parser.add_argument("--autorizar-tr-rascunho", action="store_true",
                        help="aceita TR com nome de rascunho (autorização expressa)")
    parser.add_argument("--somente-auditoria", action="store_true",
                        help="apenas audita; nada é gravado (padrão deste comando)")
    parser.add_argument("--json", type=Path, help="grava o resultado em JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = construir_parser().parse_args(argv)
    if not args.processo and not args.manifesto:
        print("Informe --processo ou --manifesto.", file=sys.stderr)
        return 2

    resultado = auditar(
        args.processo, args.manifesto, tr=args.tr,
        decisao_contrato=args.incluir_contrato, contrato=args.contrato,
        autorizar_tr_rascunho=args.autorizar_tr_rascunho,
    )

    print(f"Status: {resultado['status']}")
    for ocorrencia in resultado["ocorrencias"]:
        print(f"  [{ocorrencia['severidade']}] {ocorrencia['etapa']}: "
              f"{ocorrencia['mensagem']}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON: {args.json}")

    return 1 if resultado["contagem"].get("ERRO BLOQUEANTE") else 0


if __name__ == "__main__":
    raise SystemExit(main())
