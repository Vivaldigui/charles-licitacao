#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seguranca_repositorio.py — proteção contra vazamento pelo repositório (item 3).

O repositório do Charles é público por vocação: minutas, scripts, checklists e
doutrina. Processo real é outra coisa — tem proposta de fornecedor, CNPJ, CPF,
certidão, e-mail e assinatura. Misturar os dois é o modo mais fácil de publicar
dado pessoal sem perceber.

Este módulo é o guarda dessa fronteira. Ele:

1. diz se um caminho está dentro do repositório;
2. diz se o repositório é (ou deve ser tratado como) público;
3. diz se o caminho está coberto pelo `.gitignore`;
4. procura documento sensível — proposta, certidão, habilitação, e-mail;
5. bloqueia a gravação quando as três coisas se somam;
6. verifica o que está na área de commit (`--verificar-staged`), para uso como
   gancho de pré-commit.

**Duas honestidades necessárias.** Não dá para verificar a visibilidade de um
repositório GitHub sem rede: havendo remoto, ele é tratado como público, por
precaução — `CHARLES_REPO_PUBLICO=0` declara o contrário sob responsabilidade
de quem declara. E nada aqui faz commit nem push: a regra é que arquivo externo
não sobe ao GitHub sem comando expresso do usuário, e o Charles não dá esse
comando sozinho.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from manifesto import (  # noqa: E402
    AREA_EXTERNOS,
    AREA_QUARENTENA,
    AREA_TRABALHO,
    OperacaoBloqueada,
    PASTA_PADRAO_PROCESSOS,
    RAIZ_REPOSITORIO,
    VARIAVEL_PROCESSOS,
    preparar_console,
    processos_em_diretorio_externo,
)

VARIAVEL_PUBLICO = "CHARLES_REPO_PUBLICO"
VARIAVEL_PERMITIR = "CHARLES_PERMITIR_PROCESSO_NO_REPO"

#: Extensões e radicais que denunciam documento com dado de terceiro.
RADICAIS_SENSIVEIS = (
    "proposta", "cotacao", "orcamento", "certidao", "cnd", "fgts", "crf",
    "inss", "habilitacao", "contrato_social", "cnpj", "cpf", "rg_",
    "declaracao", "email", "e_mail", "nota_fiscal", "nf_", "recibo",
    "comprovante", "assinado", "procuracao", "identidade", "extrato_bancario",
)

#: Pastas cujo conteúdo é sensível por natureza.
#:
#: `07_MATERIAL_DE_TRABALHO` entra aqui apesar de guardar produção do próprio
#: Charles: a pesquisa de contratações similares baixa documento de outro órgão,
#: e edital alheio traz CPF de responsável. Classificar como material de
#: trabalho corrige o **destino** do arquivo — não o torna publicável.
PASTAS_SENSIVEIS = (AREA_EXTERNOS, AREA_QUARENTENA, AREA_TRABALHO, "05_ASSINADOS")

EXTENSOES_SENSIVEIS = {".pdf", ".eml", ".msg", ".p7s", ".jpg", ".jpeg", ".png"}


@dataclass
class Alerta:
    gravidade: str  # "bloqueio" | "aviso" | "informacao"
    mensagem: str
    caminho: Optional[str] = None


@dataclass
class Avaliacao:
    dentro_do_repositorio: bool
    repositorio_publico: Optional[bool]
    coberto_por_gitignore: Optional[bool]
    alertas: list[Alerta] = field(default_factory=list)
    #: Preenchido quando `coberto_por_gitignore` é None por não ter sido
    #: possível verificar — para que o relato diga "não verificado", e não
    #: "não coberto".
    motivo_indeterminado: Optional[str] = None

    @property
    def bloqueado(self) -> bool:
        return any(a.gravidade == "bloqueio" for a in self.alertas)

    def texto(self) -> str:
        if not self.alertas:
            return "Sem alertas de segurança."
        return "\n".join(
            f"[{a.gravidade.upper()}] {a.mensagem}"
            + (f" — {a.caminho}" if a.caminho else "")
            for a in self.alertas
        )


# --------------------------------------------------------------------------- #
# Consultas ao repositório
# --------------------------------------------------------------------------- #

def _git(*argumentos: str, cwd: Path = RAIZ_REPOSITORIO) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *argumentos],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def dentro_do_repositorio(caminho: Path | str) -> bool:
    try:
        Path(caminho).resolve().relative_to(RAIZ_REPOSITORIO.resolve())
        return True
    except ValueError:
        return False


def repositorio_publico() -> Optional[bool]:
    """
    True quando deve ser tratado como público. None quando não há repositório.

    A declaração explícita em `CHARLES_REPO_PUBLICO` vence. Sem ela, a presença
    de um remoto basta para a precaução: privado hoje é público amanhã, e o
    dano de um vazamento não se desfaz com `git rm`.
    """
    declarado = os.environ.get(VARIAVEL_PUBLICO, "").strip().lower()
    if declarado in ("0", "false", "nao", "não", "privado"):
        return False
    if declarado in ("1", "true", "sim", "publico", "público"):
        return True
    if not (RAIZ_REPOSITORIO / ".git").exists():
        return None
    remoto = _git("remote")
    return bool(remoto.returncode == 0 and remoto.stdout.strip())


def coberto_por_gitignore(caminho: Path | str) -> Optional[bool]:
    """
    True/False conforme o `.gitignore`; **None quando não se verificou**.

    `None` não significa "não coberto": significa que a pergunta não pôde ser
    respondida — fora do repositório, sem `.git`, ou com o `git` indisponível.
    Quem consome precisa distinguir os dois casos; para a explicação em
    português, ver `motivo_nao_verificavel`.
    """
    caminho = Path(caminho)
    if not dentro_do_repositorio(caminho):
        return None
    if not (RAIZ_REPOSITORIO / ".git").exists():
        return None
    resultado = _git("check-ignore", "-q", str(caminho))
    if resultado.returncode in (0, 1):
        return resultado.returncode == 0
    return None


def motivo_nao_verificavel(caminho: Path | str) -> Optional[str]:
    """
    Por que o `.gitignore` não pôde ser consultado, ou `None` se pôde.

    Existe porque "não sei" e "não está coberto" produziam a mesma mensagem —
    "NÃO coberto pelo .gitignore" —, afirmação que o código não tinha como
    fazer. Sem `.git`, nada foi verificado; a proteção continua conservadora
    (o destino segue recusado), mas o motivo passa a ser verdadeiro.
    """
    caminho = Path(caminho)
    if not dentro_do_repositorio(caminho):
        return None
    if not (RAIZ_REPOSITORIO / ".git").exists():
        return (
            f"não há repositório Git em {RAIZ_REPOSITORIO} — o .gitignore não "
            f"está sendo aplicado a nada e não pôde ser consultado"
        )
    resultado = _git("check-ignore", "-q", str(caminho))
    if resultado.returncode in (0, 1):
        return None
    detalhe = (resultado.stderr or "").strip().splitlines()
    return (
        "não foi possível executar `git check-ignore`"
        + (f": {detalhe[0]}" if detalhe else "")
    )


def arquivo_sensivel(caminho: Path | str) -> Optional[str]:
    """Motivo pelo qual o arquivo parece conter dado de terceiro, ou None."""
    caminho = Path(caminho)
    partes = [p.lower() for p in caminho.parts]
    for pasta in PASTAS_SENSIVEIS:
        if pasta.lower() in partes:
            return f"está em área de documento externo/assinado ({pasta})"
    radical = caminho.name.lower()
    for termo in RADICAIS_SENSIVEIS:
        if termo in radical:
            return f"o nome contém '{termo}'"
    return None


# --------------------------------------------------------------------------- #
# Avaliação de destino
# --------------------------------------------------------------------------- #

def avaliar_destino(caminho: Path | str, *, sensivel: Optional[bool] = None) -> Avaliacao:
    """
    Avalia gravar/armazenar `caminho`. Não grava nada; só classifica o risco.

    `sensivel=True` força o tratamento de documento externo mesmo quando o nome
    não denuncia nada — é o caso da importação, em que se sabe a natureza do
    arquivo antes de olhar o nome.
    """
    caminho = Path(caminho)
    dentro = dentro_do_repositorio(caminho)
    publico = repositorio_publico() if dentro else None
    ignorado = coberto_por_gitignore(caminho) if dentro else None
    indeterminado = (
        motivo_nao_verificavel(caminho) if dentro and ignorado is None else None
    )
    motivo_sensivel = arquivo_sensivel(caminho)
    if sensivel is True and not motivo_sensivel:
        motivo_sensivel = "classificado como documento externo pela operação"
    if sensivel is False:
        motivo_sensivel = None

    alertas: list[Alerta] = []
    if not dentro:
        alertas.append(Alerta(
            "informacao",
            "Destino fora do repositório: não há risco de versionamento acidental.",
            str(caminho),
        ))
        return Avaliacao(dentro, publico, ignorado, alertas, indeterminado)

    if indeterminado:
        alertas.append(Alerta(
            "aviso",
            f"Cobertura do .gitignore não verificada: {indeterminado}.",
            str(caminho),
        ))

    alertas.append(Alerta(
        "aviso",
        f"Destino DENTRO do repositório. Processos reais devem ficar em "
        f"{VARIAVEL_PROCESSOS} (ex.: {VARIAVEL_PROCESSOS}=C:\\Charles\\Processos).",
        str(caminho),
    ))

    if motivo_sensivel and publico is not False:
        if ignorado:
            alertas.append(Alerta(
                "aviso",
                f"Arquivo sensível ({motivo_sensivel}) dentro do repositório, mas "
                f"coberto pelo .gitignore. Não será versionado; ainda assim, o "
                f"lugar dele é fora do repositório.",
                str(caminho),
            ))
        elif ignorado is False:
            alertas.append(Alerta(
                "bloqueio",
                f"Arquivo sensível ({motivo_sensivel}) em repositório tratado como "
                f"público e NÃO coberto pelo .gitignore. Gravação recusada. "
                f"Configure {VARIAVEL_PROCESSOS} ou ajuste o .gitignore.",
                str(caminho),
            ))
        else:
            alertas.append(Alerta(
                "bloqueio",
                f"Arquivo sensível ({motivo_sensivel}) em repositório tratado como "
                f"público, e a cobertura do .gitignore NÃO PÔDE SER VERIFICADA "
                f"({indeterminado}). Gravação recusada por precaução — o que não "
                f"se verificou não conta como protegido. Configure "
                f"{VARIAVEL_PROCESSOS} ou torne a pasta um repositório Git.",
                str(caminho),
            ))
    elif motivo_sensivel:
        # "Declarado" e "inferido" não são a mesma coisa: sem remoto, o privado
        # vale enquanto ninguém publicar o repositório — e quem publica não
        # costuma reler este alerta antes.
        origem = (
            f"declarado privado por {VARIAVEL_PUBLICO}"
            if os.environ.get(VARIAVEL_PUBLICO, "").strip()
            else "tratado como privado porque não tem remoto configurado"
        )
        alertas.append(Alerta(
            "aviso",
            f"Arquivo sensível ({motivo_sensivel}) em repositório {origem}. "
            f"A responsabilidade é de quem decidiu — e a proteção cai no dia em "
            f"que um remoto for adicionado.",
            str(caminho),
        ))
    return Avaliacao(dentro, publico, ignorado, alertas, indeterminado)


def exigir_destino_seguro(caminho: Path | str, *, sensivel: Optional[bool] = None) -> Avaliacao:
    """Avalia e levanta `OperacaoBloqueada` quando há bloqueio."""
    avaliacao = avaliar_destino(caminho, sensivel=sensivel)
    if avaliacao.bloqueado and not _permissao_explicita():
        raise OperacaoBloqueada(
            "Gravação recusada por segurança:\n"
            + avaliacao.texto()
            + f"\n\nPara insistir conscientemente, defina {VARIAVEL_PERMITIR}=1 "
            f"— e responda pela exposição."
        )
    return avaliacao


def _permissao_explicita() -> bool:
    return os.environ.get(VARIAVEL_PERMITIR, "").strip().lower() in ("1", "true", "sim")


# --------------------------------------------------------------------------- #
# Varredura de processo e da área de commit
# --------------------------------------------------------------------------- #

def varrer_processo(raiz_processo: Path | str) -> list[Alerta]:
    """Alertas sobre todos os arquivos sensíveis de um processo dentro do repo."""
    raiz = Path(raiz_processo)
    if not dentro_do_repositorio(raiz):
        return [Alerta("informacao", "Processo fora do repositório.", str(raiz))]
    alertas: list[Alerta] = []
    for arquivo in sorted(raiz.rglob("*")):
        if not arquivo.is_file():
            continue
        motivo = arquivo_sensivel(arquivo)
        if not motivo:
            continue
        ignorado = coberto_por_gitignore(arquivo)
        if ignorado:
            continue
        if ignorado is False:
            alertas.append(Alerta(
                "bloqueio",
                f"Documento sensível versionável ({motivo}).",
                str(arquivo.relative_to(RAIZ_REPOSITORIO)),
            ))
        else:
            alertas.append(Alerta(
                "bloqueio",
                f"Documento sensível ({motivo}) cuja proteção NÃO PÔDE SER "
                f"VERIFICADA: {motivo_nao_verificavel(arquivo)}.",
                str(arquivo.relative_to(RAIZ_REPOSITORIO)),
            ))
    if not alertas:
        alertas.append(Alerta(
            "informacao",
            "Nenhum documento sensível desprotegido encontrado neste processo.",
            str(raiz),
        ))
    return alertas


def verificar_staged() -> list[Alerta]:
    """
    Documentos sensíveis prestes a entrar num commit.

    Serve de gancho de pré-commit — instalação manual, descrita no README do
    módulo. O Charles não instala gancho no `.git` do usuário por conta própria.
    """
    resultado = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    if resultado.returncode != 0:
        return [Alerta("informacao", "Sem repositório git utilizável.")]
    alertas: list[Alerta] = []
    for relativo in resultado.stdout.splitlines():
        relativo = relativo.strip()
        if not relativo:
            continue
        caminho = RAIZ_REPOSITORIO / relativo
        motivo = arquivo_sensivel(caminho)
        dentro_de_processos = relativo.startswith("08_processos_em_andamento/")
        if motivo or (dentro_de_processos and caminho.suffix.lower() in EXTENSOES_SENSIVEIS):
            alertas.append(Alerta(
                "bloqueio",
                f"Arquivo sensível na área de commit ({motivo or 'documento em pasta de processo'}).",
                relativo,
            ))
    return alertas


def diagnostico() -> str:
    """Resumo legível da configuração de armazenamento e exposição."""
    publico = repositorio_publico()
    externo = processos_em_diretorio_externo()
    linhas = [
        "# Segurança do armazenamento de processos",
        "",
        f"- Raiz do repositório: `{RAIZ_REPOSITORIO}`",
        f"- `{VARIAVEL_PROCESSOS}`: "
        + (f"`{os.environ[VARIAVEL_PROCESSOS]}`" if externo
           else "**não configurada** — processos cairiam em "
                f"`{PASTA_PADRAO_PROCESSOS.relative_to(RAIZ_REPOSITORIO)}`"),
        f"- Repositório tratado como público: "
        + {True: "**sim** (há remoto configurado ou declaração explícita)",
           False: f"não (declarado em `{VARIAVEL_PUBLICO}`)",
           None: "não há repositório git"}[publico],
        "",
    ]
    if not externo and publico is not False:
        linhas += [
            "> **Atenção.** Sem `CHARLES_PROCESSOS_DIR`, os processos reais seriam "
            "criados dentro de um repositório tratado como público. Configure a "
            "variável antes de instruir processo com dado de fornecedor.",
            "",
        ]
    return "\n".join(linhas)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    preparar_console()
    analisador = argparse.ArgumentParser(
        description="Verificações de segurança do armazenamento de processos."
    )
    analisador.add_argument("--diagnostico", action="store_true",
                            help="mostra a configuração de armazenamento")
    analisador.add_argument("--processo", help="varre a pasta de um processo")
    analisador.add_argument("--caminho", help="avalia um destino específico")
    analisador.add_argument("--verificar-staged", action="store_true",
                            help="verifica a área de commit (uso como pré-commit)")
    argumentos = analisador.parse_args(argv)

    if not any((argumentos.diagnostico, argumentos.processo, argumentos.caminho,
                argumentos.verificar_staged)):
        argumentos.diagnostico = True

    problemas = 0
    if argumentos.diagnostico:
        print(diagnostico())
    if argumentos.caminho:
        avaliacao = avaliar_destino(argumentos.caminho)
        print(avaliacao.texto())
        problemas += int(avaliacao.bloqueado)
    if argumentos.processo:
        from manifesto import caminho_processo  # import tardio: evita ciclo

        alertas = varrer_processo(caminho_processo(argumentos.processo))
        for alerta in alertas:
            print(f"[{alerta.gravidade.upper()}] {alerta.mensagem} — {alerta.caminho}")
        problemas += sum(a.gravidade == "bloqueio" for a in alertas)
    if argumentos.verificar_staged:
        alertas = verificar_staged()
        for alerta in alertas:
            print(f"[{alerta.gravidade.upper()}] {alerta.mensagem} — {alerta.caminho}")
        problemas += sum(a.gravidade == "bloqueio" for a in alertas)
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
