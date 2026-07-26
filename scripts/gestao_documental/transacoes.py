#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transacoes.py — substituição de documento como operação tudo-ou-nada (item 29).

O estado do processo mora em dois lugares que precisam concordar: os ARQUIVOS
e os MANIFESTOS. A regra 34 proíbe as duas metades da mesma falha — "atualizar
manifesto sem atualizar arquivos" e "atualizar arquivos sem atualizar
manifesto". Uma exceção no meio do caminho (disco cheio, arquivo aberto no
Word, processo interrompido) produziria exatamente isso.

Aqui toda alteração passa por uma `Transacao`:

* cada passo grava um desfazer antes de agir;
* o original só sai do lugar depois de haver cópia de segurança;
* a entrada final do arquivo novo é `os.replace`, atômica no mesmo volume;
* qualquer exceção dispara o rollback na ordem inversa;
* o diário (`.transacao-*.json`) fica em 99_TEMPORARIOS e registra o que houve.

Rollback também é resultado: ele é gravado no diário e devolvido a quem chamou,
nunca engolido (regra 34: "esconder falha" e "terminar parcialmente").
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from nomes_arquivos import caminho_os  # noqa: E402


class FalhaTransacional(RuntimeError):
    """A transação falhou; o estado anterior foi restaurado."""


class RollbackImpossivel(RuntimeError):
    """A transação falhou E o rollback também. Exige intervenção humana."""


@dataclass
class Passo:
    acao: str
    detalhe: dict[str, Any]
    desfazer: Optional[Callable[[], None]] = None


@dataclass
class Transacao:
    """
    Sequência de operações de arquivo reversível.

    Uso:
        with Transacao(pasta_temporaria, "substituir TR") as tx:
            tx.mover(novo, destino)
            tx.gravar_json(manifesto, dados)
    """

    pasta_trabalho: Path
    descricao: str = ""
    passos: list[Passo] = field(default_factory=list)
    confirmada: bool = False
    rollback_executado: bool = False
    erro: Optional[str] = None
    identificador: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def __post_init__(self) -> None:
        self.pasta_trabalho = Path(self.pasta_trabalho)
        os.makedirs(caminho_os(self.pasta_trabalho), exist_ok=True)
        self._backups = self.pasta_trabalho / "backup"
        self.diario = self.pasta_trabalho / f".transacao-{self.identificador}.json"

    # -- diário ------------------------------------------------------------ #

    def _gravar_diario(self, situacao: str) -> None:
        registro = {
            "id": self.identificador,
            "descricao": self.descricao,
            "situacao": situacao,
            "momento": datetime.now().isoformat(timespec="seconds"),
            "erro": self.erro,
            "passos": [
                {"acao": p.acao, **p.detalhe} for p in self.passos
            ],
        }
        try:
            self.diario.write_text(
                json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass  # o diário é auxiliar; sua falha não pode derrubar o rollback.

    # -- operações --------------------------------------------------------- #

    def salvaguardar(self, caminho: Path | str) -> Optional[Path]:
        """Cópia de segurança de um arquivo existente, antes de mexer nele."""
        caminho = Path(caminho)
        if not caminho.exists():
            return None
        os.makedirs(caminho_os(self._backups), exist_ok=True)
        copia = self._backups / f"{uuid.uuid4().hex[:8]}_{caminho.name}"
        shutil.copy2(caminho_os(caminho), caminho_os(copia))
        self.passos.append(
            Passo("salvaguarda", {"origem": str(caminho), "copia": str(copia)})
        )
        return copia

    def mover(self, origem: Path | str, destino: Path | str) -> Path:
        """
        Move `origem` para `destino` de forma atômica quando possível.

        `os.replace` é atômico dentro do mesmo volume. Entre volumes (o caso de
        `CHARLES_PROCESSOS_DIR` em outro disco) copia-se para um `.part` ao lado
        do destino e só então se faz o replace: o destino nunca existe pela
        metade.
        """
        origem, destino = Path(origem), Path(destino)
        os.makedirs(caminho_os(destino.parent), exist_ok=True)
        # Salvaguarda dos DOIS lados: desfazer um movimento é repor o destino
        # como estava E devolver o arquivo à origem. Sem a cópia da origem, um
        # rollback deixaria o documento anterior sem lugar nenhum.
        copia_origem = self.salvaguardar(origem)
        copia_destino = self.salvaguardar(destino)

        try:
            os.replace(caminho_os(origem), caminho_os(destino))
        except OSError:
            parcial = destino.with_name(f"{destino.name}.part-{self.identificador}")
            shutil.copy2(caminho_os(origem), caminho_os(parcial))
            os.replace(caminho_os(parcial), caminho_os(destino))
            origem.unlink(missing_ok=True)

        def desfazer() -> None:
            if copia_destino and copia_destino.exists():
                shutil.copy2(caminho_os(copia_destino), caminho_os(destino))
            else:
                destino.unlink(missing_ok=True)
            if copia_origem and copia_origem.exists() and not origem.exists():
                os.makedirs(caminho_os(origem.parent), exist_ok=True)
                shutil.copy2(caminho_os(copia_origem), caminho_os(origem))

        self.passos.append(
            Passo("mover", {"origem": str(origem), "destino": str(destino)}, desfazer)
        )
        return destino

    def copiar(self, origem: Path | str, destino: Path | str) -> Path:
        """Copia preservando o original — usado com documento externo (item 17)."""
        origem, destino = Path(origem), Path(destino)
        os.makedirs(caminho_os(destino.parent), exist_ok=True)
        copia_destino = self.salvaguardar(destino)
        shutil.copy2(caminho_os(origem), caminho_os(destino))

        def desfazer() -> None:
            if copia_destino and copia_destino.exists():
                shutil.copy2(caminho_os(copia_destino), caminho_os(destino))
            else:
                destino.unlink(missing_ok=True)

        self.passos.append(
            Passo("copiar", {"origem": str(origem), "destino": str(destino)}, desfazer)
        )
        return destino

    def gravar_json(self, caminho: Path | str, dados: Any) -> Path:
        """Grava JSON via arquivo temporário + replace: nunca meio manifesto."""
        caminho = Path(caminho)
        os.makedirs(caminho_os(caminho.parent), exist_ok=True)
        copia = self.salvaguardar(caminho)
        existia = caminho.exists()
        parcial = caminho.with_name(f"{caminho.name}.part-{self.identificador}")
        with open(caminho_os(parcial), "w", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(dados, ensure_ascii=False, indent=2) + "\n")
        os.replace(caminho_os(parcial), caminho_os(caminho))

        def desfazer() -> None:
            if copia and copia.exists():
                shutil.copy2(caminho_os(copia), caminho_os(caminho))
            elif not existia:
                caminho.unlink(missing_ok=True)

        self.passos.append(Passo("gravar_json", {"arquivo": str(caminho)}, desfazer))
        return caminho

    def gravar_texto(self, caminho: Path | str, texto: str) -> Path:
        caminho = Path(caminho)
        os.makedirs(caminho_os(caminho.parent), exist_ok=True)
        copia = self.salvaguardar(caminho)
        existia = caminho.exists()
        parcial = caminho.with_name(f"{caminho.name}.part-{self.identificador}")
        with open(caminho_os(parcial), "w", encoding="utf-8") as arquivo:
            arquivo.write(texto)
        os.replace(caminho_os(parcial), caminho_os(caminho))

        def desfazer() -> None:
            if copia and copia.exists():
                shutil.copy2(caminho_os(copia), caminho_os(caminho))
            elif not existia:
                caminho.unlink(missing_ok=True)

        self.passos.append(Passo("gravar_texto", {"arquivo": str(caminho)}, desfazer))
        return caminho

    def acrescentar_linha(self, caminho: Path | str, linha: str) -> Path:
        """
        Acrescenta uma linha ao log JSONL (item 13: o log só cresce).

        O desfazer trunca de volta ao tamanho anterior — não reescreve evento
        antigo nenhum.
        """
        caminho = Path(caminho)
        os.makedirs(caminho_os(caminho.parent), exist_ok=True)
        tamanho = caminho.stat().st_size if caminho.exists() else 0
        with open(caminho_os(caminho), "a", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(linha.rstrip("\n") + "\n")

        def desfazer() -> None:
            with open(caminho_os(caminho), "r+b") as arquivo:
                arquivo.truncate(tamanho)

        self.passos.append(
            Passo("acrescentar_linha", {"arquivo": str(caminho)}, desfazer)
        )
        return caminho

    # -- conclusão --------------------------------------------------------- #

    def confirmar(self) -> None:
        self.confirmada = True
        self._gravar_diario("confirmada")

    def desfazer_tudo(self) -> list[str]:
        """Rollback na ordem inversa. Devolve as falhas que sobraram."""
        falhas: list[str] = []
        for passo in reversed(self.passos):
            if passo.desfazer is None:
                continue
            try:
                passo.desfazer()
            except Exception as erro:  # noqa: BLE001 - toda falha precisa aparecer
                falhas.append(f"{passo.acao}: {erro}")
        self.rollback_executado = True
        self._gravar_diario("rollback" if not falhas else "rollback_incompleto")
        return falhas

    def __enter__(self) -> "Transacao":
        self._gravar_diario("iniciada")
        return self

    def __exit__(self, tipo, valor, _traceback) -> bool:
        if tipo is None:
            if not self.confirmada:
                self.confirmar()
            return False
        self.erro = f"{tipo.__name__}: {valor}"
        falhas = self.desfazer_tudo()
        if falhas:
            raise RollbackImpossivel(
                f"Falha em '{self.descricao}' ({self.erro}) e o rollback não "
                f"completou: {'; '.join(falhas)}. Diário: {self.diario}. "
                f"NÃO prossiga sem conferência humana dos arquivos."
            ) from valor
        return False  # propaga o erro original, com o estado já restaurado
