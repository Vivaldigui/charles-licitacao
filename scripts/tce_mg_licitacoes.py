#!/usr/bin/env python3
"""Coleta de contratações do TCE-MG no Portal da Transparência (SIAD / Admin TCEMG).

Fonte: https://transparencia.tce.mg.gov.br/public/licitacoes

O portal é um front Angular que fala com um proxy autenticado por captcha. O
token do captcha fica em `localStorage['tokenAuthorizationProxy']` e vale ~2h.
Este script NÃO resolve captcha: recebe o token já obtido pelo navegador
(`--token-file`) e apenas repete as mesmas chamadas que a página faz.

Subcomandos
-----------
listar   consulta a API e grava o manifesto JSON/CSV das contratações
baixar   baixa a "DOC Interna/Externa" (autos digitalizados) e os anexos
extrair  extrai o texto dos PDFs baixados (requer pypdf)

Nada aqui interpreta juridicamente o conteúdo: o script coleta, nomeia e
registra a evidência (URL, data/hora de acesso, tamanho, sha256).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

API = (
    "https://arabiasaudita.tce.mg.gov.br:8443/TCEMG-proxy-web/"
    "publico/apimoci/p-portal-transparencia/"
)
PORTAL = "https://transparencia.tce.mg.gov.br/public/licitacoes"

# Indicadores usados pelo portal para montar a URL do arquivo protocolado.
# Confirmados em api/Indicador/Sigla/{CODI,ANX} — ver README do módulo.
ID_CATEGORIA_COMPRA_DIRETA = 28  # CODI
ID_TIPO_ARQUIVO_ANEXO = 30  # ANX

# Mapa modalidade -> sigla do protocolo, igual ao obterSiglaTipoArquivo() do front.
SIGLAS = {
    "Pregão": "PRE",
    "Inexigibilidade": "INX",
    "Dispensa de Licitação": "DSP",
}

FONTES = {
    # fonte -> {rótulo da modalidade: valor aceito pelo parâmetro `modalidade`}
    "SIAD": {
        "Dispensa de Licitação": "Dispensa de Licitação",
        "Pregão": "Pregão",
        "Inexigibilidade": "Inexigibilidade",
        "Compra direta": "Compra direta",
        "Cotação eletrônica": "Cotação eletrônica",
    },
    "Admin": {
        "Dispensa de Licitação": "10",
        "Pregão": "1",
        "Inexigibilidade": "9",
        "Concorrência": "7",
    },
}

USER_AGENT = "Charles/CMI (coleta de referencias publicas; contato: Camara Municipal de Itanhandu)"


def agora() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class Cliente:
    token: str
    pausa: float = 0.6
    contexto: ssl.SSLContext = field(default_factory=ssl.create_default_context)

    def _abrir(self, url: str, headers: dict[str, str], timeout: int = 180):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers})
        return urllib.request.urlopen(req, timeout=timeout, context=self.contexto)

    def _headers_api(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {"AuthorizationProxy": f"token {self.token}"}
        if extra:
            h.update(extra)
        return h

    def listar(
        self, fonte: str, lei: str, modalidade: str | None, page_size: int = 500
    ) -> tuple[list[dict], dict]:
        params = {"idFontePesquisa": fonte, "idLei": lei}
        if modalidade:
            params["modalidade"] = modalidade
        url = (
            f"{API}api/CompraLicitacao/GetAllCompraLicitacao/{fonte}/{lei}?"
            + urllib.parse.urlencode(params)
        )
        paginacao = {"page": 1, "pageSize": page_size, "order": "objeto", "sortOrder": "ASC"}
        with self._abrir(
            url, self._headers_api({"Pagination": json.dumps(paginacao)})
        ) as r:
            corpo = json.loads(r.read().decode("utf-8"))
            meta = json.loads(r.headers.get("Pagination") or "{}")
        time.sleep(self.pausa)
        return corpo or [], meta

    @staticmethod
    def protocolo(ano: int, numero: int, sigla: str) -> str:
        """MM(2) + AAAA(4) + ID(10) + SIGLA(3) — montarProtocolo() do front."""
        mes = "00"  # o front chama com `mes` indefinido
        return f"{mes}{int(ano):04d}{int(numero):010d}{(sigla.strip() + '000')[:3]}"

    def baixar_doc(self, protocolo: str, destino: Path) -> dict:
        url = (
            f"{API}api/Arquivo/Protocolo/{protocolo}"
            f"?IdCategoria={ID_CATEGORIA_COMPRA_DIRETA}"
            f"&IdTipoArquivo={ID_TIPO_ARQUIVO_ANEXO}"
        )
        return self._baixar(url, destino, self._headers_api())

    def baixar_publico(self, url: str, destino: Path) -> dict:
        # Nomes de anexo vêm com acento ("Publicações_1_1113_2024.pdf"); a URL precisa
        # ser percent-encoded ou o urllib estoura em ascii.
        partes = urllib.parse.urlsplit(url)
        url = urllib.parse.urlunsplit(
            partes._replace(path=urllib.parse.quote(partes.path, safe="/%"))
        )
        return self._baixar(url, destino, {})

    def _baixar(self, url: str, destino: Path, headers: dict[str, str]) -> dict:
        registro = {"url": url, "acessado_em": agora(), "arquivo": str(destino)}
        try:
            with self._abrir(url, headers) as r:
                dados = r.read()
                registro["status"] = r.status
                registro["content_type"] = r.headers.get("content-type")
        except urllib.error.HTTPError as exc:
            registro["status"] = exc.code
            registro["erro"] = f"HTTP {exc.code}"
            return registro
        except Exception as exc:  # rede, TLS, timeout
            registro["status"] = None
            registro["erro"] = f"{type(exc).__name__}: {exc}"
            return registro
        finally:
            time.sleep(self.pausa)

        if not dados:
            registro["erro"] = "resposta vazia"
            return registro
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(dados)
        registro["bytes"] = len(dados)
        registro["sha256"] = hashlib.sha256(dados).hexdigest()
        registro["pdf"] = dados[:5] == b"%PDF-"
        return registro


def slug(texto: str, limite: int = 60) -> str:
    import re
    import unicodedata

    texto = unicodedata.normalize("NFKD", texto or "")
    texto = texto.encode("ascii", "ignore").decode("ascii").lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto).strip("-")
    return texto[:limite].strip("-") or "sem-objeto"


def nome_base(registro: dict) -> str:
    return (
        f"{registro['anoLicitacao']}-{int(registro['numeroLicitacao']):04d}"
        f"_{slug(registro.get('objeto') or '')}"
    )


# --------------------------------------------------------------------------- #
# Subcomandos
# --------------------------------------------------------------------------- #
def cmd_listar(args) -> int:
    cli = Cliente(token=Path(args.token_file).read_text(encoding="utf-8").strip())
    manifesto = {
        "fonte_portal": PORTAL,
        "endpoint": API + "api/CompraLicitacao/GetAllCompraLicitacao/{fonte}/{lei}",
        "coletado_em": agora(),
        "lei": args.lei,
        "consultas": [],
        "registros": [],
    }
    for fonte in args.fontes:
        for rotulo in args.modalidades:
            valor = FONTES.get(fonte, {}).get(rotulo)
            if valor is None:
                print(f"  ! {fonte}/{rotulo}: modalidade não existe nessa fonte", file=sys.stderr)
                continue
            registros, meta = cli.listar(fonte, args.lei, valor)
            print(f"  {fonte}/{rotulo}: {len(registros)} registro(s)")
            manifesto["consultas"].append(
                {
                    "fonte": fonte,
                    "modalidade": rotulo,
                    "modalidade_param": valor,
                    "total_informado": meta.get("totalItems"),
                    "total_recebido": len(registros),
                }
            )
            for reg in registros:
                reg["_fonte"] = fonte
                reg["_modalidade_filtro"] = rotulo
                reg["_sigla_protocolo"] = SIGLAS.get(rotulo, "")
                reg["_nome_base"] = nome_base(reg)
                manifesto["registros"].append(reg)

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "MANIFESTO.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    colunas = [
        "_fonte",
        "_modalidade_filtro",
        "numeroLicitacao",
        "anoLicitacao",
        "nomeTipoLicitacao",
        "objeto",
        "situacao",
        "vlrReferencia",
        "vlrHomologado",
        "nomFornecedor",
        "numContrato",
        "dataSessao",
        "urlRaiz",
    ]
    with (saida / "MANIFESTO.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=colunas, extrasaction="ignore")
        w.writeheader()
        for reg in manifesto["registros"]:
            w.writerow(reg)
    print(f"\n{len(manifesto['registros'])} registro(s) -> {saida / 'MANIFESTO.json'}")
    return 0


def cmd_baixar(args) -> int:
    cli = Cliente(token=Path(args.token_file).read_text(encoding="utf-8").strip())
    saida = Path(args.saida)
    manifesto = json.loads((saida / "MANIFESTO.json").read_text(encoding="utf-8"))
    evidencias: list[dict] = []

    for reg in manifesto["registros"]:
        fonte = reg["_fonte"]
        modalidade = reg["_modalidade_filtro"]
        pasta = saida / slug(fonte) / slug(modalidade) / reg["_nome_base"]
        sigla = reg.get("_sigla_protocolo") or ""

        # 1) DOC Interna/Externa (autos digitalizados) — só existe via protocolo.
        if sigla:
            proto = Cliente.protocolo(reg["anoLicitacao"], reg["numeroLicitacao"], sigla)
            alvo = pasta / f"DOC_INTERNA_EXTERNA_{proto}.pdf"
            if alvo.exists() and not args.forcar:
                print(f"  = {alvo.relative_to(saida)}")
            else:
                ev = cli.baixar_doc(proto, alvo)
                ev.update({"registro": reg["_nome_base"], "tipo": "DOC_INTERNA_EXTERNA",
                           "fonte": fonte, "modalidade": modalidade, "protocolo": proto})
                evidencias.append(ev)
                marca = "ok" if ev.get("bytes") else "falhou"
                print(f"  {marca:>6} {alvo.relative_to(saida)} "
                      f"({ev.get('bytes', 0) / 1e6:.1f} MB, HTTP {ev.get('status')})")

        # 2) Anexos publicados (editais e afins) — URL pública, sem token.
        for anexo in reg.get("anexos") or []:
            raiz = (reg.get("urlRaiz") or "").strip()
            nome = (anexo.get("nomeAnexo") or "").strip()
            if not raiz or not nome:
                continue
            alvo = pasta / "anexos" / nome
            if alvo.exists() and not args.forcar:
                print(f"  = {alvo.relative_to(saida)}")
                continue
            ev = cli.baixar_publico(raiz + nome, alvo)
            ev.update({"registro": reg["_nome_base"], "tipo": anexo.get("nomeTipoAnexo") or "ANEXO",
                       "fonte": fonte, "modalidade": modalidade})
            evidencias.append(ev)
            marca = "ok" if ev.get("bytes") else "falhou"
            print(f"  {marca:>6} {alvo.relative_to(saida)} "
                  f"({ev.get('bytes', 0) / 1e6:.1f} MB, HTTP {ev.get('status')})")

    caminho = saida / "EVIDENCIAS_DOWNLOAD.json"
    anteriores = []
    if caminho.exists():
        anteriores = json.loads(caminho.read_text(encoding="utf-8"))
    caminho.write_text(
        json.dumps(anteriores + evidencias, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ok = sum(1 for e in evidencias if e.get("bytes"))
    print(f"\n{ok}/{len(evidencias)} download(s) com conteúdo -> {caminho}")
    return 0


def cmd_extrair(args) -> int:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("pypdf não instalado: pip install -r requirements-auditor.txt", file=sys.stderr)
        return 1

    saida = Path(args.saida)
    relatorio = []
    for pdf in sorted(saida.rglob("*.pdf")):
        destino = pdf.parent / "texto_extraido" / (pdf.stem + ".txt")
        if destino.exists() and not args.forcar:
            continue
        try:
            leitor = PdfReader(str(pdf))
            paginas = [(p.extract_text() or "") for p in leitor.pages]
        except Exception as exc:
            relatorio.append({"arquivo": str(pdf), "erro": f"{type(exc).__name__}: {exc}"})
            print(f"  falhou {pdf.name}: {exc}")
            continue
        texto = "\n\n".join(
            f"===== PÁGINA {i + 1} =====\n{t}" for i, t in enumerate(paginas)
        )
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")
        com_texto = sum(1 for t in paginas if t.strip())
        relatorio.append(
            {
                "arquivo": str(pdf),
                "paginas": len(paginas),
                "paginas_com_texto": com_texto,
                "digitalizado": com_texto < max(1, len(paginas) // 4),
            }
        )
        print(f"  ok {pdf.name}: {com_texto}/{len(paginas)} páginas com texto")
    (saida / "EXTRACAO.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--saida", default="_entrada/tce_mg_licitacoes", help="diretório de trabalho")
    p.add_argument("--token-file", default="token.txt", help="arquivo com o tokenAuthorizationProxy")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("listar", help="consulta a API e grava o manifesto")
    pl.add_argument("--lei", default="14.133")
    pl.add_argument("--fontes", nargs="+", default=["SIAD", "Admin"])
    pl.add_argument(
        "--modalidades", nargs="+", default=["Dispensa de Licitação", "Pregão"]
    )
    pl.set_defaults(func=cmd_listar)

    pb = sub.add_parser("baixar", help="baixa DOC Interna/Externa e anexos")
    pb.add_argument("--forcar", action="store_true")
    pb.set_defaults(func=cmd_baixar)

    pe = sub.add_parser("extrair", help="extrai o texto dos PDFs baixados")
    pe.add_argument("--forcar", action="store_true")
    pe.set_defaults(func=cmd_extrair)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
