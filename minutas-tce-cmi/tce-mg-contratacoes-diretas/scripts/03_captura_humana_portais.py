# -*- coding: utf-8 -*-
"""03_captura_humana_portais.py — Roteiro registrado de captura humana (Fase 2).

O Compras MG continua protegido por hCaptcha. O Portal da Transparência pode
ser consultado em navegador, mas sua API direta responde HTTP 401 sem a sessão.
Este script NÃO acessa os portais: ele organiza e proveniencia o que uma pessoa
capturar manualmente, deixando o percurso documentado e verificável.

Fluxo previsto:
  1. A pessoa acessa o portal no navegador, resolve o CAPTCHA, navega até o
     processo/sequência e salva a tela (PDF "imprimir como", HTML, screenshots).
  2. Os arquivos vão para tmp/entrada_captura_humana/ (ou o caminho dado).
  3. Rode: python scripts/03_captura_humana_portais.py
     -> copia para 99_ORIGINAIS/ + registra SHA-256 em
        registros_web/humana/ + registro de proveniência em
        00_CONTROLE/captura_humana/registo.json (o caminho percorrido é o que a
        pessoa preenche, nunca inventado por este script).

Uso:
    python scripts/03_captura_humana_portais.py --entrada tmp/entrada_captura_humana
    python scripts/03_captura_humana_portais.py --modelo   # gera registro vazio

Este script nunca afirma ter acessado o portal — ele registra o que foi anexado.
"""
import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import caminho, json_dump, le_config, sha256_bytes  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada",
                    default="tmp/entrada_captura_humana",
                    help="pasta com arquivos capturados manualmente")
    ap.add_argument("--modelo", action="store_true",
                    help="grava um registo.json de modelo para preenchimento humano")
    args = ap.parse_args()

    cfg = le_config()
    if args.modelo:
        modelo = {
            "sessao": "2026-08-09_exemplo",
            "portal": "nome_do_portal",  # Transparencia TCE-MG | Compras MG 1020
            "capturado_por": "NO ME DA PESSOA",
            "data_hora": "AAAA-MM-DD HH:MM",
            "caminho_percorrido": [
                "1. Abrir URL X no navegador",
                "2. Se o portal apresentar CAPTCHA, resolver somente por ação humana",
                "3. Filtrar por <o que foi filtrado>",
                "4. Abrir processo <N/NNNN> e salvar a tela",
            ],
            "observacoes": "",
        }
        json_dump(caminho("00_CONTROLE/captura_humana/registo_modelo.json"), modelo)
        print("Modelo gravado em 00_CONTROLE/captura_humana/registo_modelo.json")
        return

    entrada = args.entrada
    if not os.path.isdir(entrada):
        sys.exit(f"Pasta de entrada não encontrada: {entrada} — capture os arquivos "
                 f"no navegador e coloque-os lá antes de rodar (ver docstring).")

    arquivos = sorted(f for f in os.listdir(entrada)
                      if os.path.isfile(os.path.join(entrada, f)))
    if not arquivos:
        sys.exit(f"Pasta {entrada} vazia — nada para registrar.")

    dest_originais = caminho(cfg["diretorios"]["originais"])
    dest_registros = caminho(cfg["diretorios"]["registros_web"], "humana")
    os.makedirs(dest_originais, exist_ok=True)
    os.makedirs(dest_registros, exist_ok=True)

    registrados = []
    for nome in arquivos:
        origem = os.path.join(entrada, nome)
        # cópia no original (nunca move — o original do usuário permanece)
        destino_orig = os.path.join(dest_originais, nome)
        if not os.path.exists(destino_orig):
            shutil.copy2(origem, destino_orig)
        with open(destino_orig, "rb") as f:
            b = f.read()
        sha = sha256_bytes(b)
        destino_reg = os.path.join(dest_registros, nome)
        if not os.path.exists(destino_reg):
            shutil.copy2(destino_orig, destino_reg)
        registrados.append({
            "arquivo_entrada": origem,
            "arquivo_original": destino_orig,
            "arquivo_registro": destino_reg,
            "sha256": sha,
            "bytes": len(b),
            "data_captura_registro": datetime.now(timezone.utc).isoformat(),
        })
        print(f"[ok] {nome} · {sha[:16]}… · {len(b)} bytes")

    registo = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "classificacao": "captura humana — preencha o caminho percorrido no registo.json",
        "portais_status": {
            "transparencia_tce_mg": cfg["fontes"]["transparencia_tce_mg"]["status"],
            "compras_mg": cfg["fontes"]["compras_mg"]["status"],
        },
        "arquivos": registrados,
        "caminho_percorrido": "PREENCHER PELA PESSOA (ver 00_CONTROLE/captura_humana/registo)",
    }
    json_dump(caminho("00_CONTROLE/captura_humana/registo.json"), registo)
    print(f"[fim] {len(registrados)} arquivos registrados. Preencha o caminho "
          f"percorrido em 00_CONTROLE/captura_humana/registo.json")


if __name__ == "__main__":
    main()
