"""Orquestrador de conversões.

Mantém o registro de conversores e roteia cada solicitação para
o conversor adequado. Adicionar um novo formato é tão simples
quanto chamar :func:`register_converter` com a nova instância.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .converters import (
    BaseConverter,
    ConversionOptions,
    DocxToPdfConverter,
    ImageConverter,
    PdfToImageConverter,
    TxtToPdfConverter,
)
from .exceptions import (
    BatchDirectoryError,
    ConversionError,
    UnsupportedFormatError,
)
from .utils import (
    ProgressBar,
    get_logger,
    iter_files_in_directory,
    normalize_extension,
    validate_batch_directory,
    validate_input_path,
    validate_output_path,
)


@dataclass(frozen=True)
class BatchResult:
    """Resumo de uma execução em lote.

    Attributes:
        total: número de arquivos encontrados na pasta de origem.
        converted: número de arquivos convertidos com sucesso.
        skipped: lista de pares ``(arquivo, motivo)`` para arquivos pulados.
        failed: lista de pares ``(arquivo, erro)`` para falhas.
    """

    total: int
    converted: int
    skipped: list[tuple[Path, str]]
    failed: list[tuple[Path, str]]


class ConversionEngine:
    """Registro e roteamento de conversores."""

    def __init__(self) -> None:
        self._converters: list[BaseConverter] = []

    def register(self, converter: BaseConverter) -> None:
        """Registra um conversor no engine."""
        self._converters.append(converter)

    def find_converter(self, source: str, target: str) -> BaseConverter:
        """Retorna o conversor adequado para o par origem/destino.

        Raises:
            UnsupportedFormatError: nenhum conversor registrado lida
                com esse par.
        """
        source = normalize_extension(source)
        target = normalize_extension(target)
        for conv in self._converters:
            if conv.supports(source, target):
                return conv
        raise UnsupportedFormatError(
            source_format=source,
            target_format=target,
            supported=sorted(self.supported_targets()),
        )

    def supported_sources(self) -> set[str]:
        """Conjunto de todas as extensões de origem suportadas."""
        result: set[str] = set()
        for conv in self._converters:
            result.update(conv.source_formats)
        return result

    def supported_targets(self) -> set[str]:
        """Conjunto de todas as extensões de destino suportadas."""
        result: set[str] = set()
        for conv in self._converters:
            result.update(conv.target_formats)
        return result

    def convert_file(
        self,
        input_path: Path,
        output_path: Path,
        options: ConversionOptions | None = None,
    ) -> Path:
        """Converte um único arquivo.

        Args:
            input_path: arquivo de entrada.
            output_path: caminho do arquivo de saída.
            options: opções de conversão; usa valores padrão se ``None``.

        Returns:
            Caminho efetivamente gerado pelo conversor.

        Raises:
            InputFileNotFoundError: entrada não existe.
            InvalidPathError: entrada/saída inválida.
            UnsupportedFormatError: par origem/destino não suportado.
            ConversionError: falha durante a conversão.
        """
        options = options or ConversionOptions()
        logger = get_logger()

        validate_input_path(input_path)
        source_ext = normalize_extension(input_path)
        target_ext = normalize_extension(output_path)

        if not source_ext:
            raise UnsupportedFormatError(
                source_format="(sem extensão)",
                target_format=target_ext,
            )
        if not target_ext:
            raise UnsupportedFormatError(
                source_format=source_ext,
                target_format="(sem extensão)",
            )

        converter = self.find_converter(source_ext, target_ext)
        validate_output_path(output_path, overwrite=options.overwrite)

        logger.info("Convertendo '%s' → '%s'", input_path.name, output_path.name)
        result = converter.convert(input_path, output_path, options)
        return result

    def convert_batch(
        self,
        source_dir: Path,
        target_dir: Path,
        target_format: str,
        options: ConversionOptions | None = None,
        recursive: bool = False,
        show_progress: bool = True,
    ) -> BatchResult:
        """Converte todos os arquivos de uma pasta para um formato-alvo.

        Args:
            source_dir: pasta de origem (deve existir).
            target_dir: pasta de destino (criada se não existir).
            target_format: extensão-alvo (ex.: ``"webp"``).
            options: opções de conversão; usa padrão se ``None``.
            recursive: se ``True``, percorre subpastas recursivamente.
            show_progress: se ``True``, renderiza barra de progresso.

        Returns:
            :class:`BatchResult` com estatísticas.
        """
        options = options or ConversionOptions()
        logger = get_logger()
        validate_batch_directory(source_dir, must_exist=True)
        validate_batch_directory(target_dir, must_exist=False)

        if source_dir.resolve() == target_dir.resolve():
            raise BatchDirectoryError(
                "Pasta de origem e destino não podem ser a mesma. "
                "Especifique caminhos diferentes."
            )

        target_format = normalize_extension(target_format)
        files = list(iter_files_in_directory(source_dir, recursive=recursive))
        if not files:
            logger.warning("Nenhum arquivo encontrado em '%s'.", source_dir)
            return BatchResult(total=0, converted=0, skipped=[], failed=[])

        progress = ProgressBar(total=len(files), enabled=show_progress)
        converted = 0
        skipped: list[tuple[Path, str]] = []
        failed: list[tuple[Path, str]] = []

        for entry in files:
            source_ext = normalize_extension(entry)
            try:
                converter = self.find_converter(source_ext, target_format)
            except UnsupportedFormatError as exc:
                skipped.append((entry, str(exc)))
                logger.warning("Pulando '%s': %s", entry.name, exc)
                progress.update(label=entry.name)
                continue

            del converter
            relative = entry.relative_to(source_dir)
            destination = target_dir / relative.with_suffix(f".{target_format}")
            try:
                self.convert_file(entry, destination, options)
                converted += 1
            except ConversionError as exc:
                failed.append((entry, str(exc)))
                logger.error("Falha ao converter '%s': %s", entry.name, exc)
            progress.update(label=entry.name)

        progress.close()
        return BatchResult(total=len(files), converted=converted, skipped=skipped, failed=failed)


def build_default_engine() -> ConversionEngine:
    """Cria um engine pré-configurado com todos os conversores embutidos."""
    engine = ConversionEngine()
    engine.register(ImageConverter())
    engine.register(PdfToImageConverter())
    engine.register(TxtToPdfConverter())
    engine.register(DocxToPdfConverter())
    return engine
