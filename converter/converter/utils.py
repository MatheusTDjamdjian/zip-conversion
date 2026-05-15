"""Helpers reutilizáveis: validação de caminhos, logging e barra de progresso.

Mantém apenas utilitários transversais. Lógica de conversão fica
em ``converters/``.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterable
from pathlib import Path

from .exceptions import InputFileNotFoundError, InvalidPathError

_LOGGER_NAME = "converter"


def get_logger() -> logging.Logger:
    """Retorna o logger raiz da ferramenta (sem reconfigurar)."""
    return logging.getLogger(_LOGGER_NAME)


def configure_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configura o logger raiz da ferramenta.

    Args:
        verbose: se ``True``, define nível DEBUG.
        quiet: se ``True``, define nível WARNING (apenas avisos/erros).

    Se ambos forem ``False``, o nível padrão é INFO.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    logger.handlers.clear()

    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    handler = logging.StreamHandler(stream=sys.stderr)
    if verbose:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    else:
        fmt = "%(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def normalize_extension(ext_or_path: str | Path) -> str:
    """Normaliza uma extensão para minúsculas e sem ponto.

    Aceita tanto uma string (``".PNG"``, ``"png"``) quanto um ``Path``.
    """
    if isinstance(ext_or_path, Path):
        ext = ext_or_path.suffix
    else:
        ext = ext_or_path
    return ext.lower().lstrip(".")


def validate_input_path(path: Path) -> Path:
    """Valida que o caminho existe e é um arquivo legível.

    Returns:
        O próprio ``path``, já resolvido.

    Raises:
        InputFileNotFoundError: caminho não existe.
        InvalidPathError: existe mas não é arquivo ou não pode ser lido.
    """
    if not path.exists():
        raise InputFileNotFoundError(path)
    if not path.is_file():
        raise InvalidPathError(path, "o caminho não aponta para um arquivo.")
    try:
        with path.open("rb"):
            pass
    except PermissionError as exc:
        raise InvalidPathError(
            path,
            "sem permissão de leitura. Verifique as permissões do arquivo.",
        ) from exc
    return path


def validate_output_path(path: Path, overwrite: bool = True) -> Path:
    """Valida o caminho de saída e cria o diretório-pai se necessário.

    Args:
        path: caminho do arquivo a ser escrito.
        overwrite: se ``False``, levanta erro caso o arquivo exista.

    Raises:
        InvalidPathError: diretório-pai não pode ser criado ou arquivo
            já existe com ``overwrite=False``.
    """
    parent = path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise InvalidPathError(
            parent, f"não foi possível criar o diretório de saída ({exc})."
        ) from exc

    if path.exists() and not overwrite:
        raise InvalidPathError(
            path, "arquivo de destino já existe e sobrescrita está desabilitada."
        )
    return path


def validate_batch_directory(path: Path, must_exist: bool = True) -> Path:
    """Valida um diretório usado em conversão em lote.

    Args:
        path: caminho do diretório.
        must_exist: se ``True``, o diretório deve existir; caso contrário,
            é criado.
    """
    if must_exist:
        if not path.exists():
            raise InvalidPathError(path, "diretório não encontrado.")
        if not path.is_dir():
            raise InvalidPathError(path, "o caminho não aponta para um diretório.")
    else:
        path.mkdir(parents=True, exist_ok=True)
    return path


def iter_files_in_directory(directory: Path, recursive: bool = False) -> Iterable[Path]:
    """Itera arquivos de um diretório, ignorando ocultos.

    Args:
        directory: pasta a ser percorrida.
        recursive: se ``True``, desce em subpastas.
    """
    pattern = "**/*" if recursive else "*"
    for entry in sorted(directory.glob(pattern)):
        if entry.is_file() and not entry.name.startswith("."):
            yield entry


def parse_resize(value: str) -> tuple[int, int]:
    """Faz parse de string ``"LARGURAxALTURA"`` em tupla.

    Args:
        value: string como ``"1920x1080"``.

    Raises:
        ValueError: formato inválido ou dimensões não positivas.
    """
    parts = value.lower().replace("×", "x").split("x")
    if len(parts) != 2:
        raise ValueError(
            f"Valor de redimensionamento inválido: '{value}'. "
            "Use o formato LARGURAxALTURA (ex.: 1920x1080)."
        )
    try:
        width, height = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError(f"Dimensões devem ser números inteiros. Recebido: '{value}'.") from exc
    if width <= 0 or height <= 0:
        raise ValueError(f"Dimensões devem ser positivas. Recebido: {width}x{height}.")
    return width, height


class ProgressBar:
    """Barra de progresso simples, sem dependências externas.

    Renderiza no ``stderr`` apenas se a saída for um TTY e o modo
    silencioso não estiver ativo.
    """

    def __init__(self, total: int, width: int = 30, enabled: bool = True) -> None:
        self.total = max(total, 1)
        self.width = width
        self.current = 0
        self.enabled = enabled and sys.stderr.isatty() and total > 0

    def update(self, amount: int = 1, label: str = "") -> None:
        """Incrementa o progresso e redesenha a barra."""
        self.current += amount
        if not self.enabled:
            return
        ratio = min(self.current / self.total, 1.0)
        filled = int(self.width * ratio)
        bar = "#" * filled + "-" * (self.width - filled)
        pct = int(ratio * 100)
        line = f"[{bar}] {pct:3d}% ({self.current}/{self.total})"
        if label:
            line += f" {label}"
        sys.stderr.write("\r" + line + " " * 8)
        sys.stderr.flush()

    def close(self) -> None:
        """Finaliza a barra com uma quebra de linha."""
        if self.enabled:
            sys.stderr.write("\n")
            sys.stderr.flush()
