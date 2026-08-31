from __future__ import annotations

import json
from pathlib import Path

import contratacoes_similares as cs
import pncp_consulta


DEMANDA = {
    "objeto": "Aquisição de forno de micro-ondas para a copa da Câmara",
    "palavras_chave": ["forno de micro-ondas", "micro-ondas copa"],
    "sinonimos": ["micro-ondas"],
    "filtros": {"uf": "MG"},
    "processo_nome": "micro-ondas-copa",
}


# 1. objeto simples -> palavras-chave nucleares deduplicadas, objeto primeiro
def test_gerar_palavras_chave_objeto_primeiro_e_dedup() -> None:
    palavras = cs.gerar_palavras_chave(
        {"objeto": "Micro-ondas", "palavras_chave": ["micro-ondas", "MICRO-ONDAS"], "sinonimos": ["forno"]}
    )
    assert palavras[0] == "Micro-ondas"
    assert palavras.count("micro-ondas") == 0 or [p.lower() for p in palavras].count("micro-ondas") == 1
    assert "forno" in palavras


# 2. score de termos e relevância sugerida
def test_score_e_relevancia_sugerida() -> None:
    alto = cs._score_termos("forno micro-ondas copa", "aquisição de forno de micro-ondas para copa")
    zero = cs._score_termos("forno micro-ondas", "aquisição de cadeiras de escritório")
    assert alto > zero
    assert "sem link" in cs._relevancia_sugerida(0.9, tem_link=False)


# 3./8. deduplicação por número de controle e por link
def test_deduplicar_por_numero_e_link() -> None:
    refs = [
        {"numero_contratacao": "X1", "link": "http://a"},
        {"numero_contratacao": "X1", "link": "http://b"},
        {"numero_contratacao": "", "link": "http://c"},
        {"numero_contratacao": "", "link": "http://c"},
    ]
    saida = cs.deduplicar(refs)
    assert len(saida) == 2


# 4. modalidade diferente NÃO exclui: registrada como metadado
def test_modalidade_e_metadado_nao_filtra() -> None:
    item = {"objeto_encontrado": "forno micro-ondas", "modalidade": "Pregão Eletrônico", "link": "http://x"}
    ref = cs.normalizar_pncp(item, DEMANDA["objeto"], "2026-07-23")
    assert ref["modalidade"] == "Pregão Eletrônico"
    assert ref["origem"] == "PNCP"


# 5./6. PNCP indisponível e web sem chave não quebram; evidência nunca "confirmada" sozinha
def test_pesquisar_sem_rede_gera_relatorio(monkeypatch) -> None:
    monkeypatch.setattr(cs, "consultar_pncp_multi", None)
    pacote = cs.pesquisar(DEMANDA, usar_pncp=True, usar_web=False)
    assert "pncp_consulta indisponível." in pacote["erros"]
    assert "Relatório de Pesquisa de Contratações Similares" in pacote["relatorio"]
    assert "NÃO pesquisa formal de preços" in pacote["relatorio"]


# 7. documento inacessível: item sem link não entra na fila de leitura
def test_fila_leitura_ignora_sem_link() -> None:
    refs = [{"link": "http://a", "orgao": "O", "objeto_encontrado": "x", "documentos_lidos": []},
            {"link": "", "orgao": "O2", "objeto_encontrado": "y"}]
    fila = cs.montar_fila_leitura(refs)
    assert len(fila) == 1
    assert fila[0]["link"] == "http://a"


# 10. referência boa com modalidade diferente entra e é ordenada pelo score
def test_pesquisar_com_manual_ordena_por_score() -> None:
    manual = [
        {"orgao": "Câmara A", "objeto_encontrado": "cadeira de escritório", "link": "http://a",
         "modalidade": "Dispensa"},
        {"orgao": "Câmara B", "objeto_encontrado": "forno de micro-ondas para copa", "link": "http://b",
         "modalidade": "Pregão"},
    ]
    pacote = cs.pesquisar(DEMANDA, usar_pncp=False, usar_web=False, manual=manual)
    refs = pacote["referencias"]
    assert refs[0]["orgao"] == "Câmara B"  # maior sobreposição de termos
    assert all(r["origem"] == "Manual" for r in refs)


# 9. resultado duplicado entre manual e PNCP some na dedup (mesmo número)
def test_dedup_entre_origens() -> None:
    manual = [{"numero_contratacao": "N1", "orgao": "A", "objeto_encontrado": "forno", "link": "http://a"}]

    def fake_multi(*a, **k):
        return {"data_consulta": "2026-07-23", "termos_pesquisados": ["forno"],
                "itens": [{"numero_contratacao": "N1", "objeto_encontrado": "forno", "link": "http://a"}]}

    import contratacoes_similares
    orig = contratacoes_similares.consultar_pncp_multi
    contratacoes_similares.consultar_pncp_multi = fake_multi
    try:
        pacote = cs.pesquisar(DEMANDA, usar_pncp=True, usar_web=False, manual=manual)
    finally:
        contratacoes_similares.consultar_pncp_multi = orig
    assert len(pacote["referencias"]) == 1


# 11./12. estrutura de saída é criada e preserva links/datas
def test_escrever_saida_dir(tmp_path: Path) -> None:
    pacote = cs.pesquisar(DEMANDA, usar_pncp=False, usar_web=False,
                          manual=[{"orgao": "A", "objeto_encontrado": "forno", "link": "http://a"}])
    raiz = cs.escrever_saida_dir(tmp_path / "micro-ondas-copa", DEMANDA, pacote["referencias"],
                                 pacote["fila_leitura"], pacote["relatorio"], None, None, None)
    assert (raiz / "01_ficha_demanda.md").exists()
    assert (raiz / "07_relatorio" / "relatorio_contratacoes_similares.md").exists()
    assert (raiz / "08_aplicacao_itanhandu").is_dir()
    refs = json.loads((raiz / "03_resultados_brutos" / "referencias.json").read_text(encoding="utf-8"))
    assert refs[0]["link"] == "http://a"


# pncp_consulta.consultar_pncp_multi: dedup e termo_origem, sem rede
def test_consultar_pncp_multi_dedup(monkeypatch) -> None:
    chamadas = {"n": 0}

    def fake_consultar_pncp(objeto, **kwargs):
        chamadas["n"] += 1
        return {"itens": [{"numero_contratacao": "C1", "objeto_encontrado": "forno", "link": "http://c1"}],
                "modo": "teste", "url_consultada": "u", "total": 1, "erro": None}

    monkeypatch.setattr(pncp_consulta, "consultar_pncp", fake_consultar_pncp)
    res = pncp_consulta.consultar_pncp_multi(["forno", "micro-ondas"], max_por_termo=5, max_total=10)
    assert res["total_dedup"] == 1  # mesmo número em dois termos -> 1
    assert res["itens"][0]["termo_origem"] == "forno"
    assert chamadas["n"] == 2
