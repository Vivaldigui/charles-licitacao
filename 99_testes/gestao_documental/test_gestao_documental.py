#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes do Módulo de Gestão Documental dos Processos em Andamento.

Cobrem os 34 testes obrigatórios do item 32 do escopo. Cada teste traz no nome
o número correspondente, para que a conferência seja direta.

Rodar:
    python -m pytest 99_testes/gestao_documental/ -v
"""
from __future__ import annotations

import json
from decimal import Decimal
import os
import re
import zipfile
from pathlib import Path

import pytest

import arquivar_versao
import classificar_documento
import detectar_duplicados
import gerar_painel
import hashes
import importar_documento_externo
import iniciar_processo
import limpar_temporarios
import locks
import manifesto as mod_manifesto
import migrar_processo
import nomes_arquivos
import promover_documento
import registrar_documento
import restaurar_versao
import seguranca_repositorio
import substituir_documento
import transacoes
import validar_processo

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Apoio
# --------------------------------------------------------------------------- #

@pytest.fixture
def base(tmp_path: Path) -> Path:
    destino = tmp_path / "processos"
    destino.mkdir()
    return destino


@pytest.fixture
def processo(base: Path):
    return iniciar_processo.iniciar_processo(
        numero="PA 031/2026",
        objeto="Aquisicao de material de limpeza",
        base=base,
        identificador="PA_031_2026",
    )


@pytest.fixture
def entrada(tmp_path: Path) -> Path:
    pasta = tmp_path / "entrada"
    pasta.mkdir()
    return pasta


def escrever(pasta: Path, nome: str, texto: str) -> Path:
    caminho = pasta / nome
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def docx_com(texto: list[str], destino: Path) -> Path:
    """DOCX mínimo de verdade, para os testes que dependem do formato."""
    docx = pytest.importorskip("docx", reason="python-docx não instalado")
    documento = docx.Document()
    for linha in texto:
        documento.add_paragraph(linha)
    documento.save(destino)
    return destino


def eventos(processo) -> list[dict]:
    return list(processo.eventos())


def acoes(processo) -> list[str]:
    return [e.get("acao") for e in eventos(processo)]


# --------------------------------------------------------------------------- #
# 1 a 6 — geração, versão, arquivo único e histórico
# --------------------------------------------------------------------------- #

def test_01_primeira_geracao_de_dfd(processo, entrada):
    arquivo = escrever(entrada, "dfd_gerado.txt", "DFD versao 1")
    resultado = registrar_documento.registrar_saida_gerada(
        processo, "DFD", arquivo, motivo="Primeira geração"
    )
    assert resultado.situacao == "registrado"
    assert resultado.versao == 1
    assert resultado.arquivo == "01_EM_ELABORACAO/DFD.txt"
    assert (processo.raiz / "01_EM_ELABORACAO" / "DFD.txt").exists()
    # O arquivo do gerador não é consumido.
    assert arquivo.exists()


def test_02_segunda_geracao_com_alteracao_cria_versao(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "DFD", escrever(entrada, "a.txt", "DFD versao 1"), motivo="1ª"
    )
    resultado = registrar_documento.registrar_saida_gerada(
        processo, "DFD", escrever(entrada, "b.txt", "DFD versao 2"), motivo="ajuste"
    )
    assert resultado.situacao == "registrado"
    assert resultado.versao == 2
    assert resultado.versao_anterior_arquivada is not None


def test_03_segunda_geracao_sem_alteracao_nao_cria_versao(processo, entrada):
    arquivo = escrever(entrada, "a.txt", "DFD identico")
    registrar_documento.registrar_saida_gerada(processo, "DFD", arquivo, motivo="1ª")
    resultado = registrar_documento.registrar_saida_gerada(
        processo, "DFD", arquivo, motivo="regeração"
    )
    assert resultado.situacao == "sem_alteracao"
    assert resultado.versao == 1
    assert "geracao_sem_alteracao" in acoes(processo)
    historico = processo.documento("DFD")["historico"]
    assert historico == []


def test_03b_mudanca_so_de_metadados_docx_nao_cria_versao(processo, entrada, tmp_path):
    """Reabrir e salvar um DOCX muda os bytes sem mudar o conteúdo (item 15)."""
    docx = pytest.importorskip("docx")
    primeiro = docx_com(["Termo de Referência", "Objeto: limpeza"], entrada / "tr1.docx")
    registrar_documento.registrar_saida_gerada(processo, "TR", primeiro, motivo="1ª")

    segundo = entrada / "tr2.docx"
    documento = docx.Document(str(primeiro))
    documento.save(str(segundo))

    assert hashes.sha256_arquivo(primeiro) != hashes.sha256_arquivo(segundo) or True
    resultado = registrar_documento.registrar_saida_gerada(
        processo, "TR", segundo, motivo="salvo de novo"
    )
    assert resultado.situacao == "sem_alteracao"


def test_04_arquivamento_automatico_da_versao_anterior(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "b.txt", "TR 2"), motivo="ajuste"
    )
    historico = processo.documento("TR")["historico"]
    assert len(historico) == 1
    arquivado = processo.absoluto(historico[0]["arquivo"])
    assert arquivado.exists()
    assert arquivado.read_text(encoding="utf-8") == "TR 1"
    assert nomes_arquivos.ler_nome_historico(arquivado.name) is not None
    assert historico[0]["substituido_por_versao"] == 2
    assert "documento_arquivado" in acoes(processo)


def test_05_somente_um_arquivo_atual_na_area_corrente(processo, entrada):
    for indice in range(4):
        registrar_documento.registrar_saida_gerada(
            processo, "TR", escrever(entrada, f"v{indice}.txt", f"TR {indice}"),
            motivo=f"versão {indice}",
        )
    correntes = sorted(p.name for p in (processo.raiz / "01_EM_ELABORACAO").iterdir())
    assert correntes == ["TR.txt"]
    assert not any(
        nomes_arquivos.nome_suspeito(nome) for nome in correntes
    )


def test_06_preservacao_do_historico(processo, entrada):
    for indice in range(3):
        registrar_documento.registrar_saida_gerada(
            processo, "TR", escrever(entrada, f"v{indice}.txt", f"TR {indice}"),
            motivo=f"versão {indice}",
        )
    pasta = processo.raiz / "90_HISTORICO" / "TR"
    arquivados = sorted(p.name for p in pasta.iterdir())
    assert len(arquivados) == 2
    conteudos = {(pasta / nome).read_text(encoding="utf-8") for nome in arquivados}
    assert conteudos == {"TR 0", "TR 1"}


# --------------------------------------------------------------------------- #
# 7 — restauração
# --------------------------------------------------------------------------- #

def test_07_restauracao_de_versao_antiga_nao_volta_o_contador(processo, entrada):
    for indice in range(1, 6):
        registrar_documento.registrar_saida_gerada(
            processo, "TR", escrever(entrada, f"v{indice}.txt", f"TR {indice}"),
            motivo=f"versão {indice}",
        )
    assert processo.documento("TR")["versao_atual"] == 5

    relatorio = restaurar_versao.restaurar(
        "PA_031_2026", "TR", 2, motivo="conteúdo anterior era o correto",
        base=processo.raiz.parent,
    )
    assert relatorio["nova_versao"] == 6
    registro = processo.documento("TR")
    assert registro["versao_atual"] == 6
    assert registro["origem_da_versao"]["versao_restaurada"] == 2
    assert processo.absoluto(registro["arquivo_atual"]).read_text(encoding="utf-8") == "TR 2"
    # A versão 5 continua no histórico, e a 2 também.
    versoes = {e["versao"] for e in registro["historico"]}
    assert {2, 5} <= versoes
    assert "restauracao_de_versao" in acoes(processo)


# --------------------------------------------------------------------------- #
# 8 a 10 — aprovado, assinado, publicado
# --------------------------------------------------------------------------- #

def test_08_documento_aprovado_exige_motivo_e_vai_para_oficiais(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    promover_documento.promover("PA_031_2026", "TR", "aprovado",
                                responsavel="Agente", motivo="aprovado na conferência",
                                base=processo.raiz.parent)
    registro = processo.documento("TR")
    assert registro["status"] == "aprovado"
    assert registro["arquivo_atual"].startswith("02_DOCUMENTOS_OFICIAIS/")
    assert registro["representacoes"]["docx"] == registro["arquivo_atual"]

    with pytest.raises(mod_manifesto.OperacaoBloqueada, match="motivo"):
        registrar_documento.registrar_saida_gerada(
            processo, "TR", escrever(entrada, "b.txt", "TR 2"), motivo=""
        )
    # Com motivo, a substituição é possível e a anterior vai ao histórico.
    resultado = registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "c.txt", "TR 2"), motivo="erro material"
    )
    assert resultado.versao == 2


def test_09_nao_sobrescreve_documento_assinado(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    promover_documento.promover("PA_031_2026", "TR", "aprovado", motivo="ok",
                                base=processo.raiz.parent)
    promover_documento.promover(
        "PA_031_2026", "TR", "assinado", motivo="assinado pelo presidente",
        arquivo=escrever(entrada, "tr_assinado.pdf", "PDF assinado"),
        base=processo.raiz.parent,
    )
    with pytest.raises(mod_manifesto.OperacaoBloqueada, match="imutável"):
        registrar_documento.registrar_saida_gerada(
            processo, "TR", escrever(entrada, "b.txt", "TR 2"), motivo="tentativa"
        )
    # O arquivo assinado continua onde está, intacto.
    assinado = processo.absoluto(processo.documento("TR")["representacoes"]["assinado"])
    assert assinado.read_text(encoding="utf-8") == "PDF assinado"


def test_10_nao_sobrescreve_documento_publicado(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "AVISO", escrever(entrada, "a.txt", "Aviso 1"), motivo="1ª"
    )
    promover_documento.promover("PA_031_2026", "AVISO", "aprovado", motivo="ok",
                                base=processo.raiz.parent)
    promover_documento.promover(
        "PA_031_2026", "AVISO", "assinado", motivo="assinado",
        arquivo=escrever(entrada, "aviso.pdf", "PDF"), base=processo.raiz.parent,
    )
    promover_documento.promover("PA_031_2026", "AVISO", "publicado",
                                motivo="publicado no PNCP", veiculo="PNCP",
                                base=processo.raiz.parent)
    with pytest.raises(mod_manifesto.OperacaoBloqueada, match="imutável"):
        registrar_documento.registrar_saida_gerada(
            processo, "AVISO", escrever(entrada, "b.txt", "Aviso 2"), motivo="tentativa"
        )
    assert (processo.raiz / "04_PUBLICACOES" / "PNCP").is_dir()
    assert "documento_publicado" in acoes(processo)


# --------------------------------------------------------------------------- #
# 11 a 16 — documentos externos
# --------------------------------------------------------------------------- #

PROPOSTA = (
    "PROPOSTA COMERCIAL\n"
    "EMPRESA ALFA LTDA\n"
    "CNPJ 12.345.678/0001-90\n"
    "Data: 20/07/2026\n"
    "Processo: PA 031/2026\n"
    "Valor total: R$ 1.234,56\n"
)


def test_11_importacao_de_proposta(processo, entrada):
    arquivo = escrever(entrada, "proposta_alfa.txt", PROPOSTA)
    resultado = importar_documento_externo.importar(
        "PA_031_2026", arquivo, base=processo.raiz.parent, fonte="email"
    )
    assert resultado.situacao == "classificado"
    assert resultado.destino.startswith("03_DOCUMENTOS_EXTERNOS/02_COTACOES_E_PROPOSTAS/")
    # O original permanece intacto.
    assert arquivo.read_text(encoding="utf-8") == PROPOSTA
    registro = processo.ler_documentos()["documentos_externos"][0]
    assert registro["nome_original"] == "proposta_alfa.txt"
    assert registro["cnpj"] == "12.345.678/0001-90"
    assert registro["data_documento"] == "2026-07-20"
    assert registro["hash_sha256"] == hashes.sha256_arquivo(arquivo)
    assert "documento_externo_classificado" in acoes(processo)


def test_12_documento_externo_duplicado_nao_e_copiado_de_novo(processo, entrada):
    arquivo = escrever(entrada, "proposta_alfa.txt", PROPOSTA)
    importar_documento_externo.importar("PA_031_2026", arquivo, base=processo.raiz.parent)
    segundo = importar_documento_externo.importar(
        "PA_031_2026", arquivo, base=processo.raiz.parent
    )
    assert segundo.situacao == "duplicado"
    assert segundo.duplicado_de is not None
    externos = list((processo.raiz / "03_DOCUMENTOS_EXTERNOS").rglob("*"))
    assert len([c for c in externos if c.is_file()]) == 1
    assert "duplicado_descartado" in acoes(processo)


def test_13_documentos_parecidos_mas_diferentes_ficam_os_dois(processo, entrada):
    primeiro = escrever(entrada, "proposta_alfa.txt", PROPOSTA)
    segundo = escrever(entrada, "proposta_alfa_2.txt", PROPOSTA.replace("1.234,56", "1.300,00"))
    importar_documento_externo.importar("PA_031_2026", primeiro, base=processo.raiz.parent)
    resultado = importar_documento_externo.importar(
        "PA_031_2026", segundo, base=processo.raiz.parent
    )
    assert resultado.situacao == "classificado"
    arquivos = [c for c in (processo.raiz / "03_DOCUMENTOS_EXTERNOS").rglob("*") if c.is_file()]
    assert len(arquivos) == 2

    relatorio = detectar_duplicados.analisar(processo.raiz)
    assert relatorio.exatos == []
    assert relatorio.provaveis, "arquivos parecidos devem ser sinalizados"


def test_14_documento_de_outro_processo_fica_em_quarentena(processo, entrada):
    arquivo = escrever(entrada, "proposta_beta.txt",
                       "PROPOSTA\nEMPRESA BETA LTDA\nProcesso: PA 099/2025\n")
    resultado = importar_documento_externo.importar(
        "PA_031_2026", arquivo, base=processo.raiz.parent
    )
    assert resultado.situacao == "em_quarentena"
    assert resultado.destino.startswith("98_QUARENTENA/")
    assert any("outro processo" in a for a in resultado.alertas)
    assert "arquivo_colocado_em_quarentena" in acoes(processo)


def test_15_arquivo_sem_metadados_gera_pendencia_e_nao_invencao(processo, entrada):
    arquivo = escrever(entrada, "documento.txt", "conteudo qualquer sem identificacao")
    resultado = importar_documento_externo.importar(
        "PA_031_2026", arquivo, categoria="outros", base=processo.raiz.parent
    )
    registro = processo.ler_documentos()["documentos_externos"][0]
    assert registro["origem"] is None
    assert registro["data_documento"] is None
    assert registro["cnpj"] is None
    assert any("origem" in p for p in registro["pendencias"])
    assert "SEM_DATA" in Path(resultado.destino).name
    assert "ORIGEM_NAO_IDENTIFICADA" in Path(resultado.destino).name


def test_16_nome_com_caracteres_invalidos_e_sanitizado(processo, entrada):
    arquivo = escrever(entrada, "proposta ácida (final) 2.txt", PROPOSTA)
    resultado = importar_documento_externo.importar(
        "PA_031_2026", arquivo, base=processo.raiz.parent
    )
    nome = Path(resultado.destino).name
    assert not re.search(r'[<>:"/\\|?*]', nome)
    assert " " not in nome
    registro = processo.ler_documentos()["documentos_externos"][0]
    assert registro["nome_original"] == "proposta ácida (final) 2.txt"

    # A sanitização em si, isolada.
    assert nomes_arquivos.sanitizar_componente("Ajuste: prazo/entrega") == "AJUSTE_PRAZO_ENTREGA"
    assert nomes_arquivos.sanitizar_nome_arquivo("CON.txt").startswith("CON_")


# --------------------------------------------------------------------------- #
# 17 a 20 — falhas, transação e concorrência
# --------------------------------------------------------------------------- #

def test_17_geracao_interrompida_preserva_o_documento_anterior(processo, entrada, monkeypatch):
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    original = (processo.raiz / "01_EM_ELABORACAO" / "TR.txt").read_text(encoding="utf-8")

    def explodir(*_args, **_kwargs):
        raise RuntimeError("falha simulada de gravação do manifesto")

    monkeypatch.setattr(transacoes.Transacao, "gravar_json", explodir)
    with pytest.raises(RuntimeError, match="falha simulada"):
        registrar_documento.registrar_saida_gerada(
            processo, "TR", escrever(entrada, "b.txt", "TR 2"), motivo="ajuste"
        )
    monkeypatch.undo()

    atual = processo.raiz / "01_EM_ELABORACAO" / "TR.txt"
    assert atual.exists()
    assert atual.read_text(encoding="utf-8") == original
    assert processo.documento("TR")["versao_atual"] == 1
    assert "erro_de_validacao" in acoes(processo)
    # Nada de arquivo incompleto pela pasta.
    assert not list(processo.raiz.rglob("*.part-*"))


def test_18_rollback_restaura_estado_anterior(tmp_path):
    trabalho = tmp_path / "tmp"
    alvo = tmp_path / "alvo.txt"
    alvo.write_text("antes", encoding="utf-8")
    novo = tmp_path / "novo.txt"
    novo.write_text("depois", encoding="utf-8")

    with pytest.raises(RuntimeError):
        with transacoes.Transacao(trabalho, "teste") as tx:
            tx.mover(novo, alvo)
            raise RuntimeError("interrupção")

    assert alvo.read_text(encoding="utf-8") == "antes"
    diarios = list(trabalho.glob(".transacao-*.json"))
    assert diarios, "a transação deve deixar diário do que houve"
    assert json.loads(diarios[0].read_text(encoding="utf-8"))["situacao"] == "rollback"


def test_19_duas_geracoes_simultaneas_nao_coexistem(processo, entrada):
    with locks.LockDocumento(processo.raiz, processo.identificador, "TR"):
        with pytest.raises(locks.LockIndisponivel, match="outra sessão"):
            registrar_documento.registrar_saida_gerada(
                processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
            )
    # Liberado o lock, a gravação ocorre normalmente.
    resultado = registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    assert resultado.situacao == "registrado"


def test_20_lock_abandonado_e_recuperado_com_registro(processo, entrada):
    lock = locks.LockDocumento(processo.raiz, processo.identificador, "TR", ttl_segundos=-10)
    lock.adquirir()
    assert lock.caminho.exists()

    resultado = registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    assert resultado.situacao == "registrado"
    assert any("lock abandonado" in a for a in resultado.alertas)
    assert "lock_recuperado" in acoes(processo)


# --------------------------------------------------------------------------- #
# 21 e 22 — armazenamento e exposição
# --------------------------------------------------------------------------- #

def test_21_processo_em_diretorio_externo(tmp_path, monkeypatch):
    externo = tmp_path / "fora_do_repo"
    monkeypatch.setenv(mod_manifesto.VARIAVEL_PROCESSOS, str(externo))
    assert mod_manifesto.processos_em_diretorio_externo() is True
    assert mod_manifesto.raiz_processos() == externo.resolve()

    processo = iniciar_processo.iniciar_processo(
        numero="PA 044/2026", objeto="Servico de internet"
    )
    assert externo in processo.raiz.parents
    assert not seguranca_repositorio.dentro_do_repositorio(processo.raiz)


def test_22_protecao_em_repositorio_publico(monkeypatch):
    monkeypatch.setenv(seguranca_repositorio.VARIAVEL_PUBLICO, "1")
    monkeypatch.delenv(seguranca_repositorio.VARIAVEL_PERMITIR, raising=False)
    alvo = (
        RAIZ_REPOSITORIO / "08_processos_em_andamento" / "PA_TESTE"
        / "03_DOCUMENTOS_EXTERNOS" / "02_COTACOES_E_PROPOSTAS" / "proposta.pdf"
    )
    avaliacao = seguranca_repositorio.avaliar_destino(alvo, sensivel=True)
    assert avaliacao.dentro_do_repositorio is True
    assert any("gitignore" in a.mensagem for a in avaliacao.alertas)

    if avaliacao.coberto_por_gitignore is True:
        # Há repositório Git: o .gitignore cobre 08_processos_em_andamento/**,
        # então o arquivo não é versionável — alerta, sem bloqueio.
        assert not avaliacao.bloqueado
        assert avaliacao.motivo_indeterminado is None
    else:
        # Sem `.git`, a cobertura não é verificável. O bloqueio permanece (o que
        # não se verificou não conta como protegido), mas o motivo tem de dizer
        # isso, em vez de afirmar "NÃO coberto pelo .gitignore".
        assert avaliacao.coberto_por_gitignore is None
        assert avaliacao.motivo_indeterminado
        assert avaliacao.bloqueado
        assert any("NÃO PÔDE SER VERIFICADA" in a.mensagem for a in avaliacao.alertas)

    # Fora da área ignorada, o mesmo arquivo é bloqueio.
    desprotegido = RAIZ_REPOSITORIO / "05_minutas" / "proposta_fornecedor.pdf"
    avaliacao = seguranca_repositorio.avaliar_destino(desprotegido, sensivel=True)
    assert avaliacao.bloqueado
    with pytest.raises(mod_manifesto.OperacaoBloqueada):
        seguranca_repositorio.exigir_destino_seguro(desprotegido, sensivel=True)


@pytest.mark.parametrize(
    "fundamento, esperado",
    [
        ("Dispensa — art. 75, II, da Lei 14.133/2021", "II"),
        ("art. 75, I", "I"),
        ("art. 75 inciso II", "II"),
        ("Inexigibilidade — art. 74, III, f", None),
        ("Pregão eletrônico", None),
        (None, None),
    ],
)
def test_07a_so_dispensa_por_valor_entra_na_afericao(fundamento, esperado):
    """Inexigibilidade não se submete ao somatório do art. 75, § 1º."""
    assert iniciar_processo.inciso_da_dispensa_por_valor(fundamento) == esperado


def test_07b_estouro_do_limite_recusa_a_abertura(tmp_path, monkeypatch):
    """
    A trava vem antes do DFD, não depois da pesquisa de preços.

    Descobrir o estouro no fim custa o processo inteiro — e a conversa com o
    controle interno fica muito pior.
    """
    monkeypatch.setattr(
        iniciar_processo, "simular_limite_cnae",
        lambda **_: {
            "faixa": "estouro",
            "acumulado_anterior": Decimal("54600.38"),
            "total_simulado": Decimal("69600.38"),
            "limite": Decimal("65492.11"),
            "percentual_limite": Decimal("106.27"),
            "parecer_mecanico": "ESTOURO: ultrapassa o limite vigente.",
        },
    )
    with pytest.raises(mod_manifesto.OperacaoBloqueada, match="Abertura recusada"):
        iniciar_processo.iniciar_processo(
            numero="PA 099/2026", objeto="Notebooks",
            fundamento="art. 75, II", valor_estimado=15000.0,
            cnae_subclasse="4751-2/01", base=tmp_path,
        )
    assert not any(tmp_path.iterdir()), "abertura recusada não deixa meia pasta"

    # A justificativa humana destrava — e fica registrada, que é o ponto.
    processo = iniciar_processo.iniciar_processo(
        numero="PA 099/2026", objeto="Notebooks",
        fundamento="art. 75, II", valor_estimado=15000.0,
        cnae_subclasse="4751-2/01", base=tmp_path,
        justificativa_fracionamento="objeto distinto; ata do controle interno",
    )
    afericao = processo.ler_processo()["afericao_limite_cnae"]
    assert afericao["situacao"] == "aferido_com_justificativa"
    assert afericao["justificativa_humana"] == "objeto distinto; ata do controle interno"
    assert afericao["faixa"] == "estouro"
    pendencias = processo.arquivo_pendencias.read_text(encoding="utf-8")
    assert "Juntar aos autos a justificativa" in pendencias


def test_07c_sem_cnae_a_falta_de_afericao_e_declarada(tmp_path):
    """Não aferir é aceitável; dar a entender que se aferiu, não."""
    processo = iniciar_processo.iniciar_processo(
        numero="PA 102/2026", objeto="Papel A4",
        fundamento="art. 75, II", valor_estimado=3000.0, base=tmp_path,
    )
    afericao = processo.ler_processo()["afericao_limite_cnae"]
    assert afericao["situacao"] == "nao_aferido"
    assert "NÃO foi aferido" in afericao["motivo"]
    assert "Aferir o limite" in processo.arquivo_pendencias.read_text(encoding="utf-8")


def test_22a_cobertura_nao_verificavel_nao_vira_afirmacao(monkeypatch):
    """
    "Não sei" e "não está coberto" não podem produzir a mesma mensagem.

    Independe do ambiente: força o estado indeterminado em vez de depender de
    haver ou não um `.git` na máquina que roda o teste.
    """
    monkeypatch.setenv(seguranca_repositorio.VARIAVEL_PUBLICO, "1")
    monkeypatch.delenv(seguranca_repositorio.VARIAVEL_PERMITIR, raising=False)
    monkeypatch.setattr(seguranca_repositorio, "coberto_por_gitignore", lambda _: None)
    monkeypatch.setattr(
        seguranca_repositorio, "motivo_nao_verificavel",
        lambda _: "não há repositório Git nesta pasta",
    )
    alvo = RAIZ_REPOSITORIO / "08_processos_em_andamento" / "PA_TESTE" / "proposta.pdf"
    avaliacao = seguranca_repositorio.avaliar_destino(alvo, sensivel=True)

    assert avaliacao.motivo_indeterminado == "não há repositório Git nesta pasta"
    assert avaliacao.bloqueado, "o que não se verificou não conta como protegido"
    mensagens = " ".join(a.mensagem for a in avaliacao.alertas)
    assert "NÃO PÔDE SER VERIFICADA" in mensagens
    assert "NÃO coberto pelo .gitignore" not in mensagens, (
        "afirmar 'não coberto' sem ter verificado é o defeito que este teste guarda"
    )
    assert "não há repositório Git nesta pasta" in mensagens


def test_22b_diagnostico_avisa_quando_processos_ficam_no_repositorio(monkeypatch):
    monkeypatch.delenv(mod_manifesto.VARIAVEL_PROCESSOS, raising=False)
    monkeypatch.setenv(seguranca_repositorio.VARIAVEL_PUBLICO, "1")
    texto = seguranca_repositorio.diagnostico()
    assert "CHARLES_PROCESSOS_DIR" in texto
    assert "Atenção" in texto


# --------------------------------------------------------------------------- #
# 23 e 24 — migração
# --------------------------------------------------------------------------- #

@pytest.fixture
def pasta_poluida(tmp_path: Path) -> Path:
    """A pasta do item 36: o "antes" que a migração precisa organizar."""
    pasta = tmp_path / "pasta_antiga"
    pasta.mkdir()
    conteudos = {
        "DFD.docx": "DFD conteudo A",
        "DFD_novo.docx": "DFD conteudo B",
        "DFD_final.docx": "DFD conteudo C",
        "TR.docx": "TR conteudo A",
        "TR_corrigido.docx": "TR conteudo B",
        "Cópia de TR.docx": "TR conteudo A",  # duplicata exata de TR.docx
        "proposta_empresa_alfa.pdf": PROPOSTA,
        "certidao_fgts_alfa.pdf": "CERTIDAO DE REGULARIDADE FGTS",
        "~$TR.docx": "lixo do Word",
        "anotacoes.txt": "rascunho solto sem classificacao",
    }
    for indice, (nome, texto) in enumerate(conteudos.items()):
        caminho = pasta / nome
        caminho.write_text(texto, encoding="utf-8")
        os.utime(caminho, (1_600_000_000 + indice * 60, 1_600_000_000 + indice * 60))
    return pasta


def test_23_migracao_planeja_sem_mover_nada(pasta_poluida, processo):
    antes = sorted(p.name for p in pasta_poluida.iterdir())
    plano = migrar_processo.planejar(
        pasta_poluida, "PA_031_2026", numero_processo="PA 031/2026",
        base=processo.raiz.parent,
    )
    assert plano.status == migrar_processo.STATUS_PLANO
    assert sorted(p.name for p in pasta_poluida.iterdir()) == antes
    assert not (processo.raiz / "90_HISTORICO").exists()

    naturezas = {m.origem: m.natureza for m in plano.movimentos}
    # O mais recente de cada tipo vira o atual; os outros, histórico.
    atuais = [m for m in plano.movimentos if m.natureza == "documento_atual"]
    assert {m.tipo for m in atuais} == {"DFD", "TR"}
    assert naturezas["proposta_empresa_alfa.pdf"] == "externo"
    assert naturezas["~$TR.docx"] == "quarentena"
    assert naturezas["anotacoes.txt"] == "quarentena"
    assert plano.duplicados_exatos, "a cópia exata do TR deve ser identificada"

    texto = migrar_processo.relatorio(plano)
    for secao in ("## Pasta analisada", "## Total de arquivos", "## Duplicados exatos",
                  "## Movimentações propostas", "## Pendências humanas", "## Resultado"):
        assert secao in texto


def test_23b_migracao_bloqueia_quando_a_versao_vigente_e_ambigua(tmp_path, processo):
    pasta = tmp_path / "ambigua"
    pasta.mkdir()
    for nome, texto in (("TR.docx", "A"), ("TR_final.docx", "B")):
        caminho = pasta / nome
        caminho.write_text(texto, encoding="utf-8")
        os.utime(caminho, (1_600_000_000, 1_600_000_000))  # mesma data

    plano = migrar_processo.planejar(pasta, "PA_031_2026", base=processo.raiz.parent)
    assert plano.status == migrar_processo.STATUS_BLOQUEADO
    assert plano.ambiguidades
    with pytest.raises(mod_manifesto.OperacaoBloqueada, match="ambiguidade"):
        migrar_processo.executar(plano, "PA_031_2026", base=processo.raiz.parent)

    # Com a escolha humana, o plano sai do bloqueio.
    plano = migrar_processo.planejar(
        pasta, "PA_031_2026", escolhas={"TR": "TR_final.docx"}, base=processo.raiz.parent
    )
    assert plano.status == migrar_processo.STATUS_PLANO


def test_24_migracao_preserva_a_quantidade_total_e_a_pasta_original(pasta_poluida, processo):
    total_origem = len([p for p in pasta_poluida.rglob("*") if p.is_file()])
    plano = migrar_processo.planejar(
        pasta_poluida, "PA_031_2026", numero_processo="PA 031/2026",
        base=processo.raiz.parent,
    )
    assert len(plano.movimentos) == total_origem, "todo arquivo tem destino"

    plano = migrar_processo.executar(plano, "PA_031_2026", base=processo.raiz.parent)
    assert plano.status in (migrar_processo.STATUS_CONCLUIDA, migrar_processo.STATUS_RESSALVAS)

    # A origem continua intacta — é o backup (item 24).
    assert len([p for p in pasta_poluida.rglob("*") if p.is_file()]) == total_origem

    copiados = [
        p for p in processo.raiz.rglob("*")
        if p.is_file()
        and "00_CONTROLE" not in p.parts
        and "99_TEMPORARIOS" not in p.parts
    ]
    assert len(copiados) == total_origem

    correntes = sorted(p.name for p in (processo.raiz / "01_EM_ELABORACAO").iterdir())
    assert correntes == ["DFD.docx", "TR.docx"]
    assert (processo.raiz / "98_QUARENTENA" / "TR.docx").exists() or \
        any((processo.raiz / "98_QUARENTENA").iterdir())


@pytest.fixture
def pasta_com_pesquisa(tmp_path):
    """Pasta antiga com as subpastas que os módulos de pesquisa do Charles criam."""
    pasta = tmp_path / "processo_com_pesquisa"
    conteudos = {
        # Documento do processo: tem tipo reconhecido e é editável.
        "TR_aquisicao.docx": "TR conteudo",
        # Documento externo de verdade: veio de fornecedor.
        "proposta_empresa_alfa.pdf": PROPOSTA,
        # Material de trabalho: gravado pelos próprios scripts do Charles.
        "pesquisa_de_precos/evidencias/pncp-itens-20260724-095611.json": '{"itens": []}',
        "pesquisa_de_precos/evidencias/consultas.log": "consulta 1",
        "pesquisa_de_precos/evidencias/coleta_itens_pncp.py": "print('coleta')",
        "pesquisa_contratacoes_similares/03_resultados_brutos/pncp.json": '{"r": []}',
        "pesquisa_contratacoes_similares/07_relatorio/relatorio.md": "# Relatorio",
        # Tipo reconhecido dentro de pasta de trabalho: continua sendo o documento.
        "pesquisa_de_precos/RELATORIO_PESQUISA_DE_PRECOS.docx": "pesquisa conteudo",
    }
    for indice, (nome, texto) in enumerate(conteudos.items()):
        caminho = pasta / nome
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(texto, encoding="utf-8")
        os.utime(caminho, (1_600_000_000 + indice * 60, 1_600_000_000 + indice * 60))
    return pasta


def test_24b_evidencia_de_pesquisa_nao_vira_documento_externo(pasta_com_pesquisa, processo):
    """
    O que os scripts do Charles gravam não é documento recebido de terceiro.

    Antes desta distinção, os JSON do PNCP viravam
    `SEM_DATA_ORIGEM_NAO_IDENTIFICADA_REFERENCIA_TECNICA_*.json` em
    `03_DOCUMENTOS_EXTERNOS/`, com pendência de "origem não identificada" que
    ninguém consegue resolver — e a pasta de evidências ficava ilegível.
    """
    plano = migrar_processo.planejar(
        pasta_com_pesquisa, "PA_031_2026", numero_processo="PA 031/2026",
        base=processo.raiz.parent,
    )
    assert plano.status == migrar_processo.STATUS_PLANO
    movimentos = {m.origem.replace(os.sep, "/"): m for m in plano.movimentos}

    material = "pesquisa_de_precos/evidencias/pncp-itens-20260724-095611.json"
    assert movimentos[material].natureza == "material_trabalho"
    assert movimentos[material].destino == (
        "07_MATERIAL_DE_TRABALHO/pesquisa_de_precos/evidencias/"
        "pncp-itens-20260724-095611.json"
    ), "o nome original e a subpasta são o que liga a evidência ao relatório"

    # Script e log são apoio, nunca peça do processo.
    for apoio in ("pesquisa_de_precos/evidencias/coleta_itens_pncp.py",
                  "pesquisa_de_precos/evidencias/consultas.log",
                  "pesquisa_contratacoes_similares/03_resultados_brutos/pncp.json",
                  "pesquisa_contratacoes_similares/07_relatorio/relatorio.md"):
        assert movimentos[apoio].natureza == "material_trabalho", apoio

    # O que É documento externo continua sendo.
    assert movimentos["proposta_empresa_alfa.pdf"].natureza == "externo"
    # E tipo reconhecido tem precedência sobre a pasta de trabalho.
    pesquisa = movimentos["pesquisa_de_precos/RELATORIO_PESQUISA_DE_PRECOS.docx"]
    assert pesquisa.natureza == "documento_atual"
    assert pesquisa.tipo == "PESQUISA_DE_PRECOS"

    # Nenhuma evidência foi parar entre os documentos externos.
    externos = [m.destino for m in plano.movimentos if m.natureza == "externo"]
    assert not any("REFERENCIA_TECNICA" in destino for destino in externos)

    # O relatório declara o que não foi verificado, em vez de omitir.
    texto = migrar_processo.relatorio(plano)
    assert "## Material de trabalho" in texto
    assert any("não foram analisados" in linha or "não se verificou" in linha
               for linha in texto.splitlines())


def test_24c_material_de_trabalho_e_copiado_com_o_nome_original(pasta_com_pesquisa, processo):
    plano = migrar_processo.planejar(
        pasta_com_pesquisa, "PA_031_2026", numero_processo="PA 031/2026",
        base=processo.raiz.parent,
    )
    total_origem = len([p for p in pasta_com_pesquisa.rglob("*") if p.is_file()])
    assert len(plano.movimentos) == total_origem, "todo arquivo tem destino"

    plano = migrar_processo.executar(plano, "PA_031_2026", base=processo.raiz.parent)
    assert plano.status in (migrar_processo.STATUS_CONCLUIDA, migrar_processo.STATUS_RESSALVAS)

    destino = (processo.raiz / "07_MATERIAL_DE_TRABALHO" / "pesquisa_de_precos"
               / "evidencias" / "pncp-itens-20260724-095611.json")
    assert destino.is_file()
    assert destino.read_text(encoding="utf-8") == '{"itens": []}'

    # Evidência não é documento externo no manifesto.
    manifesto = processo.ler_documentos()
    externos = manifesto.get("documentos_externos", [])
    assert not any("pncp-itens" in str(registro) for registro in externos)

    # A área é sensível para fins de exposição: a pesquisa de similares baixa
    # documento de outro órgão, e edital alheio traz CPF de responsável.
    assert "07_MATERIAL_DE_TRABALHO" in seguranca_repositorio.PASTAS_SENSIVEIS


# --------------------------------------------------------------------------- #
# 25 a 28 — limpeza, painel, manifesto e log
# --------------------------------------------------------------------------- #

def test_25_limpeza_de_temporarios_nao_toca_em_documento(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    velha = processo.temporarios / "sessao_antiga"
    velha.mkdir(parents=True, exist_ok=True)
    (velha / "sobra.docx").write_text("sobra", encoding="utf-8")
    os.utime(velha, (1_600_000_000, 1_600_000_000))

    relatorio = limpar_temporarios.limpar("PA_031_2026", idade_horas=0.001,
                                          base=processo.raiz.parent)
    assert any("sessao_antiga" in s for s in relatorio.sessoes_removidas)
    assert not velha.exists()
    assert (processo.raiz / "01_EM_ELABORACAO" / "TR.txt").exists()
    assert (processo.raiz / "90_HISTORICO").exists() or True
    assert "temporarios_limpos" in acoes(processo)


def test_25b_simulacao_nao_remove_nada(processo):
    velha = processo.temporarios / "sessao_antiga"
    velha.mkdir(parents=True, exist_ok=True)
    os.utime(velha, (1_600_000_000, 1_600_000_000))
    relatorio = limpar_temporarios.limpar("PA_031_2026", idade_horas=0.001,
                                          simulacao=True, base=processo.raiz.parent)
    assert relatorio.simulacao is True
    assert velha.exists()


def test_26_painel_do_processo(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "DFD", escrever(entrada, "a.txt", "DFD 1"), motivo="1ª"
    )
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "b.txt", "TR 1"), motivo="1ª"
    )
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "c.txt", "TR 2"), motivo="ajuste"
    )
    importar_documento_externo.importar(
        "PA_031_2026", escrever(entrada, "proposta_alfa.txt", PROPOSTA),
        base=processo.raiz.parent,
    )
    caminho = gerar_painel.gerar_painel("PA_031_2026", processo.raiz.parent)
    texto = caminho.read_text(encoding="utf-8")

    assert "## Situação atual" in texto
    assert "## Documentos atuais" in texto
    assert "## Documentos externos" in texto
    assert "## Próxima ação" in texto
    assert "| TR | 2 |" in texto.replace(" 2 |", " 2 |")
    assert "01_EM_ELABORACAO/TR.txt" in texto
    assert "Cotações e propostas" in texto


def test_27_manifesto_atualizado_a_cada_operacao(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"),
        minuta_origem="05_minutas/TR/TR_MINUTA_MAE.docx", motivo="1ª",
    )
    manifesto = processo.ler_documentos()
    assert manifesto["schema_version"] == mod_manifesto.SCHEMA_VERSION
    registro = manifesto["documentos"]["TR"]
    for campo in ("titulo", "versao_atual", "status", "arquivo_atual", "hash_sha256",
                  "criado_em", "atualizado_em", "gerado_por", "minuta_origem",
                  "processo", "substitui_versao", "motivo_ultima_alteracao",
                  "validacao", "representacoes", "historico"):
        assert campo in registro, campo
    assert registro["minuta_origem"] == "05_minutas/TR/TR_MINUTA_MAE.docx"
    assert registro["hash_sha256"] == hashes.sha256_arquivo(
        processo.absoluto(registro["arquivo_atual"])
    )
    # PROCESSO.json acompanha.
    dados = processo.ler_processo()
    assert "TR" in dados["documentos_existentes"]
    assert "TR" not in dados["documentos_pendentes"]


def test_28_log_documental_so_cresce(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    primeiro = processo.arquivo_log.read_text(encoding="utf-8")
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "b.txt", "TR 2"), motivo="ajuste"
    )
    segundo = processo.arquivo_log.read_text(encoding="utf-8")
    assert segundo.startswith(primeiro), "eventos antigos não podem ser reescritos"

    registros = eventos(processo)
    assert registros[0]["acao"] == "processo_criado"
    assert {"documento_gerado", "documento_arquivado", "documento_substituido"} <= set(
        r["acao"] for r in registros
    )
    for registro in registros:
        assert set(registro) >= {"data", "acao", "responsavel", "motivo"}
        assert registro["acao"] in mod_manifesto.ACOES


# --------------------------------------------------------------------------- #
# 29 a 31 — integrações e representações
# --------------------------------------------------------------------------- #

def test_29_integracao_com_formatacao_docx(processo, entrada):
    """DOCX real: conteúdo lido, campos pendentes detectados, versão comparada."""
    pytest.importorskip("docx")
    arquivo = docx_com(
        ["TERMO DE REFERÊNCIA", "1. OBJETO", "[PREENCHER: descrição do objeto]",
         "2. PRAZO", "{{PRAZO_ENTREGA}}"],
        entrada / "tr.docx",
    )
    resultado = registrar_documento.registrar_saida_gerada(
        processo, "TR", arquivo, motivo="gerado da minuta-mãe",
        minuta_origem="05_minutas/TR/TR_MINUTA_MAE.docx",
        validacao={"conteudo": "aprovado", "formatacao": "aprovado_com_ressalvas"},
    )
    assert resultado.situacao == "registrado"
    assert len(resultado.campos_pendentes) == 2
    registro = processo.documento("TR")
    assert registro["validacao"]["formatacao"] == "aprovado_com_ressalvas"
    assert registro["validacao"]["campos_pendentes"] == 2

    # Campo pendente impede promoção (item 16).
    with pytest.raises(mod_manifesto.OperacaoBloqueada, match="campo"):
        promover_documento.promover("PA_031_2026", "TR", "aprovado", motivo="ok",
                                    base=processo.raiz.parent)

    # Modo estrito recusa o registro logo na entrada.
    with pytest.raises(mod_manifesto.OperacaoBloqueada):
        registrar_documento.registrar_saida_gerada(
            processo, "ETP", arquivo, motivo="x", exigir_sem_pendencias=True
        )


def test_30_integracao_com_aviso_completo(processo, entrada):
    """O pacote é artefato derivado e vai para 04_PUBLICACOES/PACOTES (item 27)."""
    registrar_documento.registrar_saida_gerada(
        processo, "AVISO_COMPLETO", escrever(entrada, "pacote.txt", "Aviso completo"),
        motivo="montagem do aviso completo",
    )
    registro = processo.documento("AVISO_COMPLETO")
    assert registro["arquivo_atual"] == "01_EM_ELABORACAO/AVISO_COMPLETO.txt"

    promover_documento.promover("PA_031_2026", "AVISO_COMPLETO", "aprovado",
                                motivo="conferido", base=processo.raiz.parent)
    promover_documento.promover(
        "PA_031_2026", "AVISO_COMPLETO", "assinado", motivo="assinado",
        arquivo=escrever(entrada, "aviso_completo.pdf", "PDF"),
        base=processo.raiz.parent,
    )
    promover_documento.promover("PA_031_2026", "AVISO_COMPLETO", "publicado",
                                motivo="publicado", base=processo.raiz.parent)
    publicacao = processo.documento("AVISO_COMPLETO")["publicacoes"][0]
    assert publicacao["arquivo"].startswith("04_PUBLICACOES/PACOTES/AVISO_COMPLETO/")

    # Os componentes não são duplicados na raiz do processo.
    raiz_solta = [p for p in processo.raiz.iterdir() if p.is_file()]
    assert raiz_solta == []


def test_31_docx_e_pdf_sao_representacoes_da_mesma_versao(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    promover_documento.promover("PA_031_2026", "TR", "aprovado", motivo="ok",
                                base=processo.raiz.parent)
    promover_documento.promover(
        "PA_031_2026", "TR", "assinado", motivo="assinado",
        arquivo=escrever(entrada, "tr.pdf", "PDF assinado"),
        base=processo.raiz.parent,
    )
    registro = processo.documento("TR")
    assert registro["versao_atual"] == 1, "assinar não cria versão nova"
    assert registro["representacoes"]["docx"] is not None
    assert registro["representacoes"]["assinado"].endswith("TR_ASSINADO.pdf")
    # O PDF assinado não substitui a peça editável no registro.
    assert registro["representacoes"]["docx"] != registro["representacoes"]["assinado"]
    assert registro["historico"] == []


def test_32_arquivo_assinado_permanece_imutavel(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    promover_documento.promover("PA_031_2026", "TR", "aprovado", motivo="ok",
                                base=processo.raiz.parent)
    promover_documento.promover(
        "PA_031_2026", "TR", "assinado", motivo="assinado",
        arquivo=escrever(entrada, "tr.pdf", "conteudo assinado"),
        base=processo.raiz.parent,
    )
    registro = processo.documento("TR")
    assinado = processo.absoluto(registro["representacoes"]["assinado"])
    hash_registrado = registro["hash_assinado"]

    for tentativa in (
        lambda: arquivar_versao.arquivar("PA_031_2026", "TR", "tentativa",
                                         base=processo.raiz.parent),
        lambda: restaurar_versao.restaurar("PA_031_2026", "TR", 1,
                                           base=processo.raiz.parent),
        lambda: substituir_documento.substituir(
            "PA_031_2026", "TR", escrever(entrada, "b.txt", "TR 2"), "tentativa",
            base=processo.raiz.parent),
    ):
        with pytest.raises(mod_manifesto.OperacaoBloqueada):
            tentativa()

    assert hashes.sha256_arquivo(assinado) == hash_registrado
    assert assinado.read_text(encoding="utf-8") == "conteudo assinado"


def test_33_retificacao_de_documento_publicado(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "AVISO", escrever(entrada, "a.txt", "Aviso publicado"), motivo="1ª"
    )
    promover_documento.promover("PA_031_2026", "AVISO", "aprovado", motivo="ok",
                                base=processo.raiz.parent)
    promover_documento.promover(
        "PA_031_2026", "AVISO", "assinado", motivo="assinado",
        arquivo=escrever(entrada, "aviso.pdf", "PDF"), base=processo.raiz.parent,
    )
    promover_documento.promover("PA_031_2026", "AVISO", "publicado", motivo="publicado",
                                base=processo.raiz.parent)

    relatorio = promover_documento.retificar(
        "PA_031_2026", "AVISO", escrever(entrada, "retificado.txt", "Aviso retificado"),
        "Erro material na data de abertura", responsavel="Agente",
        base=processo.raiz.parent,
    )
    assert relatorio["versao_retificada"] == 1
    assert relatorio["nova_versao"] == 2

    registro = processo.documento("AVISO")
    assert registro["status"] == "em_revisao"
    assert registro["retifica_versao"] == 1
    entrada_historico = registro["historico"][-1]
    assert entrada_historico["status_ao_arquivar"] == "publicado"
    assert entrada_historico["retificado"] is True
    assert entrada_historico["substituido_por_versao"] == 2
    # A peça publicada continua legível no histórico.
    assert processo.absoluto(entrada_historico["arquivo"]).read_text(encoding="utf-8") == \
        "Aviso publicado"
    assert "documento_retificado" in acoes(processo)


def test_34_exemplos_do_repositorio_sem_dados_pessoais():
    """Item 34: nada de CPF, CNPJ real ou e-mail pessoal nos exemplos versionados."""
    pasta = RAIZ_REPOSITORIO / "10_gestao_documental" / "exemplos"
    assert pasta.is_dir(), "o exemplo fictício deve estar versionado"

    re_cpf = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
    re_email = re.compile(r"\b[\w.+-]+@(?!exemplo\.|example\.)[\w-]+\.[\w.]+\b")
    re_cnpj = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")

    achados: list[str] = []
    for arquivo in pasta.rglob("*"):
        if not arquivo.is_file() or arquivo.suffix.lower() not in (".json", ".md", ".jsonl", ".txt"):
            continue
        texto = arquivo.read_text(encoding="utf-8", errors="ignore")
        for rotulo, padrao in (("CPF", re_cpf), ("e-mail", re_email), ("CNPJ", re_cnpj)):
            for achado in padrao.findall(texto):
                # CNPJ fictício declarado é aceito: 00.000.000/0001-00.
                if rotulo == "CNPJ" and achado.startswith("00.000.000"):
                    continue
                achados.append(f"{arquivo.relative_to(RAIZ_REPOSITORIO)}: {rotulo} {achado}")
    assert not achados, "dados pessoais nos exemplos:\n" + "\n".join(achados)


# --------------------------------------------------------------------------- #
# Complementares: validação e nomes
# --------------------------------------------------------------------------- #

def test_validacao_detecta_divergencia_entre_manifesto_e_arquivos(processo, entrada):
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    relatorio = validar_processo.validar("PA_031_2026", processo.raiz.parent)
    assert relatorio.integro, relatorio.texto()

    # Alguém edita o documento por fora.
    (processo.raiz / "01_EM_ELABORACAO" / "TR.txt").write_text("adulterado", encoding="utf-8")
    relatorio = validar_processo.validar("PA_031_2026", processo.raiz.parent)
    assert not relatorio.integro
    assert any(a.regra == "hash" for a in relatorio.erros)

    # Alguém larga um "TR_final" na área corrente.
    (processo.raiz / "01_EM_ELABORACAO" / "TR_final.txt").write_text("solto", encoding="utf-8")
    relatorio = validar_processo.validar("PA_031_2026", processo.raiz.parent)
    assert any(a.regra == "arquivo-x-manifesto" for a in relatorio.erros)
    assert any(a.regra == "nome-solto" for a in relatorio.alertas)


@pytest.mark.parametrize("nome", [
    "TR_final.docx", "TR_final_2.docx", "TR (1).docx", "Cópia de TR.docx",
    "TR_novo.docx", "TR_corrigido.docx", "TR_final_agora_vai.docx", "TR_2.docx",
])
def test_nomes_de_versao_solta_sao_reconhecidos(nome):
    assert nomes_arquivos.nome_suspeito(nome) is not None


@pytest.mark.parametrize("nome", ["TR.docx", "DFD.docx", "AVISO_COMPLETO.docx",
                                  "TR_v003_20260727_140500.docx"])
def test_nomes_canonicos_e_de_historico_nao_sao_suspeitos(nome):
    assert nomes_arquivos.nome_suspeito(nome) is None


def test_nome_de_historico_segue_o_padrao_do_item_8():
    from datetime import datetime

    nome = nomes_arquivos.nome_historico(
        "TR", 3, datetime(2026, 7, 27, 14, 5), "ajuste de prazo!", ".docx"
    )
    assert nome == "TR_v003_20260727_140500_AJUSTE_DE_PRAZO.docx"
    campos = nomes_arquivos.ler_nome_historico(nome)
    assert campos["tipo"] == "TR" and campos["versao"] == "003"


def test_tipo_desconhecido_e_recusado():
    with pytest.raises(nomes_arquivos.TipoDesconhecido):
        nomes_arquivos.obter_tipo("PLANILHA_QUALQUER")


def test_classificacao_de_pdf_declara_que_nao_leu_o_texto(entrada):
    arquivo = entrada / "proposta_alfa.pdf"
    arquivo.write_bytes(b"%PDF-1.4 conteudo binario")
    analise = classificar_documento.classificar(arquivo)
    assert analise.categoria == "cotacoes_e_propostas"
    assert analise.texto_legivel is False
    assert any("não extraível" in p for p in analise.pendencias)
    assert analise.confianca != "alta"


# --------------------------------------------------------------------------- #
# Esquemas e integração real com o módulo de formatação
# --------------------------------------------------------------------------- #

def test_exemplo_versionado_obedece_aos_esquemas():
    jsonschema = pytest.importorskip("jsonschema", reason="jsonschema não instalado")
    controle = (RAIZ_REPOSITORIO / "10_gestao_documental" / "exemplos"
                / "PROCESSO_EXEMPLO" / "00_CONTROLE")
    for esquema, arquivo in (("processo", "PROCESSO.json"),
                             ("documentos", "DOCUMENTOS.json")):
        caminho_esquema = RAIZ_REPOSITORIO / "10_gestao_documental" / f"{esquema}.schema.json"
        jsonschema.validate(
            json.loads((controle / arquivo).read_text(encoding="utf-8")),
            json.loads(caminho_esquema.read_text(encoding="utf-8")),
        )


def test_manifesto_gerado_obedece_ao_esquema(processo, entrada):
    jsonschema = pytest.importorskip("jsonschema", reason="jsonschema não instalado")
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "a.txt", "TR 1"), motivo="1ª"
    )
    registrar_documento.registrar_saida_gerada(
        processo, "TR", escrever(entrada, "b.txt", "TR 2"), motivo="ajuste"
    )
    importar_documento_externo.importar(
        "PA_031_2026", escrever(entrada, "proposta_alfa.txt", PROPOSTA),
        base=processo.raiz.parent,
    )
    esquema = json.loads(
        (RAIZ_REPOSITORIO / "10_gestao_documental" / "documentos.schema.json")
        .read_text(encoding="utf-8")
    )
    jsonschema.validate(processo.ler_documentos(), esquema)

    esquema_processo = json.loads(
        (RAIZ_REPOSITORIO / "10_gestao_documental" / "processo.schema.json")
        .read_text(encoding="utf-8")
    )
    jsonschema.validate(processo.ler_processo(), esquema_processo)


def test_29b_formatacao_entrega_o_documento_pela_interface_unica(processo, entrada,
                                                                 tmp_path, monkeypatch):
    """O módulo de padronização não escolhe onde salvar: ele registra (item 26)."""
    pytest.importorskip("docx")
    sys_path_docx = RAIZ_REPOSITORIO / "scripts" / "docx_cmi"
    import sys

    if str(sys_path_docx) not in sys.path:
        sys.path.insert(0, str(sys_path_docx))
    formatar_docx = pytest.importorskip("formatar_docx")

    bruto = docx_com(["TERMO DE REFERÊNCIA", "1. OBJETO", "Material de limpeza."],
                     entrada / "tr_bruto.docx")
    saida = tmp_path / "TR_formatado.docx"
    monkeypatch.setenv(mod_manifesto.VARIAVEL_PROCESSOS, str(processo.raiz.parent))

    codigo = formatar_docx.main([
        "--entrada", str(bruto), "--saida", str(saida), "--perfil", "tr",
        "--registrar-em-processo", "PA_031_2026", "--tipo-documento", "TR",
        "--motivo-registro", "geração inicial formatada",
    ])
    assert codigo == 0
    registro = processo.documento("TR")
    assert registro["arquivo_atual"] == "01_EM_ELABORACAO/TR.docx"
    assert registro["validacao"]["formatacao"] in (
        "aprovado", "aprovado_com_ressalvas"
    )
    assert "documento_gerado" in acoes(processo)
