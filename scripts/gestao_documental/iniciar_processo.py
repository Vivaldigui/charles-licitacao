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
import sys
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from manifesto import (  # noqa: E402
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
    )

    with Transacao(processo.temporarios, f"iniciar {processo_id}") as tx:
        tx.gravar_json(processo.arquivo_processo, dados)
        tx.gravar_json(processo.arquivo_documentos, manifesto_vazio(processo_id))
        tx.gravar_texto(processo.arquivo_painel, painel_inicial(numero, objeto))
        tx.gravar_texto(
            processo.arquivo_pendencias,
            "# Pendências\n\n"
            "- [ ] Confirmar a lista de documentos obrigatórios na esteira.\n"
            "- [ ] Confirmar o fundamento legal e o instrumento contratual.\n",
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
