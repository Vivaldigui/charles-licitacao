# -*- coding: utf-8 -*-
"""utils — ajuda compartilhada dos scripts de coleta da base.

Ferramentas comuns: requisição educada com retry/backoff, SHA-256, carregamento
da config.yaml, escrita de evidência bruta canonizada (registros_web + manifesto).
O módulo é parte da base; a leitura do YAML usa a dependência PyYAML declarada
em ``requirements.txt``.
"""
import hashlib
import http.cookiejar
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import yaml  # PyYAML (única dependência opcional; config.yaml é fácil de ler à mão)

_UTILS_DIR = os.path.dirname(os.path.abspath(__file__))   # scripts/utils/
SCRIPTS_DIR = os.path.dirname(_UTILS_DIR)                 # scripts/
ROOT = os.path.dirname(SCRIPTS_DIR)                       # raiz da base
CONFIG_PATH = os.path.join(SCRIPTS_DIR, "config.yaml")    # scripts/config.yaml

_CACHE_CONFIG = None

# Sessão HTTP compartilhada: cookies (ex.: ASP.NET_SessionId + antiforgery)
# precisam ser reutilizados entre GET (Index) e POST (RetornoBusca).
_COOKIE_JAR = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(_COOKIE_JAR))


def caminho(*partes):
    return os.path.join(ROOT, *partes)


def le_config():
    """Carrega scripts/config.yaml (cacheado)."""
    global _CACHE_CONFIG
    if _CACHE_CONFIG is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _CACHE_CONFIG = yaml.safe_load(f)
    return _CACHE_CONFIG


def pausa_educada():
    c = le_config()["coleta"]
    time.sleep(float(c["pausa_segundos"]))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url, data=None, headers=None, retries=None, timeout=None):
    """GET/POST simples com retry/backoff exponencial e UA identificável.

    Retorna (status, dict_headers, raw_bytes). Levanta a última exceção se
    todas as tentativas falharem — o chamador decide como registrar.
    """
    c = le_config()["coleta"]
    retries = int(retries if retries is not None else c["retries"])
    timeout = int(timeout if timeout is not None else c["timeout"])
    h = {"User-Agent": c["user_agent"]}
    if headers:
        h.update(headers)
    last = None
    for i in range(retries):
        try:
            if data is None:
                req = urllib.request.Request(url, headers=h)
            else:
                req = urllib.request.Request(url, data=data, headers=h)
            with _OPENER.open(req, timeout=timeout) as r:
                raw = r.read()
                return r.status, dict(r.getheaders()), raw
        except Exception as e:
            last = e
            wait = 1.5 * (2 ** i)
            print(f"    [retry {i+1}/{retries}] {e} ... dorme {wait:.1f}s")
            time.sleep(min(wait, 8))
    raise last


def token_antiforgery(html: str) -> str:
    """Extrai __RequestVerificationToken de uma página ASP.NET MVC (TCLEGIS)."""
    m = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else ""


def grava_evidencia_web(subpasta, nome_arquivo, conteudo_bytes, tag, fonte_url,
                        conteudo_txt=None):
    """Canoniza captura bruta em registros_web/<subpasta>/ e atualiza o manifesto.

    Idempotente: se o arquivo já existe com o mesmo SHA-256, não regrava nem duplica
    entrada no manifesto. Usado pelos coletores para deixar evidência verificável.
    """
    cfg = le_config()
    dir_dest = caminho(cfg["diretorios"]["registros_web"], subpasta)
    os.makedirs(dir_dest, exist_ok=True)
    destino = os.path.join(dir_dest, nome_arquivo)
    sha = sha256_bytes(conteudo_bytes)

    manifesto_path = caminho(cfg["diretorios"]["registros_web"], "MANIFESTO_EVIDENCIAS.json")
    manifesto = {}
    if os.path.exists(manifesto_path):
        with open(manifesto_path, "r", encoding="utf-8") as f:
            manifesto = json.load(f)

    chave_manifesto = os.path.relpath(
        destino, caminho(cfg["diretorios"]["registros_web"])
    ).replace("\\", "/")
    entrada_existente = manifesto.get(chave_manifesto)
    if entrada_existente and entrada_existente.get("sha256") == sha:
        return {"ja_existia": True, "sha256": sha, "caminho": destino}

    with open(destino, "wb") as f:
        f.write(conteudo_bytes)
    manifesto[chave_manifesto] = {
        "arquivo": chave_manifesto,
        "sha256": sha,
        "bytes": len(conteudo_bytes),
        "fonte_url": fonte_url,
        "tag": tag,
        "data_hora": datetime.now(timezone.utc).isoformat(),
    }
    with open(manifesto_path, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)
    return {"ja_existia": False, "sha256": sha, "caminho": destino}


def json_dump(caminho_arquivo, obj):
    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return caminho_arquivo


def slug(texto: str, maxlen: int = 48) -> str:
    """Slug simples para nome de arquivo de evidência."""
    t = re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")
    return t[:maxlen] or "resultado"
