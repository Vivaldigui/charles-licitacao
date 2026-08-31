# -*- coding: utf-8 -*-
"""Fase 1 - Testar mecanica de busca do Compras MG (orgao 1020)."""
import http.cookiejar, urllib.request, urllib.parse, io, re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

BASE = "https://www1.compras.mg.gov.br/processocompra/processo/consultaProcessoCompra.html"

# garante sessao
r = opener.open(urllib.request.Request(BASE + "?orgaoEntidade=1020", headers=H), timeout=60)
r.read()

params_def = dict(
    idProcessoCompraSelecionado="", procedimentoProcessoSelecionado="", unidadeCompra="",
    possuiPregao="", possuiEdital="", estaPesquisando="true", metodo="pesquisar",
    textoConfirmacao="", orgaoEntidade="1020", codigoUnidadeCompra="", numero="", ano="",
    situacao="", procedimentoModificado="", procedimento1="", procedimento2="",
    procedimento3="", procedimento4="", especializacao="", dataCriacaoDe="",
    dataCriacaoAte="", dataLicitacaoDe="", dataLicitacaoAte="", linhaFornecimento="",
    linhaFornecimentoOpcaoEOu="E", linhaFornecimentoOpcaoSem="", descricaoMaterialOuServico="",
    descricaoMaterialOuServicoOpcaoEOu="E", descricaoMaterialOuServicoOpcaoSem="",
    especificacaoItemMaterialOuServico="", especificacaoItemMaterialOuServicoOpcaoEOu="E",
    especificacaoItemMaterialOuServicoOpcaoSem="",
)

# 1) GET com todos os parametros
q = urllib.parse.urlencode(params_def)
r = opener.open(urllib.request.Request(BASE + "?" + q, headers=H), timeout=60)
body = r.read().decode("latin-1", "replace")
def tem_resultado(b):
    return ("quantidadeItems_tabConsultaProcessoCompra" in b
            and "IDDOPROCESSO" in b and ("radio" in b.lower() or "atencao" not in ""))
# identificar inputs radio de processo
radios = re.findall(r'<input[^>]*(?:radio|checkbox)[^>]*>', body)
print("GET completo: len", len(body), "| radios:", len(radios))
if radios:
    for rr in radios[:6]:
        print("   ", rr[:160])

# 2) POST (mesmo form, method get declarado, mas abaixo tentamos post com body)
try:
    data = urllib.parse.urlencode(params_def).encode("latin-1")
    req = urllib.request.Request(BASE, data=data, headers=dict(H, **{"Content-Type": "application/x-www-form-urlencoded"}), method="POST")
    r = opener.open(req, timeout=60)
    body = r.read().decode("latin-1", "replace")
    radios = re.findall(r'<input[^>]*(?:radio|checkbox)[^>]*>', body)
    print("POST: len", len(body), "| radios:", len(radios), "| url final", r.geturl())
    if radios:
        for rr in radios[:6]:
            print("   ", rr[:160])
except Exception as e:
    print("POST ERRO:", e)

# 3) procurando label do 1020 no html original
orig = io.open(r"G:\Outros computadores\Meu computador (1)\Charles\tce-mg-contratacoes-diretas\00_CONTROLE\_tmp_comprasmg_consulta.html", encoding="latin-1", errors="replace").read()
m = re.search(r'<option[^>]*value="1020"[^>]*>([^<]*)</option>', orig)
print("label 1020:", m.group(1) if m else "NAO ENCONTRADO")