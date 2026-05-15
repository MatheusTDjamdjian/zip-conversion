"""Exceções customizadas para a ferramenta de conversão.

Todas as mensagens são escritas em português claro e acionável,
informando ao usuário não apenas o que falhou, mas o que ele
pode fazer para resolver o problema.
"""

from __future__ import annotations

from pathlib import Path


class ConverterError(Exception):
    """Exceção base de todos os erros da ferramenta.

    Permite que código cliente capture qualquer erro originado
    pela ferramenta com um único `except`.
    """


class ConversionError(ConverterError):
    """Erro genérico durante o processo de conversão.

    Levantado quando uma conversão falha por um motivo que não
    é estrutural (formato, arquivo inexistente, etc.), por
    exemplo erros internos das bibliotecas de terceiros.
    """


class UnsupportedFormatError(ConverterError):
    """Formato de origem ou destino não suportado pela ferramenta.

    Args:
        source_format: extensão de origem (ex.: ``"heic"``).
        target_format: extensão de destino (ex.: ``"webp"``).
        supported: lista opcional de formatos suportados.
    """

    def __init__(
        self,
        source_format: str,
        target_format: str,
        supported: list[str] | None = None,
    ) -> None:
        msg = (
            f"Conversão de '{source_format}' para '{target_format}' não é suportada. "
            "Verifique a tabela de formatos no README."
        )
        if supported:
            msg += f" Formatos suportados: {', '.join(sorted(supported))}."
        super().__init__(msg)
        self.source_format = source_format
        self.target_format = target_format


class InputFileNotFoundError(ConverterError):
    """Arquivo de entrada não encontrado.

    Distinta da ``FileNotFoundError`` padrão para permitir mensagens
    em português e tratamento específico.
    """

    def __init__(self, path: Path) -> None:
        super().__init__(
            f"Arquivo de entrada não encontrado: '{path}'. "
            "Verifique se o caminho está correto e se o arquivo existe."
        )
        self.path = path


class InvalidPathError(ConverterError):
    """Caminho de entrada ou saída inválido (permissões, tipo, etc.)."""

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"Caminho inválido '{path}': {reason}")
        self.path = path


class BatchDirectoryError(ConverterError):
    """Erro relacionado a diretórios no modo de conversão em lote."""
