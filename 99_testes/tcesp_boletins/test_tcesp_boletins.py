from __future__ import annotations

from scripts import tcesp_boletins as mod


def test_normalizar_remove_acentos_e_espacos() -> None:
    assert mod.normalizar("  DISPENSA   de Licitação  ") == "dispensa de licitacao"
    assert mod.normalizar("DISPENSA DE LICITA ÇÃO") == "dispensa de licitacao"


def test_cabecalho_quebrado_preserva_inicio_e_nao_duplica() -> None:
    pagina = """SEGUNDA CÂMARA
➢ Processos n.º TC-012854.989.16-7, TC-015268.989.16-7, TC-
015513.989.16-0 e TC-006558.989.17-4
(Sessão de 15/06/2021, relatoria: Conselheiro Dimas Ramalho)

EMENTA: REPRESENTAÇÃO. DISPENSA DE LICITAÇÃO. CONTRATO.
"""
    cabecalhos = mod.cabecalhos_processos([pagina])
    assert cabecalhos == [(0, pagina.index("➢ Processos"))]
    bloco, paginas = mod.recortar_bloco([pagina], cabecalhos[0], None)
    dados = mod.extrair_metadados(bloco, pagina[: cabecalhos[0][1]])
    assert dados["processos"] == [
        "TC-012854.989.16-7",
        "TC-015268.989.16-7",
        "TC-015513.989.16-0",
        "TC-006558.989.17-4",
    ]
    assert paginas == [1]


def test_termos_relevantes_rejeitam_dispensa_incidental() -> None:
    falso = "A escrituração digital dispensa, de fato, a elaboração de outro balanço."
    verdadeiro = "EMENTA: DISPENSA DE LICITAÇÃO. SITUAÇÃO EMERGENCIAL."
    assert mod.termos_relevantes(falso) == []
    assert "dispensa de licitacao" in mod.termos_relevantes(verdadeiro)


def test_metadados_e_regime() -> None:
    bloco = """025086.989.24-1 e outro
(Sessão Plenária de 11/02/2026. Relatoria: Conselheiro Marco Aurélio Bertaiolli)

EMENTA: RECURSOS ORDINÁRIOS. DISPENSA DE LICITAÇÃO.

Nota CPAJ: aplicação do art. 24, IV, da Lei nº 8.666/93.
"""
    dados = mod.extrair_metadados(bloco, "")
    assert dados["processos"] == ["TC-025086.989.24-1"]
    assert dados["data_sessao"] == "2026-02-11"
    assert dados["orgao_julgador"] == "TRIBUNAL PLENO"
    assert dados["relator"] == "Conselheiro Marco Aurélio Bertaiolli"
    assert mod.detectar_regime(bloco) == "lei-8666"
    assert "dispensa por valor" not in mod.detectar_temas(bloco)
    assert "dispensa por valor" in mod.detectar_temas("Dispensa com base no art. 24, II, da Lei 8.666/93")


def test_orgao_julgador_vem_do_contexto() -> None:
    bloco = """011307.989.23-6 e outros
(Sessão de 10/02/2026. Relatoria: Conselheiro Renato Martins Costa)

EMENTA: DISPENSA DE LICITAÇÃO.
"""
    dados = mod.extrair_metadados(bloco, "SEGUNDA CÂMARA\n")
    assert dados["orgao_julgador"] == "SEGUNDA CÂMARA"


def test_formato_antigo_de_processo_cria_novo_cabecalho() -> None:
    pagina = """➢ Processo nº TC-007058/026/14
(Sessão Plenária de 24/02/2021, relatoria: Conselheiro Renato Martins Costa)

EMENTA: DISPENSA DE LICITAÇÃO. CONTRATO.
"""
    cabecalhos = mod.cabecalhos_processos([pagina])
    assert cabecalhos == [(0, 0)]
    dados = mod.extrair_metadados(pagina, "")
    assert dados["processos"] == ["TC-007058/026/14"]


def test_formatos_sem_prefixo_ou_sem_digito_final() -> None:
    pagina = """035734/026/14
(Sessão Plenária de 09/11/2022. Relatoria: Conselheiro Renato Martins Costa)

EMENTA: DISPENSAS DE LICITAÇÃO.

007649.989.22
(Sessão de 05/12/2023. Relatoria: Conselheiro Renato Martins Costa)

EMENTA: CONTRATAÇÕES DIRETAS.
"""
    cabecalhos = mod.cabecalhos_processos([pagina])
    assert len(cabecalhos) == 2
    primeiro, _ = mod.recortar_bloco([pagina], cabecalhos[0], cabecalhos[1])
    segundo, _ = mod.recortar_bloco([pagina], cabecalhos[1], None)
    assert mod.extrair_metadados(primeiro, "")["processos"] == ["TC-035734/026/14"]
    assert mod.extrair_metadados(segundo, "")["processos"] == ["TC-007649.989.22"]
