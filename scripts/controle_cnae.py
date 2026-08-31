#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
controle_cnae.py — Controle mecânico de contratações por subclasse CNAE.

O script lê `06_precedentes_camara/contratacoes.csv` como fonte da verdade,
consulta `06_precedentes_camara/limites.json` e emite alertas sobre o somatório
do exercício para contratações por dispensa de valor (art. 75, I/II).

Regras de segurança:
  - nunca inventa limite vigente: valor ausente/null = limite não confirmado;
  - nunca inventa CNAE: campos pendentes permanecem `[PREENCHER]`;
  - a saída é parecer mecânico, não decisão jurídica.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Optional

from normalizar_precos import parse_brl

COLUNAS = [
    "data_conclusao",
    "processo",
    "objeto",
    "cnae_subclasse",
    "cnae_descricao",
    "fundamento",
    "valor",
    "conta_para_limite",
    "exercicio",
    "inciso",
]

RAIZ = Path(__file__).resolve().parents[1]
CSV_PADRAO = RAIZ / "06_precedentes_camara" / "contratacoes.csv"
LIMITES_PADRAO = RAIZ / "06_precedentes_camara" / "limites.json"
CONTROLE_MD_PADRAO = RAIZ / "06_precedentes_camara" / "CONTROLE_CONTRATACOES.md"
FONTE_LIMITES_PADRAO = "01_legislacao/limites-vigentes-dispensa-art-75.md"

MARCADOR_INICIO = "<!-- INICIO_TABELA_GERADA -->"
MARCADOR_FIM = "<!-- FIM_TABELA_GERADA -->"


def moeda_para_decimal(valor: Any) -> Optional[Decimal]:
    """Converte valor aceito por parse_brl para Decimal positivo, ou None."""
    normalizado = parse_brl(valor)
    if normalizado is None:
        return None
    try:
        return Decimal(str(normalizado)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None


def decimal_para_brl(valor: Optional[Decimal]) -> str:
    """Formata Decimal como moeda brasileira sem inventar valor ausente."""
    if valor is None:
        return "[PREENCHER]"
    q = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    inteiro, decimal = f"{q:.2f}".split(".")
    grupos = []
    while inteiro:
        grupos.append(inteiro[-3:])
        inteiro = inteiro[:-3]
    return ".".join(reversed(grupos)) + "," + decimal


def carregar_contratacoes(caminho: Path = CSV_PADRAO) -> list[dict[str, str]]:
    """Lê o CSV de contratações com separador ponto e vírgula."""
    if not caminho.exists():
        return []
    with caminho.open("r", encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        return [{col: (linha.get(col) or "").strip() for col in COLUNAS} for linha in leitor]


def gravar_contratacao(registro: dict[str, str], caminho: Path = CSV_PADRAO) -> None:
    """Acrescenta um registro validado ao CSV."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    existe = caminho.exists()
    with caminho.open("a", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";", lineterminator="\n")
        if not existe:
            escritor.writeheader()
        escritor.writerow({col: registro.get(col, "") for col in COLUNAS})


def carregar_limites(caminho: Path = LIMITES_PADRAO) -> dict[str, Any]:
    """Carrega limites.json; se faltar, retorna estrutura vazia."""
    if not caminho.exists():
        return {}
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def _conta_para_limite(valor: str) -> bool:
    return str(valor or "").strip().upper() in {"S", "SIM", "TRUE", "1"}


def _mesma_subclasse(valor: str, cnae: str) -> bool:
    return str(valor or "").strip() == str(cnae or "").strip()


def acumulado_subclasse(
    registros: Iterable[dict[str, str]],
    *,
    cnae: str,
    exercicio: str,
) -> Decimal:
    """Soma valores da mesma subclasse/exercício que contam para limite."""
    total = Decimal("0.00")
    for registro in registros:
        if not _conta_para_limite(registro.get("conta_para_limite", "")):
            continue
        if str(registro.get("exercicio", "")).strip() != str(exercicio):
            continue
        if not _mesma_subclasse(registro.get("cnae_subclasse", ""), cnae):
            continue
        valor = moeda_para_decimal(registro.get("valor"))
        if valor is not None:
            total += valor
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def obter_limite(
    limites: dict[str, Any],
    *,
    exercicio: str,
    inciso: str,
) -> tuple[Optional[Decimal], str, str]:
    """Retorna limite confirmado, decreto e fonte. Limite null permanece None."""
    bloco = limites.get(str(exercicio), {}) if isinstance(limites, dict) else {}
    bruto = bloco.get(str(inciso).upper()) if isinstance(bloco, dict) else None
    decreto = bloco.get("decreto", "[PREENCHER: decreto vigente]") if isinstance(bloco, dict) else "[PREENCHER: decreto vigente]"
    fonte = bloco.get("fonte", FONTE_LIMITES_PADRAO) if isinstance(bloco, dict) else FONTE_LIMITES_PADRAO
    if bruto is None:
        return None, str(decreto), str(fonte)
    return moeda_para_decimal(bruto), str(decreto), str(fonte)


#: Faixas que impedem seguir como dispensa por valor sem decisão humana registrada.
FAIXAS_IMPEDITIVAS = ("vermelho", "estouro", "limite_nao_confirmado", "limite_invalido")


def classificar_faixa(total: Decimal, limite: Optional[Decimal]) -> tuple[str, str]:
    """
    Classifica o percentual de uso do limite, quando confirmado.

    `estouro` é faixa própria, e não um caso de `vermelho`: ultrapassar o limite
    do exercício não é "atenção", é impedimento — a contratação não cabe mais
    como dispensa por valor naquele ramo de atividade. Somar 86% e somar 240% ao
    mesmo rótulo escondia exatamente a situação que o art. 75, § 1º, quer evitar.
    """
    if limite is None:
        return "limite_nao_confirmado", "Limite vigente não confirmado; atualizar limites.json antes de concluir."
    if limite <= 0:
        return "limite_invalido", "Limite informado é inválido; validação humana obrigatória."
    percentual = (total / limite) * Decimal("100")
    if percentual < Decimal("60"):
        return "verde", "Verde: abaixo de 60% do limite confirmado."
    if percentual <= Decimal("85"):
        return "amarelo", "Amarelo: entre 60% e 85%; planejar agregação no PCA."
    if percentual <= Decimal("100"):
        return "vermelho", (
            "Vermelho: acima de 85% do limite. Não enquadrar como dispensa por valor "
            "sem reavaliar o somatório do exercício e justificar nos autos."
        )
    return "estouro", (
        "ESTOURO: o somatório do exercício nesta subclasse ULTRAPASSA o limite vigente. "
        "A contratação não cabe como dispensa por valor neste ramo de atividade — "
        "avaliar licitação, agregação no PCA ou outro fundamento (art. 75, § 1º)."
    )


def simular(
    *,
    objeto: str,
    cnae: str,
    valor: str,
    inciso: str = "II",
    exercicio: str = "2026",
    csv_path: Path = CSV_PADRAO,
    limites_path: Path = LIMITES_PADRAO,
) -> dict[str, Any]:
    """Executa a simulação mecânica de uma nova contratação."""
    valor_decimal = moeda_para_decimal(valor)
    if valor_decimal is None:
        raise ValueError("Valor inválido ou ambíguo; informar valor em padrão BR seguro, como 1.234,56.")
    registros = carregar_contratacoes(csv_path)
    limites = carregar_limites(limites_path)
    acumulado = acumulado_subclasse(registros, cnae=cnae, exercicio=exercicio)
    total = (acumulado + valor_decimal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    limite, decreto, fonte = obter_limite(limites, exercicio=exercicio, inciso=inciso)
    faixa, mensagem = classificar_faixa(total, limite)
    percentual = None
    saldo = None
    if limite is not None and limite > 0:
        percentual = (total / limite * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        saldo = (limite - total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "objeto": objeto,
        "cnae": cnae,
        "exercicio": exercicio,
        "inciso": inciso.upper(),
        "valor_simulado": valor_decimal,
        "acumulado_anterior": acumulado,
        "total_simulado": total,
        "limite": limite,
        "decreto": decreto,
        "fonte_limite": fonte,
        "percentual_limite": percentual,
        "saldo": saldo,
        "faixa": faixa,
        "parecer_mecanico": mensagem,
    }


def _imprimir_simulacao(resultado: dict[str, Any]) -> None:
    print("# Simulação de limite por CNAE")
    print(f"Objeto: {resultado['objeto']}")
    print(f"CNAE subclasse: {resultado['cnae']}")
    print(f"Exercício/inciso: {resultado['exercicio']} / {resultado['inciso']}")
    print(f"Acumulado anterior: R$ {decimal_para_brl(resultado['acumulado_anterior'])}")
    print(f"Valor simulado: R$ {decimal_para_brl(resultado['valor_simulado'])}")
    print(f"Total simulado: R$ {decimal_para_brl(resultado['total_simulado'])}")
    if resultado["limite"] is None:
        print("Limite vigente: [PREENCHER: limite não confirmado]")
        print(f"Arquivo a atualizar: {resultado['fonte_limite']}")
        print(f"Decreto: {resultado['decreto']}")
    else:
        print(f"Limite vigente: R$ {decimal_para_brl(resultado['limite'])}")
        print(f"Percentual usado: {resultado['percentual_limite']}%")
        print(f"Saldo: R$ {decimal_para_brl(resultado['saldo'])}")
    print(f"Parecer mecânico: {resultado['parecer_mecanico']}")
    print("[VALIDAÇÃO HUMANA] Conferir CNAE oficial, fundamento, limite vigente e caso concreto.")


def _validar_registro(args: argparse.Namespace) -> dict[str, str]:
    valor = moeda_para_decimal(args.valor)
    if valor is None:
        raise ValueError("Valor inválido ou ambíguo; informe em padrão seguro, como 1.234,56.")
    if not args.data:
        raise ValueError("Informe --data.")
    if not args.processo:
        raise ValueError("Informe --processo.")
    inciso = args.inciso.upper()
    fundamento = args.fundamento or f"Dispensa — art. 75, {inciso}"
    return {
        "data_conclusao": args.data,
        "processo": args.processo,
        "objeto": args.objeto,
        "cnae_subclasse": args.cnae,
        "cnae_descricao": args.cnae_descricao,
        "fundamento": fundamento,
        "valor": f"{valor:.2f}",
        "conta_para_limite": args.conta_para_limite.upper(),
        "exercicio": str(args.exercicio),
        "inciso": inciso,
    }


def _linha_registro(registro: dict[str, str]) -> str:
    valor = decimal_para_brl(moeda_para_decimal(registro.get("valor")))
    conta = "Sim" if _conta_para_limite(registro.get("conta_para_limite", "")) else "Não"
    cnae = registro.get("cnae_subclasse", "") or "—"
    descricao = registro.get("cnae_descricao", "") or "—"
    return (
        f"| {registro.get('data_conclusao', '') or '—'} "
        f"| {registro.get('processo', '') or '—'} "
        f"| {registro.get('objeto', '') or '—'} "
        f"| {cnae} — {descricao} "
        f"| {registro.get('fundamento', '') or '—'} "
        f"| {valor} "
        f"| {conta} "
        f"| {registro.get('exercicio', '') or '—'} |"
    )


def _gerar_acumulados(registros: list[dict[str, str]], limites: dict[str, Any]) -> list[dict[str, Any]]:
    grupos: dict[tuple[str, str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
    for registro in registros:
        if not _conta_para_limite(registro.get("conta_para_limite", "")):
            continue
        valor = moeda_para_decimal(registro.get("valor"))
        if valor is None:
            continue
        chave = (
            registro.get("exercicio", ""),
            registro.get("cnae_subclasse", ""),
            (registro.get("inciso", "") or "II").upper(),
        )
        grupos[chave] += valor
    saida = []
    for (exercicio, cnae, inciso), total in sorted(grupos.items()):
        limite, _, fonte = obter_limite(limites, exercicio=exercicio, inciso=inciso)
        faixa, mensagem = classificar_faixa(total, limite)
        saldo = (limite - total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if limite is not None else None
        saida.append({
            "exercicio": exercicio,
            "cnae": cnae,
            "total": total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "inciso": inciso,
            "limite": limite,
            "saldo": saldo,
            "faixa": faixa,
            "mensagem": mensagem,
            "fonte": fonte,
        })
    return saida


def gerar_tabelas_markdown(registros: list[dict[str, str]], limites: dict[str, Any]) -> str:
    """Gera a seção de tabelas do controle em Markdown."""
    linhas: list[str] = []
    linhas.append("## Registro de contratações")
    linhas.append("")
    linhas.append("| Data conclusão | Processo / Dispensa | Objeto | CNAE (subclasse) | Modalidade / Fundamento | Valor (R$) | Conta p/ limite? | Exercício |")
    linhas.append("|---|---|---|---|---|---|---|---|")
    if registros:
        linhas.extend(_linha_registro(registro) for registro in registros)
    else:
        linhas.append("| — | — | — | — | — | — | — | — |")
    linhas.append("")
    linhas.append("## Acumulado por subclasse CNAE × exercício (somente dispensa por valor — art. 75, I/II)")
    linhas.append("")
    linhas.append("| Exercício | CNAE (subclasse) | Total acumulado (R$) | Inciso | Limite vigente | Saldo até o limite | Alerta |")
    linhas.append("|---|---|---|---|---|---|---|")
    acumulados = _gerar_acumulados(registros, limites)
    if acumulados:
        for item in acumulados:
            limite_txt = (
                "[PREENCHER: limite vigente não confirmado]"
                if item["limite"] is None else decimal_para_brl(item["limite"])
            )
            saldo_txt = "[CALCULAR após confirmar limite]" if item["saldo"] is None else decimal_para_brl(item["saldo"])
            linhas.append(
                f"| {item['exercicio']} | {item['cnae']} | {decimal_para_brl(item['total'])} "
                f"| {item['inciso']} | {limite_txt} | {saldo_txt} | {item['mensagem']} |"
            )
    else:
        linhas.append("| — | — | — | — | — | — | — |")
    linhas.append("")
    linhas.append(
        "> O limite vigente vem de `01_legislacao/limites-vigentes-dispensa-art-75.md` "
        "(atualizado por decreto). Quando o acumulado de uma subclasse se aproximar do limite, "
        "**alertar** e planejar licitação/agregação no PCA, evitando fracionamento."
    )
    linhas.append("")
    return "\n".join(linhas)


def atualizar_frontmatter_data(texto: str, data_iso: str) -> str:
    """Atualiza o campo atualizado_em do frontmatter, quando presente."""
    return re.sub(r"(?m)^atualizado_em:\s*\d{4}-\d{2}-\d{2}\s*$", f"atualizado_em: {data_iso}", texto, count=1)


def regenerar_controle_md(
    *,
    md_path: Path = CONTROLE_MD_PADRAO,
    csv_path: Path = CSV_PADRAO,
    limites_path: Path = LIMITES_PADRAO,
    data_iso: Optional[str] = None,
) -> None:
    """Regenera a seção marcada do CONTROLE_CONTRATACOES.md."""
    registros = carregar_contratacoes(csv_path)
    limites = carregar_limites(limites_path)
    tabelas = gerar_tabelas_markdown(registros, limites)
    bloco = f"{MARCADOR_INICIO}\n{tabelas}{MARCADOR_FIM}"
    data_final = data_iso or date.today().isoformat()
    texto = md_path.read_text(encoding="utf-8")
    texto = atualizar_frontmatter_data(texto, data_final)
    if MARCADOR_INICIO in texto and MARCADOR_FIM in texto:
        padrao = re.compile(
            re.escape(MARCADOR_INICIO) + r".*?" + re.escape(MARCADOR_FIM),
            flags=re.DOTALL,
        )
        novo = padrao.sub(bloco, texto, count=1)
    else:
        partes = re.split(r"(?m)^## Registro de contratações\s*$", texto, maxsplit=1)
        if len(partes) == 2:
            cabecalho = partes[0].rstrip()
            novo = cabecalho + "\n\n" + bloco + "\n"
        else:
            novo = texto.rstrip() + "\n\n" + bloco + "\n"
    md_path.write_text(novo, encoding="utf-8")


def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Controla contratações por CNAE e limite da dispensa por valor.")
    sub = ap.add_subparsers(dest="comando", required=True)

    comum_sim = argparse.ArgumentParser(add_help=False)
    comum_sim.add_argument("--objeto", required=True, help="Objeto da contratação.")
    comum_sim.add_argument("--cnae", required=True, help="Subclasse CNAE no formato oficial.")
    comum_sim.add_argument("--valor", required=True, help="Valor em padrão BR, ex.: 1.234,56.")
    comum_sim.add_argument("--inciso", default="II", choices=["I", "II"], help="Inciso do art. 75. Default: II.")
    comum_sim.add_argument("--exercicio", default="2026", help="Exercício financeiro. Default: 2026.")

    sim = sub.add_parser("simular", parents=[comum_sim], help="Simula o impacto de nova contratação.")
    sim.add_argument(
        "--como-trava", action="store_true",
        help="Sai com código 1 nas faixas impeditivas (vermelho, estouro, limite não "
             "confirmado). Serve para travar a abertura do processo antes de instruir.",
    )

    reg = sub.add_parser("registrar", parents=[comum_sim], help="Registra contratação concluída no CSV.")
    reg.add_argument("--processo", required=True, help="Número/identificação do processo.")
    reg.add_argument("--data", required=True, help="Data de conclusão em AAAA-MM-DD.")
    reg.add_argument(
        "--cnae-descricao",
        default="[PREENCHER: consultar denominação oficial no IBGE/CONCLA]",
        help="Denominação oficial da subclasse CNAE.",
    )
    reg.add_argument("--fundamento", default="", help="Fundamento/modalidade. Default: Dispensa — art. 75, inciso.")
    reg.add_argument("--conta-para-limite", default="S", choices=["S", "N"], help="Se conta para limite por valor.")

    sub.add_parser("relatorio", help="Regenera as tabelas do controle Markdown a partir do CSV.")
    return ap


def main(argv: Optional[list[str]] = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    try:
        if args.comando == "simular":
            resultado = simular(
                objeto=args.objeto,
                cnae=args.cnae,
                valor=args.valor,
                inciso=args.inciso,
                exercicio=str(args.exercicio),
            )
            _imprimir_simulacao(resultado)
            if getattr(args, "como_trava", False) and resultado["faixa"] in FAIXAS_IMPEDITIVAS:
                print(
                    f"\nIMPEDIMENTO ({resultado['faixa']}): a decisão é humana. "
                    f"Registre nos autos a justificativa ou reavalie o fundamento.",
                    file=sys.stderr,
                )
                return 1
            return 0
        if args.comando == "registrar":
            registro = _validar_registro(args)
            gravar_contratacao(registro)
            print(f"Contratação registrada em {CSV_PADRAO}.")
            print("Rode `python scripts/controle_cnae.py relatorio` para atualizar o Markdown.")
            return 0
        if args.comando == "relatorio":
            regenerar_controle_md()
            print(f"Controle Markdown atualizado em {CONTROLE_MD_PADRAO}.")
            return 0
    except ValueError as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[ERRO] Falha de arquivo: {exc}", file=sys.stderr)
        return 2
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

