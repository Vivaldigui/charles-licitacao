#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iniciar_processo.py — cria a pasta organizada de um processo (itens 4 e 11).

    python scripts/gestao_documental/iniciar_processo.py \
      --numero "PA 031/2026" \
      --objeto "Aquisição de material de limpeza"

O que este script FAZ: o esqueleto mínimo (`00_CONTROLE`, `01_EM_ELABORACAO`,
`99_TEMPORARIOS`), o `PROCESSO.json`, o `DOCUMENTOS.json` vazio, a primeira
linha do log e o painel inicial. As demais pastas nascem quando o primeiro
documento correspondente for registrado — item 4: "não criar pastas vazias
desnecessariamente".

O que este script NÃO faz: decidir modalidade, fundamento legal ou lista de
documentos obrigatórios. A lista gravada é uma SUGESTÃO operacional, marcada
como tal no JSON, a ser confirmada na esteira
(`07_checklists/esteira-contratacao-direta.md`). Enquadramento é decisão
administrativa, não default de script.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from manifesto import (  # noqa: E402
    OperacaoBloqueada,
    Processo,
    SCHEMA_VERSION,
    agora,
    evento,
    linha_log,
    manifesto_vazio,
    preparar_console,
    raiz_processos,
)
from nomes_arquivos import sanitizar_componente, sanitizar_nome_processo  # noqa: E402
from seguranca_repositorio import diagnostico, exigir_destino_seguro  # noqa: E402
from transacoes import Transacao  # noqa: E402

#: Sugestão de instrução para contratação direta por valor. NÃO é norma:
#: confirme na esteira e no Regulamento da Câmara antes de tratar como
#: obrigatória.
DOCUMENTOS_SUGERIDOS = (
    "DFD",
    "PESQUISA_DE_PRECOS",
    "TR",
    "JUSTIFICATIVA_CONTRATACAO_DIRETA",
    "AUTORIZACAO",
    "AVISO",
    "ATA_JULGAMENTO",
    "HOMOLOGACAO",
)


class ProcessoJaExiste(FileExistsError):
    """Já há pasta de processo com esse identificador."""


#: Reconhece "art. 75, II", "art. 75 inciso I", "Dispensa — art. 75, II" etc.
RE_DISPENSA_POR_VALOR = re.compile(
    r"art\.?\s*75[^IVX\d]{0,20}(?:inciso\s*)?\b(I{1,2})\b", re.IGNORECASE
)


def inciso_da_dispensa_por_valor(fundamento: Optional[str]) -> Optional[str]:
    """
    Inciso I ou II do art. 75 citado no fundamento, ou `None`.

    Só a dispensa **por valor** submete-se ao somatório do exercício por ramo de
    atividade (art. 75, § 1º). Inexigibilidade e as demais dispensas do art. 75
    não entram na conta — e travá-las seria erro.
    """
    if not fundamento:
        return None
    achado = RE_DISPENSA_POR_VALOR.search(fundamento)
    return achado.group(1).upper() if achado else None


def simular_limite_cnae(
    *, objeto: str, cnae: str, valor: float, inciso: str, exercicio: str
) -> Optional[dict[str, Any]]:
    """
    Simulação do limite por subclasse CNAE, ou `None` se a ferramenta faltar.

    Import tardio e tolerante: `controle_cnae.py` vive em `scripts/`, fora deste
    pacote, e a abertura de processo não pode quebrar porque o controle mudou de
    lugar. Ausência vira aviso — nunca uma aprovação silenciosa.
    """
    raiz_scripts = str(Path(__file__).resolve().parent.parent)
    if raiz_scripts not in sys.path:
        sys.path.insert(0, raiz_scripts)
    try:
        from controle_cnae import simular  # noqa: PLC0415
    except ImportError:
        return None
    try:
        return simular(
            objeto=objeto,
            cnae=cnae,
            valor=f"{valor:.2f}".replace(".", ","),
            inciso=inciso,
            exercicio=exercicio,
        )
    except (ValueError, OSError):
        return None


def _aferir_limite_cnae(
    *,
    objeto: str,
    cnae_subclasse: Optional[str],
    fundamento: Optional[str],
    valor_estimado: Optional[float],
    exercicio: str,
    justificativa: Optional[str],
) -> Optional[dict[str, Any]]:
    """
    Afere o limite do exercício por subclasse e **bloqueia** o que não cabe.

    Bloqueia apenas em dispensa por valor com CNAE e valor informados: sem esses
    elementos não há o que aferir, e recusar abertura por falta de dado seria
    trocar um risco por uma paralisia. O que falta vira pendência registrada.

    A justificativa humana destrava — e fica gravada no `PROCESSO.json`. É a
    diferença entre decidir e contornar: o `--forcar` some do vocabulário, e o
    que sobra é uma razão escrita, com nome, que o controle interno pode ler.
    """
    inciso = inciso_da_dispensa_por_valor(fundamento)
    if not inciso:
        return None
    if not cnae_subclasse or valor_estimado is None:
        return {
            "situacao": "nao_aferido",
            "inciso": inciso,
            "motivo": (
                "dispensa por valor sem "
                + ("subclasse CNAE" if not cnae_subclasse else "valor estimado")
                + " informada: o limite do exercício NÃO foi aferido"
            ),
        }

    resultado = simular_limite_cnae(
        objeto=objeto, cnae=cnae_subclasse, valor=valor_estimado,
        inciso=inciso, exercicio=exercicio,
    )
    if resultado is None:
        return {
            "situacao": "nao_aferido",
            "inciso": inciso,
            "cnae_subclasse": cnae_subclasse,
            "motivo": "controle CNAE indisponível: o limite do exercício NÃO foi aferido",
        }

    from controle_cnae import FAIXAS_IMPEDITIVAS, decimal_para_brl  # noqa: PLC0415

    faixa = str(resultado["faixa"])
    afericao: dict[str, Any] = {
        "situacao": "aferido",
        "inciso": inciso,
        "cnae_subclasse": cnae_subclasse,
        "exercicio": exercicio,
        "faixa": faixa,
        "acumulado_anterior": str(resultado["acumulado_anterior"]),
        "total_simulado": str(resultado["total_simulado"]),
        "limite": str(resultado["limite"]) if resultado["limite"] is not None else None,
        "percentual_limite": (
            str(resultado["percentual_limite"])
            if resultado["percentual_limite"] is not None else None
        ),
        "parecer_mecanico": resultado["parecer_mecanico"],
        "aferido_em": agora(),
    }
    if faixa not in FAIXAS_IMPEDITIVAS:
        return afericao

    if not justificativa:
        raise OperacaoBloqueada(
            f"Abertura recusada — limite do art. 75, {inciso}, na subclasse "
            f"{cnae_subclasse} (exercício {exercicio}).\n\n"
            f"{resultado['parecer_mecanico']}\n"
            f"Acumulado no exercício: R$ {decimal_para_brl(resultado['acumulado_anterior'])}\n"
            f"Com esta contratação:    R$ {decimal_para_brl(resultado['total_simulado'])}\n"
            f"Limite vigente:          "
            + (f"R$ {decimal_para_brl(resultado['limite'])}"
               if resultado["limite"] is not None else "[não confirmado]")
            + "\n\nA decisão é humana e precisa constar dos autos. Reavalie o "
            "fundamento, agregue no PCA, ou reabra informando "
            "--justificativa-fracionamento \"<razão>\", que fica gravada no "
            "PROCESSO.json."
        )
    afericao["justificativa_humana"] = justificativa
    afericao["situacao"] = "aferido_com_justificativa"
    return afericao


def montar_processo_json(
    *,
    processo_id: str,
    numero: str,
    objeto: str,
    exercicio: str,
    setor_requisitante: Optional[str],
    fundamento: Optional[str],
    modalidade: Optional[str],
    responsaveis: list[str],
    valor_estimado: Optional[float],
    instrumento: Optional[str],
    publicidade: str,
    local_armazenamento: str,
    documentos_obrigatorios: list[str],
    cnae_subclasse: Optional[str] = None,
    afericao_limite_cnae: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Monta o registro do item 11. Campo desconhecido entra como `null`."""
    return {
        "schema_version": SCHEMA_VERSION,
        "processo_id": processo_id,
        "numero": numero,
        "objeto": objeto,
        "exercicio": exercicio,
        "setor_requisitante": setor_requisitante,
        "responsaveis": responsaveis,
        "modalidade": modalidade,
        "fundamento_legal": fundamento,
        "estado_atual": "em_instrucao",
        "fase_atual": "fase_preparatoria",
        "instrumento_contratual": instrumento,
        "fornecedor": None,
        "valor_estimado": valor_estimado,
        "valor_contratado": None,
        "cnae_subclasse": cnae_subclasse,
        "afericao_limite_cnae": afericao_limite_cnae,
        "documentos_obrigatorios": documentos_obrigatorios,
        "origem_lista_obrigatorios": (
            "sugestão operacional do Charles — confirmar em "
            "07_checklists/esteira-contratacao-direta.md e no Regulamento da Câmara"
        ),
        "documentos_existentes": [],
        "documentos_pendentes": list(documentos_obrigatorios),
        "datas": {
            "criacao": agora(),
            "autorizacao": None,
            "publicacao_aviso": None,
            "julgamento": None,
            "homologacao": None,
            "assinatura_contrato": None,
        },
        "local_armazenamento": local_armazenamento,
        "publicidade": publicidade,
        "atualizado_em": agora(),
    }


def painel_inicial(numero: str, objeto: str) -> str:
    return (
        f"# {numero} — {objeto}\n\n"
        "## Situação atual\n\n"
        "Fase: fase preparatória (processo recém-criado)  \n"
        f"Última atualização: {agora()}  \n"
        "Pendências bloqueantes: 0\n\n"
        "## Documentos atuais\n\n"
        "_Nenhum documento registrado até o momento._\n\n"
        "## Próxima ação\n\n"
        "Registrar o DFD.\n\n"
        "---\n"
        "_Painel gerado por `scripts/gestao_documental/gerar_painel.py`. "
        "Não edite este arquivo como fonte: a fonte é `DOCUMENTOS.json`._\n"
    )


def iniciar_processo(
    *,
    numero: str,
    objeto: str,
    exercicio: Optional[str] = None,
    setor_requisitante: Optional[str] = None,
    fundamento: Optional[str] = None,
    modalidade: Optional[str] = None,
    responsaveis: Optional[list[str]] = None,
    valor_estimado: Optional[float] = None,
    instrumento: Optional[str] = None,
    publicidade: str = "publico",
    identificador: Optional[str] = None,
    base: Optional[Path | str] = None,
    documentos_obrigatorios: Optional[list[str]] = None,
    responsavel: str = "Charles",
    cnae_subclasse: Optional[str] = None,
    justificativa_fracionamento: Optional[str] = None,
) -> Processo:
    """Cria a estrutura e os arquivos de controle. Falha não deixa meia pasta."""
    if not numero or not objeto:
        raise ValueError("Número e objeto do processo são obrigatórios.")

    processo_id = sanitizar_nome_processo(identificador or numero)
    if identificador:
        # Identificador informado é usado tal como veio: quem escolheu o nome da
        # pasta não quer vê-lo enfeitado com um resumo do objeto.
        nome_pasta = processo_id
    else:
        resumo = sanitizar_componente(objeto, limite=32)
        nome_pasta = f"{processo_id}_{resumo}" if resumo else processo_id
    raiz = raiz_processos(base) / nome_pasta

    if (raiz / "00_CONTROLE" / "PROCESSO.json").exists():
        raise ProcessoJaExiste(
            f"O processo já existe em {raiz}. Use registrar_documento.py para "
            f"acrescentar documentos, ou escolha outro identificador."
        )

    exigir_destino_seguro(raiz)

    exercicio = exercicio or (numero.split("/")[-1].strip() if "/" in numero else "")
    obrigatorios = list(documentos_obrigatorios or DOCUMENTOS_SUGERIDOS)

    # -- aferição do limite por ramo de atividade (art. 75, § 1º) ----------- #
    # Aqui, e não no fim: descobrir que a subclasse estourou o limite depois do
    # DFD, do TR e da pesquisa de preços custa o trabalho todo — e a conversa
    # com o controle interno fica muito pior.
    afericao = _aferir_limite_cnae(
        objeto=objeto,
        cnae_subclasse=cnae_subclasse,
        fundamento=fundamento,
        valor_estimado=valor_estimado,
        exercicio=exercicio,
        justificativa=justificativa_fracionamento,
    )

    processo = Processo.criar(raiz)
    dados = montar_processo_json(
        processo_id=processo_id,
        numero=numero,
        objeto=objeto,
        exercicio=exercicio,
        setor_requisitante=setor_requisitante,
        fundamento=fundamento,
        modalidade=modalidade,
        responsaveis=responsaveis or [],
        valor_estimado=valor_estimado,
        instrumento=instrumento,
        publicidade=publicidade,
        local_armazenamento=str(raiz),
        documentos_obrigatorios=obrigatorios,
        cnae_subclasse=cnae_subclasse,
        afericao_limite_cnae=afericao,
    )

    pendencias = [
        "- [ ] Confirmar a lista de documentos obrigatórios na esteira.",
        "- [ ] Confirmar o fundamento legal e o instrumento contratual.",
    ]
    if afericao and afericao["situacao"] == "nao_aferido":
        pendencias.append(
            f"- [ ] **Aferir o limite do art. 75 por subclasse CNAE** — {afericao['motivo']}. "
            f"Rode `python scripts/controle_cnae.py simular --como-trava ...` antes de instruir."
        )
    elif afericao and afericao["situacao"] == "aferido_com_justificativa":
        pendencias.append(
            f"- [ ] **Juntar aos autos a justificativa do somatório por ramo de atividade** "
            f"(faixa {afericao['faixa']}, {afericao['percentual_limite']}% do limite). "
            f"Registrada na abertura: \"{afericao['justificativa_humana']}\"."
        )
    elif afericao and afericao["faixa"] == "amarelo":
        pendencias.append(
            f"- [ ] Acompanhar o somatório da subclasse {cnae_subclasse}: já em "
            f"{afericao['percentual_limite']}% do limite do exercício; planejar agregação no PCA."
        )

    with Transacao(processo.temporarios, f"iniciar {processo_id}") as tx:
        tx.gravar_json(processo.arquivo_processo, dados)
        tx.gravar_json(processo.arquivo_documentos, manifesto_vazio(processo_id))
        tx.gravar_texto(processo.arquivo_painel, painel_inicial(numero, objeto))
        tx.gravar_texto(
            processo.arquivo_pendencias,
            "# Pendências\n\n" + "\n".join(pendencias) + "\n",
        )
        tx.acrescentar_linha(
            processo.arquivo_log,
            linha_log(evento(
                "processo_criado",
                responsavel=responsavel,
                motivo=f"Abertura do processo {numero}",
                arquivo=processo.relativo(processo.arquivo_processo),
                objeto=objeto,
            )),
        )
    return processo


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Cria a pasta organizada de um processo.",
        epilog="Processos reais devem ficar fora do repositório: configure "
               "CHARLES_PROCESSOS_DIR.",
    )
    analisador.add_argument("--numero", required=True, help='ex.: "PA 031/2026"')
    analisador.add_argument("--objeto", required=True)
    analisador.add_argument("--exercicio")
    analisador.add_argument("--setor")
    analisador.add_argument("--fundamento", help='ex.: "art. 75, II, Lei 14.133/2021"')
    analisador.add_argument("--modalidade")
    analisador.add_argument("--responsavel", action="append", default=[])
    analisador.add_argument("--valor-estimado", type=float)
    analisador.add_argument("--instrumento",
                            help="contrato | ordem_fornecimento | nota_empenho | outro")
    analisador.add_argument("--publicidade", default="publico",
                            choices=["publico", "restrito", "sigiloso"])
    analisador.add_argument("--identificador", help="nome da pasta; padrão vem do número")
    analisador.add_argument("--base", help="raiz alternativa (sobrepõe CHARLES_PROCESSOS_DIR)")
    analisador.add_argument(
        "--cnae",
        help="subclasse CNAE do objeto (ex.: 4751-2/01). Em dispensa por valor, "
             "afere o somatório do exercício e trava o que não cabe.",
    )
    analisador.add_argument(
        "--justificativa-fracionamento",
        help="razão para abrir mesmo com o limite do exercício comprometido. "
             "Fica gravada no PROCESSO.json e vira pendência de juntada aos autos.",
    )
    argumentos = analisador.parse_args(argv)

    try:
        processo = iniciar_processo(
            numero=argumentos.numero,
            objeto=argumentos.objeto,
            exercicio=argumentos.exercicio,
            setor_requisitante=argumentos.setor,
            fundamento=argumentos.fundamento,
            modalidade=argumentos.modalidade,
            responsaveis=list(argumentos.responsavel),
            valor_estimado=argumentos.valor_estimado,
            instrumento=argumentos.instrumento,
            publicidade=argumentos.publicidade,
            identificador=argumentos.identificador,
            base=argumentos.base,
            cnae_subclasse=argumentos.cnae,
            justificativa_fracionamento=argumentos.justificativa_fracionamento,
        )
    except Exception as erro:  # noqa: BLE001 - a mensagem é o produto do CLI
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    print(f"Processo criado em: {processo.raiz}")
    print(f"Controle: {processo.controle}")
    if not str(processo.raiz).startswith(str(raiz_processos())):
        print("(base alternativa informada por --base)")
    print()
    print(diagnostico())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
