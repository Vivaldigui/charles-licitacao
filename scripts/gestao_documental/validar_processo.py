#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar_processo.py — o manifesto e os arquivos ainda dizem a mesma coisa?

    python scripts/gestao_documental/validar_processo.py --processo PA_031_2026

A regra 34 proíbe as duas divergências simétricas: manifesto sem arquivo e
arquivo sem manifesto. Este script procura exatamente isso, mais o que denuncia
desorganização voltando:

* documento do manifesto cujo arquivo sumiu, ou cujo hash não confere;
* mais de um arquivo do mesmo tipo na área corrente (o "TR_final_2" renascendo);
* nome solto — "final", "novo", "cópia", "TR (1)" — em área corrente;
* versão do histórico ausente ou adulterada;
* documento externo registrado sem arquivo, ou arquivo externo sem registro;
* campos pendentes em documento aprovado, assinado ou publicado;
* locks vencidos e sessões temporárias esquecidas;
* exposição de documento sensível dentro do repositório.

O script não conserta nada. Ele diz o que está errado, com caminho e motivo, e
sai com código 1 quando há erro — serve de porta de auditoria antes de fechar
uma fase.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from hashes import campos_pendentes, sha256_arquivo, verificacao_de_pendencias_possivel  # noqa: E402
from locks import locks_ativos  # noqa: E402
from manifesto import (  # noqa: E402
    AREA_ELABORACAO,
    AREA_EXTERNOS,
    AREA_OFICIAIS,
    Processo,
    STATUS_IMUTAVEIS,
    preparar_console,
)
from nomes_arquivos import TIPOS, existe, nome_suspeito, tipo_provavel  # noqa: E402
from seguranca_repositorio import varrer_processo  # noqa: E402


@dataclass
class Achado:
    gravidade: str  # "erro" | "alerta" | "informacao"
    regra: str
    mensagem: str
    caminho: Optional[str] = None


@dataclass
class RelatorioValidacao:
    processo: str
    achados: list[Achado] = field(default_factory=list)

    @property
    def erros(self) -> list[Achado]:
        return [a for a in self.achados if a.gravidade == "erro"]

    @property
    def alertas(self) -> list[Achado]:
        return [a for a in self.achados if a.gravidade == "alerta"]

    @property
    def integro(self) -> bool:
        return not self.erros

    def texto(self) -> str:
        linhas = [
            f"# Validação do processo {self.processo}",
            "",
            f"- Erros: {len(self.erros)}",
            f"- Alertas: {len(self.alertas)}",
            "",
        ]
        if not self.achados:
            linhas.append("Nenhuma divergência encontrada.")
            return "\n".join(linhas)
        for achado in self.achados:
            local = f" — `{achado.caminho}`" if achado.caminho else ""
            linhas.append(f"- **[{achado.gravidade.upper()}]** ({achado.regra}) {achado.mensagem}{local}")
        linhas += [
            "",
            "> A validação não corrige nada. Cada item aponta um arquivo e um motivo.",
        ]
        return "\n".join(linhas)


def validar(identificador: str, base: Optional[Path | str] = None) -> RelatorioValidacao:
    processo = Processo.abrir(identificador, base)
    relatorio = RelatorioValidacao(processo=processo.identificador)
    adicionar = lambda g, r, m, c=None: relatorio.achados.append(Achado(g, r, m, c))  # noqa: E731

    manifesto = processo.ler_documentos()
    dados = processo.ler_processo()
    documentos = manifesto.get("documentos", {})
    externos = manifesto.get("documentos_externos", [])

    if not dados.get("numero"):
        adicionar("alerta", "processo", "PROCESSO.json sem número do processo.")

    registrados: set[Path] = set()

    # -- 1. manifesto → arquivos ------------------------------------------- #
    for chave, registro in sorted(documentos.items()):
        relativo = registro.get("arquivo_atual")
        if relativo:
            caminho = processo.absoluto(relativo)
            registrados.add(caminho.resolve())
            if not existe(caminho):
                adicionar("erro", "manifesto-x-arquivo",
                          f"{chave}: o manifesto aponta a versão "
                          f"{registro.get('versao_atual')}, mas o arquivo não existe.",
                          relativo)
            else:
                if registro.get("hash_sha256") and sha256_arquivo(caminho) != registro["hash_sha256"]:
                    adicionar("erro", "hash",
                              f"{chave}: o arquivo foi alterado fora do Charles — o "
                              f"hash não confere com o do manifesto.", relativo)
                if registro.get("status") in ("aprovado", *STATUS_IMUTAVEIS):
                    if verificacao_de_pendencias_possivel(caminho):
                        pendentes = campos_pendentes(caminho)
                        if pendentes:
                            adicionar("erro", "campos-pendentes",
                                      f"{chave} está '{registro.get('status')}' com "
                                      f"{len(pendentes)} campo(s) por preencher.",
                                      relativo)
                    else:
                        adicionar("informacao", "campos-pendentes",
                                  f"{chave}: campos pendentes não verificáveis neste "
                                  f"formato.", relativo)
        elif registro.get("status") not in ("arquivado", "cancelado", "substituido"):
            adicionar("alerta", "manifesto",
                      f"{chave} está '{registro.get('status')}' sem arquivo corrente.")

        # Histórico
        for entrada in registro.get("historico") or []:
            caminho = processo.absoluto(entrada.get("arquivo", ""))
            registrados.add(caminho.resolve())
            if not existe(caminho):
                adicionar("erro", "historico",
                          f"{chave} v{entrada.get('versao')}: versão registrada no "
                          f"histórico, mas o arquivo não está lá.", entrada.get("arquivo"))
            elif entrada.get("hash_sha256") and sha256_arquivo(caminho) != entrada["hash_sha256"]:
                adicionar("erro", "historico",
                          f"{chave} v{entrada.get('versao')}: o arquivo do histórico foi "
                          f"alterado — hash divergente.", entrada.get("arquivo"))

        # Representações (item 9)
        for rotulo, valor in (registro.get("representacoes") or {}).items():
            if not valor:
                continue
            caminho = processo.absoluto(valor)
            registrados.add(caminho.resolve())
            if not existe(caminho):
                adicionar("erro", "representacoes",
                          f"{chave}: representação '{rotulo}' registrada e ausente.", valor)

    # -- 2. arquivos → manifesto (área corrente) --------------------------- #
    vistos_por_tipo: dict[str, list[str]] = {}
    for area in (AREA_ELABORACAO, AREA_OFICIAIS):
        pasta = processo.raiz / area
        if not pasta.is_dir():
            continue
        for caminho in sorted(pasta.rglob("*")):
            if not caminho.is_file():
                continue
            relativo = processo.relativo(caminho)
            if caminho.resolve() not in registrados:
                adicionar("erro", "arquivo-x-manifesto",
                          "arquivo em área corrente que não consta do manifesto.",
                          relativo)
            motivo = nome_suspeito(caminho.name)
            if motivo:
                adicionar("alerta", "nome-solto",
                          f"nome de versão solta em área corrente ({motivo}).", relativo)
            provavel = tipo_provavel(caminho.name)
            if provavel:
                vistos_por_tipo.setdefault(provavel, []).append(relativo)

    for tipo, arquivos in sorted(vistos_por_tipo.items()):
        editaveis = [a for a in arquivos if Path(a).suffix.lower() in (".docx", ".docm")]
        if len(editaveis) > 1:
            adicionar("erro", "arquivo-unico",
                      f"há {len(editaveis)} arquivos editáveis do tipo {tipo} na área "
                      f"corrente: {', '.join(editaveis)}. Deve haver apenas um (item 1).")

    # -- 3. documentos externos -------------------------------------------- #
    externos_registrados: set[Path] = set()
    for registro in externos:
        relativo = registro.get("arquivo")
        if not relativo:
            adicionar("alerta", "externos",
                      f"documento externo {registro.get('documento_id')} sem caminho.")
            continue
        caminho = processo.absoluto(relativo)
        externos_registrados.add(caminho.resolve())
        if not existe(caminho):
            adicionar("erro", "externos",
                      f"documento externo registrado e ausente "
                      f"({registro.get('nome_original')}).", relativo)
        elif registro.get("hash_sha256") and sha256_arquivo(caminho) != registro["hash_sha256"]:
            adicionar("erro", "externos",
                      f"documento externo alterado após a importação — o original não "
                      f"deve ser modificado ({registro.get('nome_original')}).", relativo)
        if registro.get("status_validacao") == "em_quarentena":
            adicionar("alerta", "quarentena",
                      f"documento em quarentena aguardando confirmação humana "
                      f"({registro.get('nome_original')}).", relativo)

    pasta_externos = processo.raiz / AREA_EXTERNOS
    if pasta_externos.is_dir():
        for caminho in sorted(pasta_externos.rglob("*")):
            if caminho.is_file() and caminho.resolve() not in externos_registrados:
                adicionar("erro", "externos",
                          "arquivo em 03_DOCUMENTOS_EXTERNOS/ sem registro no manifesto "
                          "— documento externo sem rastreabilidade (regra 34).",
                          processo.relativo(caminho))

    # -- 4. quarentena, locks e temporários -------------------------------- #
    if processo.quarentena.is_dir():
        pendentes = [c for c in processo.quarentena.rglob("*") if c.is_file()]
        if pendentes:
            adicionar("alerta", "quarentena",
                      f"{len(pendentes)} arquivo(s) em 98_QUARENTENA/ aguardando decisão.")
    for lock in locks_ativos(processo.raiz):
        gravidade = "alerta" if lock.expirado() else "informacao"
        adicionar(gravidade, "lock",
                  f"lock de {lock.documento} da sessão {lock.sessao} "
                  f"({'vencido' if lock.expirado() else 'ativo'}, expira {lock.expira_em}).")
    if processo.temporarios.is_dir():
        sessoes = [c for c in processo.temporarios.iterdir() if c.name != "backup"]
        if sessoes:
            adicionar("informacao", "temporarios",
                      f"{len(sessoes)} item(ns) em 99_TEMPORARIOS/ — rode "
                      f"limpar_temporarios.py.")

    # -- 5. exposição no repositório --------------------------------------- #
    for alerta in varrer_processo(processo.raiz):
        if alerta.gravidade == "bloqueio":
            adicionar("erro", "seguranca", alerta.mensagem, alerta.caminho)

    # -- 6. tipos desconhecidos no manifesto ------------------------------- #
    for chave in documentos:
        if chave not in TIPOS:
            adicionar("alerta", "tipo",
                      f"tipo '{chave}' não consta da tabela oficial de tipos documentais.")
    return relatorio


def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Confere a coerência entre manifesto, arquivos e histórico."
    )
    analisador.add_argument("--processo", required=True)
    analisador.add_argument("--json", action="store_true")
    analisador.add_argument("--base")
    argumentos = analisador.parse_args(argv)

    try:
        relatorio = validar(argumentos.processo, argumentos.base)
    except Exception as erro:  # noqa: BLE001
        print(f"ERRO: {erro}", file=sys.stderr)
        return 2

    if argumentos.json:
        print(json.dumps(asdict(relatorio), ensure_ascii=False, indent=2))
    else:
        print(relatorio.texto())
    return 0 if relatorio.integro else 1


if __name__ == "__main__":
    raise SystemExit(main())
