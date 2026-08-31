# -*- coding: utf-8 -*-
"""Teste: busca no TCLEGIS (Post /Home/RetornoBusca) com token antiforgery."""
import io, re, sys, urllib.parse, urllib.request, http.cookiejar
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://tclegis.tce.mg.gov.br"
UA = "TCE-MG-contratacoes-diretas/0.1 (pesquisa publica)"

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
H = {"User-Agent": UA,
     "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}

# 1) GET pagina de busca do TCEMG
r = op.open(urllib.request.Request(f"{BASE}/Home/Index/TCE", headers=H), timeout=60)
html = r.read().decode("utf-8", "replace")
tok = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', html)
print("token achado:", bool(tok))
tok = tok.group(1) if tok else ""

def busca(termos, tipo_norma="", situacao=""):
    """tipo_norma e situacao podem ser vazios (todas)."""
    data = {
        "__RequestVerificationToken": tok,
        "tipoConsulta": "TCE",
        "numNorma": "",
        "numAno": "",
        "dataInicio": "",
        "dataFim": "",
        "tipoNorma": tipo_norma,
        "tipoOrigem": "",
        "indRevogada": situacao,
        "qtdPorPagina": "100",
        "orderby": "",
        "page": "1",
        "Assuntos": termos,
        "testEmenta": "true",
        "testIndexacao": "true",
        "testIntegra": "true",
        "testObservacao": "true",
        "testFonte": "true",
        "testVide": "true",
    }
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(f"{BASE}/Home/RetornoBusca", data=body,
                                 headers={**H, "Content-Type": "application/x-www-form-urlencoded",
                                          "Referer": f"{BASE}/Home/Index/TCE"})
    r = op.open(req, timeout=90)
    raw = r.read()
    try:
        txt = raw.decode("utf-8", "replace")
    except Exception:
        txt = raw.decode("latin-1", "replace")
    print(f"== busca '{termos}' -> status {r.status}, len {len(txt)}")
    import os
    fn = os.path.join(r"G:\Outros computadores\Meu computador (1)\Charles\tce-mg-contratacoes-diretas\00_CONTROLE",
                      "_tmp_tclegis_resultado.html")
    io.open(fn, "w", encoding="utf-8").write(txt)
    # resultados: links Detalhe
    ids = re.findall(r"Detalhe/(\d+)", txt)
    print("   ids Detalhe:", sorted(set(ids))[:30])
    # trechos de titulos
    tit = re.findall(r'<td[^>]*>\s*([A-ZÀ-ſ0-9][^<]{10,150}?)\s*</td>', txt)
    print("   títulos:", tit[:15])
    return txt

# assuntos de interesse
for termos in ["inexigibilidade", "licitação", "contratação direta"]:
    try:
        busca(termos)
    except Exception as e:
        print("   ERRO:", e)