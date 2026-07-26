#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_painel.py — `00_CONTROLE/PAINEL_PROCESSO.md` (item 12 do escopo).

O painel é DERIVADO: ele se refaz a partir de `PROCESSO.json` e
`DOCUMENTOS.json` a cada registro, promoção ou importação. Editá-lo à mão não
é erro grave, é só inútil — a próxima operação sobrescreve. A fonte é o JSON.

Ele responde, de relance, ao que o item 36 pede: qual é a versão atual, qual o
status, onde está o arquivo, que versões anteriores existem, que documentos
externos chegaram e o que continua pendente.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from manifesto import Processo, agora  # noqa: E402
from manifesto import preparar_console  # noqa: E402
from nomes_arquivos import CATEGORIAS_EXTERNAS  # noqa: E402

ROTULO_STATUS = {
    "rascunho": "rascunho",
    "em_elaboracao": "em elaboração",
    "em_revisao": "em revisão",
    "aprovado": "aprovado",
    "assinado": "assinado",
    "publicado": "publicado",
    "substituido": "substituído",
    "cancelado": "cancelado",
    "arquivado": "arquivado",
}

ROTULO_CATEGORIA = {
    "solicitacoes": "Solicitações",
    "cotacoes_e_propostas": "Cotações e propostas",
    "habilitacao": "Habilitação",
    "emails_e_comunicacoes": "E-mails e comunicações",
    "referencias_tecnicas": "Referências técnicas",
    "pareceres": "Pareceres",
    "comprovantes": "Comprovantes",
    "outros": "Outros",
}


def _data_curta(iso: Optional[str]) -> str:
    if not iso:
        return "—"
    texto = str(iso)
    if len(texto) >= 10 and texto[4] == "-":
        return f"{texto[8:10]}/{texto[5:7]}/{texto[0:4]}"
    return texto


def _pendencias_manuais(processo: Processo) -> list[str]:
    """Itens não marcados de `PENDENCIAS.md` — a lista humana do processo."""
    if not processo.arquivo_pendencias.exists():
        return []
    itens: list[str] = []
    for linha in processo.arquivo_pendencias.read_text(encoding="utf-8").splitlines():
        limpo = linha.strip()
        if limpo.startswith("- [ ]"):
            itens.append(limpo[5:].strip())
    return itens


def _proxima_acao(dados: dict[str, Any], manifesto: dict[str, Any]) -> str:
    """
    Sugestão operacional, jamais decisão. Sai do que falta na lista de
    documentos obrigatórios — que é ela mesma uma sugestão a confirmar.
    """
    pendentes = dados.get("documentos_pendentes") or []
    em_revisao = [
        chave for chave, registro in manifesto.get("documentos", {}).items()
        if registro.get("status") == "em_revisao"
    ]
    if em_revisao:
        return f"Concluir a revisão de: {', '.join(sorted(em_revisao))}."
    if pendentes:
        return f"Elaborar o próximo documento pendente: {pendentes[0]}."
    return "Conferir a instrução na esteira (07_checklists/esteira-contratacao-direta.md)."


def montar_painel(
    processo: Processo,
    manifesto: Optional[dict[str, Any]] = None,
    dados: Optional[dict[str, Any]] = None,
) -> str:
    manifesto = manifesto if manifesto is not None else processo.ler_documentos()
    dados = dados if dados is not None else processo.ler_processo()
    documentos = manifesto.get("documentos", {})
    externos = manifesto.get("documentos_externos", [])

    numero = dados.get("numero") or processo.identificador
    objeto = dados.get("objeto") or "(objeto não informado)"
    pendencias = _pendencias_manuais(processo)

    partes: list[str] = [
        f"# {numero} — {objeto}",
        "",
        "## Situação atual",
        "",
        f"Fase: {str(dados.get('fase_atual') or 'não informada').replace('_', ' ')}  ",
        f"Última atualização: {_data_curta(manifesto.get('atualizado_em') or agora())}  ",
        f"Pendências registradas: {len(pendencias)}",
        "",
        "## Documentos atuais",
        "",
    ]

    correntes = {
        chave: registro for chave, registro in sorted(documentos.items())
        if registro.get("arquivo_atual")
    }
    if not correntes:
        partes.append("_Nenhum documento registrado até o momento._")
    else:
        partes += [
            "| Documento | Versão | Status | Arquivo | Atualizado em | Versões anteriores |",
            "|---|---:|---|---|---|---:|",
        ]
        for chave, registro in correntes.items():
            partes.append(
                f"| {chave} | {registro.get('versao_atual', '—')} "
                f"| {ROTULO_STATUS.get(registro.get('status', ''), registro.get('status', '—'))} "
                f"| `{registro.get('arquivo_atual')}` "
                f"| {_data_curta(registro.get('atualizado_em'))} "
                f"| {len(registro.get('historico') or [])} |"
            )

    arquivados = {
        chave: registro for chave, registro in sorted(documentos.items())
        if not registro.get("arquivo_atual")
    }
    if arquivados:
        partes += ["", "### Tipos sem arquivo corrente", ""]
        for chave, registro in arquivados.items():
            partes.append(
                f"- **{chave}** — status `{registro.get('status')}`; "
                f"{len(registro.get('historico') or [])} versão(ões) em `90_HISTORICO/`."
            )

    # Representações (item 9): DOCX e PDF do mesmo documento não são versões.
    com_representacoes = {
        chave: registro for chave, registro in sorted(documentos.items())
        if any(v for k, v in (registro.get("representacoes") or {}).items() if k != "docx")
    }
    if com_representacoes:
        partes += ["", "## Representações", "",
                   "| Documento | Versão | Editável | PDF | Assinado |", "|---|---:|---|---|---|"]
        for chave, registro in com_representacoes.items():
            r = registro.get("representacoes") or {}
            partes.append(
                f"| {chave} | {registro.get('versao_atual', '—')} "
                f"| {('`' + r['docx'] + '`') if r.get('docx') else '—'} "
                f"| {('`' + r['pdf'] + '`') if r.get('pdf') else '—'} "
                f"| {('`' + r['assinado'] + '`') if r.get('assinado') else '—'} |"
            )

    partes += ["", "## Documentos externos", ""]
    if not externos:
        partes.append("_Nenhum documento externo classificado._")
    else:
        contagem: dict[str, int] = {}
        for item in externos:
            categoria = item.get("categoria") or "outros"
            contagem[categoria] = contagem.get(categoria, 0) + 1
        partes += ["| Categoria | Quantidade |", "|---|---:|"]
        for categoria in CATEGORIAS_EXTERNAS:
            if contagem.get(categoria):
                partes.append(
                    f"| {ROTULO_CATEGORIA.get(categoria, categoria)} | {contagem[categoria]} |"
                )
        em_quarentena = [i for i in externos if i.get("status_validacao") == "em_quarentena"]
        if em_quarentena:
            partes += [
                "",
                f"⚠️ **{len(em_quarentena)} documento(s) em quarentena** aguardando "
                f"confirmação humana (ver `98_QUARENTENA/`).",
            ]

    partes += ["", "## Pendências", ""]
    if pendencias:
        partes += [f"- {item}" for item in pendencias]
    else:
        partes.append("_Nenhuma pendência registrada em `PENDENCIAS.md`._")

    faltantes = dados.get("documentos_pendentes") or []
    if faltantes:
        partes += [
            "",
            "### Documentos previstos ainda não registrados",
            "",
            ", ".join(faltantes),
            "",
            "> A lista de documentos obrigatórios é sugestão operacional; confirme na "
            "esteira e no Regulamento da Câmara.",
        ]

    partes += [
        "",
        "## Próxima ação",
        "",
        _proxima_acao(dados, manifesto),
        "",
        "---",
        "",
        "_Painel derivado de `PROCESSO.json` e `DOCUMENTOS.json`, regenerado por "
        "`scripts/gestao_documental/gerar_painel.py`. Não edite como fonte._",
        "",
    ]
    return "\n".join(partes)


def gerar_painel(identificador: str, base: Optional[Path | str] = None) -> Path:
    processo = Processo.abrir(identificador, base)
    processo.arquivo_painel.write_text(montar_painel(processo), encoding="utf-8")
    return processo.arquivo_painel


def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(description="Regera o painel do processo.")
    analisador.add_argument("--processo", required=True)
    analisador.add_argument("--base")
    analisador.add_argument("--mostrar", action="store_true", help="imprime o painel")
    argumentos = analisador.parse_args(argv)

    try:
        caminho = gerar_painel(argumentos.processo, argumentos.base)
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    print(f"Painel gerado: {caminho}")
    if argumentos.mostrar:
        print()
        print(caminho.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
