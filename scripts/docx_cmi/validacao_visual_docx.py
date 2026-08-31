#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validacao_visual_docx.py — Conversão DOCX→PDF e conferência da renderização.

Existe porque o módulo de padronização declarava a validação visual como "não
executada — LibreOffice/soffice não disponível no ambiente" por TEXTO FIXO: a
frase era escrita sem que nada procurasse o conversor. Com LibreOffice instalado,
a afirmação passava a ser falsa — exatamente o tipo de conferência não executada
que a regra do módulo proíbe declarar.

O que esta validação PODE afirmar:
  - o documento abre em um renderizador real (LibreOffice/Word converte sem
    erro). Isso pega corrupção estrutural que `python-docx` tolera em silêncio;
  - quantas páginas o documento tem antes e depois da padronização;
  - se a saída ganhou página em branco que a entrada não tinha.

O que ela NÃO afirma, e nunca deve ser lida como se afirmasse:
  - que o documento "está bonito", alinhado ou pronto para assinatura. Isso é
    conferência humana. Mudança de paginação, aliás, é consequência ESPERADA de
    reformatar — por isso o resultado é informativo e não bloqueia a gravação.

Dependências: nenhuma obrigatória. Sem conversor, a validação não roda e diz
isso. Sem `pypdf` (que o repositório já usa em requirements-auditor.txt), o PDF
é gerado mas a contagem de páginas fica NÃO VERIFICADA — nunca presumida.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

CAMINHOS_LIBREOFFICE = (
    "soffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/usr/bin/libreoffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
)

# Conversão via Word: `SaveAs2` com WdFormat 17 = wdFormatPDF.
SCRIPT_WORD = """
$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject Word.Application
$app.Visible = $false
try {{
    $doc = $app.Documents.Open('{entrada}', $false, $true)
    $doc.SaveAs2('{saida}', 17)
    $doc.Close(0)
}} finally {{
    $app.Quit()
}}
"""

TEMPO_LIMITE_S = 300


# --------------------------------------------------------------------------- #
# Detecção do conversor
# --------------------------------------------------------------------------- #

@dataclass
class Conversor:
    """Conversor DOCX→PDF disponível no ambiente."""

    nome: str
    caminho: Optional[str] = None

    def disponivel(self) -> bool:
        return self.nome != "nenhum"

    def descricao(self) -> str:
        if not self.disponivel():
            return "nenhum conversor disponível"
        return f"{self.nome} ({self.caminho})"


def detectar_conversor() -> Conversor:
    """Procura LibreOffice e, no Windows, o Word. Sem nenhum, devolve 'nenhum'."""
    for candidato in CAMINHOS_LIBREOFFICE:
        caminho = shutil.which(candidato) if os.sep not in candidato else (
            candidato if Path(candidato).exists() else None)
        if caminho:
            return Conversor("libreoffice", caminho)
    if sys.platform == "win32" and shutil.which("powershell"):
        for variavel in ("ProgramFiles", "ProgramFiles(x86)"):
            raiz = os.environ.get(variavel)
            if raiz and any(Path(raiz).glob("Microsoft Office/**/WINWORD.EXE")):
                return Conversor("word", "powershell")
    return Conversor("nenhum")


# --------------------------------------------------------------------------- #
# Conversão
# --------------------------------------------------------------------------- #

def _converter_libreoffice(conversor: Conversor, entrada: Path,
                           pasta_saida: Path) -> Optional[Path]:
    """
    Converte com LibreOffice em perfil de usuário isolado.

    O `-env:UserInstallation` não é detalhe: sem ele, o processo headless
    disputa o perfil de um LibreOffice já aberto pelo usuário e sai sem
    converter e sem erro — falha silenciosa, o pior desfecho possível aqui.
    """
    with tempfile.TemporaryDirectory(prefix="charles_lo_") as perfil:
        subprocess.run(
            [conversor.caminho, "--headless", "--norestore",
             f"-env:UserInstallation={Path(perfil).as_uri()}",
             "--convert-to", "pdf", "--outdir", str(pasta_saida), str(entrada)],
            check=True, capture_output=True, timeout=TEMPO_LIMITE_S,
        )
    destino = pasta_saida / (entrada.stem + ".pdf")
    return destino if destino.exists() else None


def _converter_word(entrada: Path, destino: Path) -> Optional[Path]:
    script = SCRIPT_WORD.format(
        entrada=str(entrada.resolve()).replace("'", "''"),
        saida=str(destino.resolve()).replace("'", "''"),
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        check=True, capture_output=True, timeout=TEMPO_LIMITE_S,
    )
    return destino if destino.exists() else None


def converter(entrada: Path, destino: Path,
              conversor: Optional[Conversor] = None) -> Optional[Path]:
    """
    Converte um DOCX em PDF no caminho `destino`. Devolve None se não converteu.

    Propaga exceção nenhuma: erro de conversão vira None, e cabe a quem chama
    dizer o que faltou. Nunca inventa um PDF que não existe.
    """
    conversor = conversor or detectar_conversor()
    if not conversor.disponivel():
        return None
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        if conversor.nome == "libreoffice":
            gerado = _converter_libreoffice(conversor, entrada, destino.parent)
            if gerado and gerado != destino:
                shutil.move(str(gerado), str(destino))
                gerado = destino
            return gerado
        return _converter_word(entrada, destino)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None


# --------------------------------------------------------------------------- #
# Leitura do PDF gerado
# --------------------------------------------------------------------------- #

@dataclass
class Renderizacao:
    """O que se conseguiu observar do PDF de um documento."""

    pdf: Optional[Path] = None
    paginas: Optional[int] = None
    paginas_vazias: list[int] = field(default_factory=list)
    lido: bool = False

    @property
    def convertido(self) -> bool:
        return self.pdf is not None


def _pypdf():
    try:
        import pypdf
    except ImportError:
        return None
    return pypdf


def inspecionar_pdf(pdf: Path) -> Renderizacao:
    """
    Conta páginas e localiza páginas sem nada renderizado.

    Página vazia é a que não tem texto NEM imagem: uma página só com o brasão
    do timbre continua sendo página com conteúdo, e marcá-la como vazia seria
    falso positivo justamente sobre a parte protegida do documento.
    """
    resultado = Renderizacao(pdf=pdf)
    modulo = _pypdf()
    if modulo is None:
        return resultado
    try:
        leitor = modulo.PdfReader(str(pdf))
        resultado.paginas = len(leitor.pages)
        for numero, pagina in enumerate(leitor.pages, start=1):
            try:
                texto = (pagina.extract_text() or "").strip()
            except Exception:  # pragma: no cover - PDF com fonte exótica
                texto = ""
            if texto:
                continue
            recursos = pagina.get("/Resources") or {}
            try:
                imagens = bool(recursos.get_object().get("/XObject"))
            except Exception:  # pragma: no cover
                imagens = False
            if not imagens:
                resultado.paginas_vazias.append(numero)
        resultado.lido = True
    except Exception:  # pragma: no cover - PDF ilegível
        resultado.lido = False
    return resultado


# --------------------------------------------------------------------------- #
# Validação visual
# --------------------------------------------------------------------------- #

@dataclass
class ResultadoVisual:
    """Resultado da conferência de renderização entre entrada e saída."""

    executada: bool = False
    conversor: str = "nenhum"
    motivo: Optional[str] = None
    paginas_antes: Optional[int] = None
    paginas_depois: Optional[int] = None
    paginas_vazias_novas: list[int] = field(default_factory=list)
    observacoes: list[str] = field(default_factory=list)
    exige_conferencia: bool = False
    pdf_antes: Optional[str] = None
    pdf_depois: Optional[str] = None

    def como_dicionario(self) -> dict[str, object]:
        return {
            "executada": self.executada,
            "conversor": self.conversor,
            "motivo": self.motivo,
            "paginas_antes": self.paginas_antes,
            "paginas_depois": self.paginas_depois,
            "paginas_vazias_novas": self.paginas_vazias_novas,
            "observacoes": self.observacoes,
            "exige_conferencia": self.exige_conferencia,
            "pdf_antes": self.pdf_antes,
            "pdf_depois": self.pdf_depois,
        }

    def resumo(self) -> str:
        """Frase única para o campo `testes.validacao_visual` do relatório."""
        if not self.executada:
            return f"não executada — {self.motivo}"
        partes = [f"executada com {self.conversor}"]
        if self.paginas_antes is not None and self.paginas_depois is not None:
            partes.append(f"páginas {self.paginas_antes} -> {self.paginas_depois}")
        else:
            partes.append("contagem de páginas NÃO VERIFICADA (pypdf ausente)")
        partes += self.observacoes
        partes.append("a conferência visual final permanece a cargo do usuário")
        return "; ".join(partes)


def validar(entrada: Path, saida: Path, conversor: Optional[Conversor] = None,
            guardar_em: Optional[Path] = None) -> ResultadoVisual:
    """
    Renderiza entrada e saída e compara o que a renderização revela.

    Nunca bloqueia a gravação: reformatar muda a paginação por definição. O que
    ela sinaliza — falha de conversão, página em branco nova — vira exigência de
    conferência humana, que é a decisão conservadora.

    `guardar_em` preserva os dois PDFs para conferência; sem ele, os PDFs são
    descartados e apenas o que se mediu é reportado.
    """
    conversor = conversor or detectar_conversor()
    resultado = ResultadoVisual(conversor=conversor.nome)

    if not conversor.disponivel():
        resultado.motivo = (
            "nenhum conversor DOCX→PDF encontrado no ambiente (LibreOffice ou "
            "Word); a conferência visual permanece a cargo do usuário"
        )
        return resultado

    with tempfile.TemporaryDirectory(prefix="charles_visual_") as temporario:
        pasta = Path(guardar_em) if guardar_em else Path(temporario)
        pasta.mkdir(parents=True, exist_ok=True)
        pdf_antes = converter(entrada, pasta / "antes.pdf", conversor)
        pdf_depois = converter(saida, pasta / "depois.pdf", conversor)

        if pdf_depois is None:
            resultado.motivo = (
                f"o conversor {conversor.nome} não conseguiu renderizar o "
                f"documento gerado — indício de problema estrutural no DOCX"
            )
            resultado.exige_conferencia = True
            return resultado

        render_depois = inspecionar_pdf(pdf_depois)
        render_antes = inspecionar_pdf(pdf_antes) if pdf_antes else Renderizacao()

        resultado.executada = True
        resultado.paginas_antes = render_antes.paginas
        resultado.paginas_depois = render_depois.paginas

        if pdf_antes is None:
            resultado.observacoes.append(
                "o documento de ENTRADA não pôde ser renderizado — comparação "
                "de páginas indisponível"
            )
            resultado.exige_conferencia = True

        novas = [n for n in render_depois.paginas_vazias
                 if n not in render_antes.paginas_vazias]
        if novas:
            resultado.paginas_vazias_novas = novas
            resultado.observacoes.append(
                "página(s) sem texto nem imagem na saída: "
                + ", ".join(str(n) for n in novas)
            )
            resultado.exige_conferencia = True

        if (resultado.paginas_antes is not None
                and resultado.paginas_depois is not None
                and resultado.paginas_antes != resultado.paginas_depois):
            resultado.observacoes.append(
                "a paginação mudou — consequência possível da reformatação, "
                "confira o resultado no Word"
            )

        if not render_depois.lido:
            resultado.observacoes.append(
                "conteúdo do PDF NÃO VERIFICADO (pypdf ausente ou PDF ilegível)"
            )

        if guardar_em:
            resultado.pdf_antes = str(pdf_antes) if pdf_antes else None
            resultado.pdf_depois = str(pdf_depois)

    return resultado
