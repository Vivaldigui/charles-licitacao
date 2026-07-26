#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
locks.py — trava por processo e tipo documental (item 28 do escopo).

Duas gerações simultâneas do mesmo TR são a origem clássica do "TR_final_2":
uma sessão sobrescreve o trabalho da outra e alguém salva um paralelo para não
perder. Aqui a segunda sessão simplesmente não começa.

O lock é um arquivo `.locks/TIPO.lock` criado com `O_EXCL` — a exclusão é do
sistema de arquivos, não de uma checagem em Python. Ele guarda processo,
documento, início, sessão, PID e expiração.

**Lock abandonado.** Uma sessão que morre no meio deixa o arquivo para trás.
Recuperar é legítimo, mas só sob duas condições verificáveis: o prazo expirou,
ou o PID que o criou não existe mais NESTA máquina. A recuperação é registrada
— nunca silenciosa. Na dúvida (outra máquina, PID não verificável), o lock é
respeitado e o operador decide, porque perder trabalho alheio é pior do que
esperar.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

PASTA_LOCKS = ".locks"
TTL_PADRAO_SEGUNDOS = 900  # 15 minutos: geração de DOCX longa cabe folgada.


class LockIndisponivel(RuntimeError):
    """Outra sessão está trabalhando neste documento."""


@dataclass
class DadosLock:
    processo: str
    documento: str
    inicio: str
    expira_em: str
    sessao: str
    maquina: str
    pid: Optional[int] = None

    def expirado(self, agora: Optional[datetime] = None) -> bool:
        agora = agora or datetime.now()
        try:
            return datetime.fromisoformat(self.expira_em) < agora
        except (TypeError, ValueError):
            return True  # carimbo ilegível: trata como expirado, e registra.


def _processo_vivo(pid: Optional[int], maquina: str) -> Optional[bool]:
    """
    O PID ainda existe? None = não verificável (outra máquina ou API ausente).

    Em Windows, `os.kill(pid, 0)` NÃO é uma sonda: ele chama TerminateProcess e
    mataria o processo consultado. Por isso a verificação usa OpenProcess.
    """
    if not pid or maquina != socket.gethostname():
        return None
    if sys.platform == "win32":
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid)
            )
            if not handle:
                return False
            try:
                codigo = ctypes.c_ulong()
                if kernel32.GetExitCodeProcess(handle, ctypes.byref(codigo)):
                    return codigo.value == STILL_ACTIVE
                return None
            finally:
                kernel32.CloseHandle(handle)
        except Exception:  # pragma: no cover - ambiente sem ctypes utilizável
            return None
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # existe, é de outro usuário
    except OSError:
        return None
    return True


class LockDocumento:
    """
    Trava exclusiva de um tipo documental dentro de um processo.

    Uso:
        with LockDocumento(raiz_processo, "PA_031_2026", "TR") as lock:
            ...
    """

    def __init__(
        self,
        raiz_processo: Path | str,
        processo: str,
        documento: str,
        ttl_segundos: int = TTL_PADRAO_SEGUNDOS,
        sessao: Optional[str] = None,
    ) -> None:
        self.raiz = Path(raiz_processo)
        self.processo = processo
        self.documento = documento
        self.ttl = int(ttl_segundos)
        self.sessao = sessao or os.environ.get("CHARLES_SESSAO") or uuid.uuid4().hex[:12]
        self.caminho = self.raiz / PASTA_LOCKS / f"{documento}.lock"
        self.recuperado: Optional[str] = None
        self._adquirido = False

    # -- leitura ----------------------------------------------------------- #

    def ler(self) -> Optional[DadosLock]:
        if not self.caminho.exists():
            return None
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            return DadosLock(**{c: dados.get(c) for c in DadosLock.__annotations__})
        except (json.JSONDecodeError, TypeError, ValueError, OSError):
            return None

    def _motivo_recuperacao(self, dados: Optional[DadosLock]) -> Optional[str]:
        """Por que este lock pode ser tomado? None = não pode."""
        if dados is None:
            return "arquivo de lock ilegível ou corrompido"
        if dados.expirado():
            return f"lock expirado em {dados.expira_em}"
        vivo = _processo_vivo(dados.pid, dados.maquina or "")
        if vivo is False:
            return f"processo {dados.pid} não existe mais nesta máquina"
        return None

    # -- aquisição --------------------------------------------------------- #

    def adquirir(self, esperar_segundos: float = 0.0) -> "LockDocumento":
        limite = time.monotonic() + max(0.0, esperar_segundos)
        while True:
            if self._tentar():
                return self
            motivo = self._motivo_recuperacao(self.ler())
            if motivo:
                self.liberar_forcado(motivo)
                if self._tentar():
                    return self
            if time.monotonic() >= limite:
                dados = self.ler()
                detalhe = (
                    f"sessão {dados.sessao} desde {dados.inicio} (expira {dados.expira_em})"
                    if dados else "lock presente"
                )
                raise LockIndisponivel(
                    f"O documento {self.documento} do processo {self.processo} já está "
                    f"em processamento por outra sessão: {detalhe}. "
                    f"Nada foi alterado."
                )
            time.sleep(0.2)

    def _tentar(self) -> bool:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        agora = datetime.now()
        dados = DadosLock(
            processo=self.processo,
            documento=self.documento,
            inicio=agora.isoformat(timespec="seconds"),
            expira_em=(agora + timedelta(seconds=self.ttl)).isoformat(timespec="seconds"),
            sessao=self.sessao,
            maquina=socket.gethostname(),
            pid=os.getpid(),
        )
        try:
            descritor = os.open(
                self.caminho, os.O_CREAT | os.O_EXCL | os.O_WRONLY
            )
        except FileExistsError:
            return False
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            json.dump(asdict(dados), arquivo, ensure_ascii=False, indent=2)
        self._adquirido = True
        return True

    def liberar_forcado(self, motivo: str) -> None:
        """Remove lock abandonado. A recuperação fica registrada no objeto."""
        self.recuperado = motivo
        try:
            self.caminho.unlink()
        except FileNotFoundError:
            pass

    def liberar(self) -> None:
        if not self._adquirido:
            return
        dados = self.ler()
        # Só remove o lock que ainda é meu: se outra sessão o recuperou por
        # expiração, quem manda no arquivo agora é ela.
        if dados is None or dados.sessao == self.sessao:
            try:
                self.caminho.unlink()
            except FileNotFoundError:
                pass
        self._adquirido = False

    # -- contexto ---------------------------------------------------------- #

    def __enter__(self) -> "LockDocumento":
        return self.adquirir()

    def __exit__(self, *_excecao) -> None:
        self.liberar()


def locks_ativos(raiz_processo: Path | str) -> list[DadosLock]:
    """Locks presentes na pasta do processo, expirados inclusive."""
    pasta = Path(raiz_processo) / PASTA_LOCKS
    if not pasta.is_dir():
        return []
    encontrados: list[DadosLock] = []
    for arquivo in sorted(pasta.glob("*.lock")):
        lock = LockDocumento(raiz_processo, "", arquivo.stem)
        dados = lock.ler()
        if dados:
            encontrados.append(dados)
    return encontrados
