"""Contrato base que todo conversor deve implementar.

Adicionar um novo formato significa criar uma subclasse de
``BaseConverter`` e registrá-la em ``core.py`` — o orquestrador
não precisa de alterações.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConversionOptions:
    """Opções comuns a todas as conversões.

    Attributes:
        quality: qualidade (1-100) para formatos com compressão lossy.
        resize: tupla ``(largura, altura)`` em pixels (apenas imagens).
        overwrite: se ``True``, sobrescreve arquivos existentes.
    """

    quality: int = 85
    resize: tuple[int, int] | None = None
    overwrite: bool = True


class BaseConverter(ABC):
    """Protocolo abstrato de conversor.

    Subclasses devem declarar os formatos de origem e destino que
    suportam em ``source_formats`` e ``target_formats`` (extensões
    em minúsculas, sem ponto).
    """

    source_formats: frozenset[str] = frozenset()
    target_formats: frozenset[str] = frozenset()

    def supports(self, source: str, target: str) -> bool:
        """Indica se este conversor lida com o par origem/destino dado."""
        return source in self.source_formats and target in self.target_formats

    @abstractmethod
    def convert(
        self,
        input_path: Path,
        output_path: Path,
        options: ConversionOptions,
    ) -> Path:
        """Executa a conversão.

        Args:
            input_path: arquivo de entrada (já validado).
            output_path: caminho final do arquivo de saída.
            options: opções aplicáveis à conversão.

        Returns:
            Caminho do arquivo gerado (geralmente igual a ``output_path``,
            mas pode ser uma pasta no caso de PDF→imagens).

        Raises:
            ConversionError: erro durante a conversão.
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Nome legível do conversor (usado em logs)."""
        return self.__class__.__name__
