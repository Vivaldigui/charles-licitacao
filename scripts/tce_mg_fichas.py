#!/usr/bin/env python3
"""Gera as fichas Markdown das contratações do TCE-MG coletadas por `tce_mg_licitacoes.py`.

O que este script faz é **mecânico**: lê o manifesto e o texto dos PDFs, identifica as
peças que compõem cada documentação publicada (pelo rodapé do SEI), extrai o fundamento
legal citado e a lista de documentos que o parecer diz instruírem o processo, e escreve
uma ficha por contratação.

O que ele **não** faz: interpretar. Todo campo derivado do PDF vai marcado como
`(extraído automaticamente — conferir no PDF)`. Campo ausente fica `não identificado`,
nunca deduzido.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

RODAPE = re.compile(
    r"^(?P<tipo>.+?)\s+\((?P<id>\d{6,9})\)\s+SEI\s+(?P<proc>[\d.\-]+)\s*/\s*pg\.\s*(?P<pg>\d+)\s*$"
)

# "inciso III do art. 75" / "art. 75, inciso II" / "art. 75, III" / "art. 74, I"
FUNDAMENTOS = [
    re.compile(r"inciso\s+([IVX]+)[^.]{0,40}?art(?:igo)?\.?\s*(7[45])", re.I),
    re.compile(r"art(?:igo)?\.?\s*(7[45])\s*,\s*(?:inciso\s*)?([IVX]+)\b", re.I),
]

# Expressão que marca o dispositivo efetivamente adotado como fundamento do ato.
DECLARATORIAS = re.compile(
    r"(?:com\s+(?:fundamento|arrimo|fulcro|base)\s+n[oa]s?|aplica[çc][ãa]o\s+d[oe])\s*$",
    re.I,
)

RODAPE_INLINE = re.compile(r"[^;]{0,80}\(\d{6,9}\)\s+SEI\s+[\d.\-]+\s*/\s*pg\.\s*\d+")

ROMANOS = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII",
           "XIII", "XIV", "XV", "XVI", "XVII", "XVIII"}


def texto_do_pdf(pdf: Path) -> list[str]:
    cache = pdf.parent / "texto_extraido" / (pdf.stem + ".txt")
    if cache.exists():
        bruto = cache.read_text(encoding="utf-8")
        return re.split(r"\n?===== PÁGINA \d+ =====\n", bruto)[1:]
    from pypdf import PdfReader

    leitor = PdfReader(str(pdf))
    paginas = [(p.extract_text() or "") for p in leitor.pages]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        "\n\n".join(f"===== PÁGINA {i + 1} =====\n{t}" for i, t in enumerate(paginas)),
        encoding="utf-8",
    )
    return paginas


def pecas_do_processo(paginas: list[str]) -> tuple[list[dict], str | None]:
    """Lê o rodapé do SEI de cada página e agrupa as peças na ordem em que aparecem."""
    pecas: list[dict] = []
    processo_sei = None
    for numero, texto in enumerate(paginas, start=1):
        linhas = [ln.strip() for ln in texto.strip().splitlines() if ln.strip()]
        if not linhas:
            continue
        m = RODAPE.match(linhas[-1])
        if not m:
            continue
        processo_sei = processo_sei or m.group("proc")
        tipo = re.sub(r"\s+", " ", m.group("tipo")).strip()
        ident = m.group("id")
        if pecas and pecas[-1]["id"] == ident:
            pecas[-1]["pagina_final"] = numero
        else:
            pecas.append(
                {"tipo": tipo, "id": ident, "pagina_inicial": numero, "pagina_final": numero}
            )
    return pecas, processo_sei


def fundamentos_citados(paginas: list[str]) -> tuple[list[str], list[str]]:
    """Devolve (dispositivos adotados como fundamento, demais dispositivos citados).

    O que separa os dois é a expressão imediatamente anterior: "com fundamento no",
    "com arrimo no", "com fulcro no", "aplicação do". Sem ela, o dispositivo apenas
    aparece no texto — pode ser transcrição de lei, boilerplate de minuta ou remissão.
    """
    declarados: list[str] = []
    citados: list[str] = []
    corpo = re.sub(r"\s+", " ", "\n".join(paginas))
    for padrao in FUNDAMENTOS:
        for m in padrao.finditer(corpo):
            grupos = m.groups()
            artigo, inciso = (
                (grupos[1], grupos[0]) if grupos[0].upper() in ROMANOS else (grupos[0], grupos[1])
            )
            if artigo not in {"74", "75"} or inciso.upper() not in ROMANOS:
                continue
            rotulo = f"art. {artigo}, {inciso.upper()}"
            anterior = corpo[max(0, m.start() - 40): m.start()]
            alvo = declarados if DECLARATORIAS.search(anterior) else citados
            if rotulo not in alvo:
                alvo.append(rotulo)
    citados = [c for c in citados if c not in declarados]
    return declarados, citados


def documentos_instrutores(paginas: list[str]) -> list[str]:
    """Extrai a lista 'documentos que instruem o processo' do parecer jurídico."""
    corpo = re.sub(r"\s+", " ", "\n".join(paginas))
    ini = re.search(r"documentos que instruem (?:o|os) (?:processo|autos)[^:]*:", corpo, re.I)
    if not ini:
        return []
    trecho = corpo[ini.end(): ini.end() + 4000]
    fim = re.search(r"É o relat[óo]rio", trecho, re.I)
    if fim:
        trecho = trecho[: fim.start()]
    itens = re.split(r"\s\d{1,2}[\)\.]\s", " " + trecho)
    limpos = []
    for it in itens:
        # o texto corrido arrasta o rodapé do SEI da página; ele não é item da lista
        it = RODAPE_INLINE.sub("", it)
        it = it.strip(" ;. ")
        it = re.sub(r"\s*\([\d.;\s e]+\)\s*$", "", it).strip(" ;.")
        if 5 < len(it) < 300:
            limpos.append(it)
    return limpos


def slug(texto: str, limite: int = 60) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = texto.encode("ascii", "ignore").decode("ascii").lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto).strip("-")
    return texto[:limite].strip("-") or "sem-objeto"


def brl(valor) -> str:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "não identificado"
    if v == 0:
        return "R$ 0,00 (não informado no portal)"
    return "R$ " + f"{v:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def ficha(reg: dict, dados: dict, evid: dict | None, hoje: str) -> str:
    modalidade = reg["_modalidade_filtro"]
    tags = ["tce-mg", "referencia-externa", slug(modalidade, 30)]
    for f in dados.get("fundamentos", []):
        tags.append(slug(f, 20))

    linhas = [
        "---",
        "tipo: referencia_externa",
        "hierarquia: persuasiva",
        f"tema: {modalidade.lower()} — Lei 14.133/2021",
        "fonte: TCE-MG — Portal da Transparência (Compras e Licitações)",
        "vigencia: vigente",
        f"atualizado_em: {hoje}",
        f"tags: [{', '.join(dict.fromkeys(tags))}]",
        "---",
        "",
        f"# {modalidade} nº {reg['numeroLicitacao']}/{reg['anoLicitacao']} — TCE-MG",
        "",
        "> Documento de **referência técnica e redacional** de outro órgão. Não é norma da",
        "> Câmara Municipal de Itanhandu e não substitui o Regulamento interno nem as minutas",
        "> oficiais de `05_minutas/`.",
        "",
        "## 1. Identificação",
        "",
        "| Campo | Conteúdo |",
        "|---|---|",
        f"| Órgão | Tribunal de Contas do Estado de Minas Gerais (TCEMG) |",
        f"| Fonte da pesquisa | {reg['_fonte']} |",
        f"| Modalidade / tipo | {reg.get('nomeTipoLicitacao') or 'não identificado'} |",
        f"| Número / ano | {reg['numeroLicitacao']}/{reg['anoLicitacao']} |",
        f"| Situação | {reg.get('situacao') or 'não identificado'} |",
        f"| Processo SEI | {dados.get('processo_sei') or 'não identificado'} |",
        "",
        "**Objeto (texto do portal, literal):**",
        "",
        "> " + re.sub(r"\s+", " ", (reg.get("objeto") or "não informado")).strip(),
        "",
    ]

    portal = dados.get("linhas_portal") or [reg]
    if len(portal) > 1:
        linhas += [
            f"**Resultado por lote/fornecedor** — o portal devolve uma linha por item homologado; "
            f"esta contratação tem **{len(portal)}**. Os valores abaixo são por linha, **não** o "
            "total da contratação:",
            "",
            "| Estimado | Homologado | Fornecedor | Contrato SIAD |",
            "|---|---|---|---|",
        ]
        for linha in portal:
            linhas.append(
                f"| {brl(linha.get('vlrReferencia'))} | {brl(linha.get('vlrHomologado'))} "
                f"| {linha.get('nomFornecedor') or 'não identificado'} "
                f"| {linha.get('numContrato') or 'não identificado'} |"
            )
        linhas.append("")
    else:
        linhas += [
            "| Campo | Conteúdo |",
            "|---|---|",
            f"| Valor estimado | {brl(reg.get('vlrReferencia'))} |",
            f"| Valor homologado | {brl(reg.get('vlrHomologado'))} |",
            f"| Fornecedor | {reg.get('nomFornecedor') or 'não identificado'} |",
            f"| Contrato SIAD | {reg.get('numContrato') or 'não identificado'} |",
            "",
        ]

    declarados = dados.get("fundamentos") or []
    citados = dados.get("dispositivos_citados") or []
    if declarados:
        vazio = ""
    elif modalidade.startswith("Dispensa"):
        vazio = "- não identificado no texto extraído"
    else:
        vazio = (
            "- não se aplica: o pregão é licitação; não se funda em hipótese de "
            "contratação direta do art. 74/75"
        )
    linhas += [
        "## 2. Fundamento legal (art. 74/75)",
        "",
        "**Adotado como fundamento do ato** (precedido de \"com fundamento/arrimo/fulcro no\" ou \"aplicação do\"):",
        "",
        ("- " + "\n- ".join(declarados)) if declarados else vazio,
        "",
    ]
    if citados:
        linhas += [
            "**Demais dispositivos do art. 74/75 apenas citados no texto** — transcrição de lei,",
            "texto padrão de minuta ou remissão; **não** são o fundamento do ato:",
            "",
            "- " + "\n- ".join(citados),
            "",
        ]
    linhas += [
        "*(extraído automaticamente do texto do PDF — conferir no arquivo antes de citar)*",
        "",
    ]

    pecas = dados.get("pecas") or []
    linhas += ["## 3. Peças que compõem a documentação publicada", ""]
    if pecas:
        linhas += ["| # | Peça (rodapé do SEI) | Doc. SEI | Páginas |", "|---|---|---|---|"]
        for i, p in enumerate(pecas, 1):
            faixa = (
                str(p["pagina_inicial"])
                if p["pagina_inicial"] == p["pagina_final"]
                else f"{p['pagina_inicial']}–{p['pagina_final']}"
            )
            linhas.append(f"| {i} | {p['tipo']} | {p['id']} | {faixa} |")
    else:
        linhas.append(
            "Não foi possível identificar as peças pelo rodapé do SEI "
            "(PDF sem camada de texto ou formato diferente) — **verificação manual pendente**."
        )
    linhas.append("")

    secao = 4
    instrutores = dados.get("documentos_instrutores") or []
    if instrutores:
        linhas += [
            f"## {secao}. Documentos que o parecer jurídico afirma instruírem o processo",
            "",
            "*(lista transcrita do relatório do parecer; a maioria desses documentos **não** é",
            "publicada no portal — só o parecer os menciona)*",
            "",
        ]
        linhas += [f"- {d}" for d in instrutores]
        linhas.append("")
        secao += 1

    anexos = dados.get("anexos") or []
    if anexos:
        linhas += [f"## {secao}. Anexos publicados", ""]
        linhas += [f"- `{a}`" for a in anexos]
        linhas.append("")
        secao += 1

    linhas += [
        f"## {secao}. Evidência da coleta",
        "",
        "| Campo | Conteúdo |",
        "|---|---|",
        "| Portal | https://transparencia.tce.mg.gov.br/public/licitacoes |",
        f"| Filtros | Fonte `{reg['_fonte']}` · Lei `14.133/21` · Tipo `{modalidade}` |",
        f"| Arquivo local | `{dados.get('arquivo_relativo') or 'não baixado'}` |",
        f"| Páginas | {dados.get('paginas') or 'não identificado'} |",
        f"| Acesso em | {(evid or {}).get('acessado_em') or hoje} |",
        f"| sha256 | `{(evid or {}).get('sha256') or 'não registrado'}` |",
        "",
        "O arquivo bruto fica em `_entrada/` (fora do versionamento). Esta ficha é o que a base cita.",
        "",
    ]
    return "\n".join(linhas)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entrada", default="_entrada/tce_mg_licitacoes")
    p.add_argument("--saida", default="14_referencias_externas/tce_mg_contratacoes")
    args = p.parse_args(argv)

    entrada = Path(args.entrada)
    saida = Path(args.saida)
    manifesto = json.loads((entrada / "MANIFESTO.json").read_text(encoding="utf-8"))
    evidencias = {}
    caminho_evid = entrada / "EVIDENCIAS_DOWNLOAD.json"
    if caminho_evid.exists():
        for e in json.loads(caminho_evid.read_text(encoding="utf-8")):
            if e.get("tipo") == "DOC_INTERNA_EXTERNA" and e.get("sha256"):
                evidencias[e["registro"]] = e

    hoje = date.today().isoformat()
    vistos: dict[str, dict] = {}

    # O portal devolve uma linha por lote/fornecedor homologado, não por processo.
    # A ficha é por contratação, e as linhas viram a tabela de resultados por lote.
    linhas_por_chave: dict[str, list[dict]] = {}
    for reg in manifesto["registros"]:
        chave = f"{reg['_fonte']}|{reg['_modalidade_filtro']}|{reg['_nome_base']}"
        linhas_por_chave.setdefault(chave, []).append(reg)

    for reg in manifesto["registros"]:
        chave = f"{reg['_fonte']}|{reg['_modalidade_filtro']}|{reg['_nome_base']}"
        if chave in vistos:
            continue
        pasta = entrada / slug(reg["_fonte"]) / slug(reg["_modalidade_filtro"]) / reg["_nome_base"]
        pdfs = sorted(pasta.glob("DOC_INTERNA_EXTERNA_*.pdf"))
        dados: dict = {"anexos": [a.name for a in sorted((pasta / "anexos").glob("*"))]}
        if pdfs:
            paginas = texto_do_pdf(pdfs[0])
            pecas, sei = pecas_do_processo(paginas)
            declarados, citados = fundamentos_citados(paginas)
            dados.update(
                {
                    "arquivo_relativo": str(pdfs[0]).replace("\\", "/"),
                    "paginas": len(paginas),
                    "pecas": pecas,
                    "processo_sei": sei,
                    "fundamentos": declarados,
                    "dispositivos_citados": citados,
                    "documentos_instrutores": documentos_instrutores(paginas),
                }
            )
        dados["linhas_portal"] = linhas_por_chave[chave]
        vistos[chave] = dados

        destino = (
            saida
            / slug(reg["_modalidade_filtro"], 24)
            / f"{reg['_fonte'].lower()}_{reg['_nome_base']}.md"
        )
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(ficha(reg, dados, evidencias.get(reg["_nome_base"]), hoje), encoding="utf-8")
        dados["_ficha"] = destino.relative_to(saida).as_posix()
        dados["_reg"] = reg
        print(f"  {destino}")

    (saida / "_INDICE.md").write_text(indice(vistos, hoje), encoding="utf-8")
    print(f"\n{len(vistos)} ficha(s) gerada(s) em {saida}")
    return 0


def indice(vistos: dict, hoje: str) -> str:
    linhas = [
        "---",
        "tipo: indice",
        "hierarquia: operacional",
        "tema: contratações do TCE-MG coletadas como referência",
        "fonte: TCE-MG — Portal da Transparência (Compras e Licitações)",
        "vigencia: vigente",
        f"atualizado_em: {hoje}",
        "tags: [tce-mg, indice, referencia-externa, dispensa, pregao]",
        "---",
        "",
        "# Contratações do TCE-MG — índice",
        "",
        "Gerado por `scripts/tce_mg_fichas.py`. Não editar à mão.",
        "Metodologia e limites: [`_METODOLOGIA_COLETA.md`](_METODOLOGIA_COLETA.md).",
        "",
        "## Análises",
        "",
        "- [01 — Como o TCE-MG instrui uma dispensa](analises/01-instrucao-dispensa-tcemg.md)",
        "- [02 — A fase interna do pregão](analises/02-fase-interna-pregao-tcemg.md)",
        "- [03 — Os modelos padronizados (TR, ETP, edital, contrato)](analises/03-modelos-padrao-tcemg.md)",
        "- [04 — O que aplicar em Itanhandu](analises/04-o-que-aplicar-em-itanhandu.md)",
        "",
    ]

    def ordena(item):
        dados = item[1]
        reg = dados["_reg"]
        return (-int(reg["anoLicitacao"]), -int(reg["numeroLicitacao"]))

    def situacao_documental(dados: dict) -> str:
        if dados.get("pecas"):
            return f"{len(dados['pecas'])} peças"
        if not dados.get("arquivo_relativo"):
            return "**sem arquivo** (HTTP 404)"
        return "**PDF sem texto** (digitalizado)"

    for modalidade in ("Dispensa de Licitação", "Pregão"):
        grupo = [i for i in vistos.items() if i[1]["_reg"]["_modalidade_filtro"] == modalidade]
        grupo.sort(key=ordena)
        dispensa = modalidade.startswith("Dispensa")
        coluna = "Fundamento (art. 74/75)" if dispensa else "Situação"
        linhas += [
            f"## {modalidade} ({len(grupo)})",
            "",
            f"| Nº/Ano | Fonte | Objeto | Homologado | {coluna} | Documentação | Ficha |",
            "|---|---|---|---|---|---|---|",
        ]
        for _, dados in grupo:
            reg = dados["_reg"]
            objeto = re.sub(r"\s+", " ", (reg.get("objeto") or "")).strip()
            objeto = (objeto[:70] + "…") if len(objeto) > 70 else objeto
            if dispensa:
                celula = ", ".join(dados.get("fundamentos") or []) or "não identificado"
            else:
                celula = reg.get("situacao") or "não identificado"
            portal = dados.get("linhas_portal") or [reg]
            if len(portal) > 1:
                soma = sum(float(x.get("vlrHomologado") or 0) for x in portal)
                valor = f"{brl(soma)} (soma de {len(portal)} lotes)"
            else:
                valor = brl(reg.get("vlrHomologado"))
            linhas.append(
                f"| {reg['numeroLicitacao']}/{reg['anoLicitacao']} | {reg['_fonte']} "
                f"| {objeto} | {valor} | {celula} "
                f"| {situacao_documental(dados)} | [ficha]({dados['_ficha']}) |"
            )
        linhas.append("")

    sem_arquivo = [d for d in vistos.values() if not d.get("arquivo_relativo")]
    sem_texto = [d for d in vistos.values() if d.get("arquivo_relativo") and not d.get("pecas")]
    linhas += [
        "## Lacunas conhecidas",
        "",
        f"- **{len(sem_arquivo)}** contratação(ões) em que o portal respondeu **HTTP 404** ao pedido "
        "da DOC Interna/Externa: o botão existe na tela, mas não há arquivo associado.",
        f"- **{len(sem_texto)}** em que o PDF veio **digitalizado, sem camada de texto** — depende de "
        "OCR ou leitura manual.",
        "",
        "Em ambos os casos a ficha existe e registra a ausência. Nada foi suposto.",
        "",
    ]
    return "\n".join(linhas)


if __name__ == "__main__":
    raise SystemExit(main())
