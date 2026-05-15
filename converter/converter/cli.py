"""Interface de linha de comando.

Constrói o parser ``argparse`` em português, valida argumentos e
delega a execução ao :class:`ConversionEngine`.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .converters import ConversionOptions
from .core import BatchResult, build_default_engine
from .exceptions import ConverterError
from .utils import (
    configure_logging,
    get_logger,
    normalize_extension,
    parse_resize,
)

_EPILOG = """\
Exemplos de uso:
  python -m converter foto.png foto.webp
  python -m converter --quality 90 foto.jpg foto.webp
  python -m converter --resize 1920x1080 foto.png foto_hd.png
  python -m converter --batch ./entrada ./saida --to webp
  python -m converter --batch ./pdfs ./imagens --to png --recursive
  python -m converter documento.docx documento.pdf
  python -m converter relatorio.pdf relatorio.png

Mais informações no README.md.
"""


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        prog="converter",
        description=(
            "Ferramenta leve para conversão de arquivos: imagens, "
            "documentos e PDFs. Suporta arquivo único ou conversão em lote."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "input",
        nargs="?",
        help=("Arquivo de entrada (ou pasta de entrada quando --batch é " "usado)."),
    )
    parser.add_argument(
        "output",
        nargs="?",
        help=(
            "Arquivo de saída (ou pasta de saída quando --batch é usado). "
            "A extensão determina o formato de destino."
        ),
    )

    batch_group = parser.add_argument_group("Conversão em lote")
    batch_group.add_argument(
        "--batch",
        action="store_true",
        help="Converte todos os arquivos da pasta de entrada para a pasta de saída.",
    )
    batch_group.add_argument(
        "--to",
        dest="to_format",
        metavar="FORMATO",
        help=("Formato-alvo no modo --batch (ex.: png, webp, pdf). " "Sem ponto inicial."),
    )
    batch_group.add_argument(
        "--recursive",
        action="store_true",
        help="No modo --batch, percorre subpastas recursivamente.",
    )

    options_group = parser.add_argument_group("Opções de conversão")
    options_group.add_argument(
        "--quality",
        type=int,
        default=85,
        metavar="N",
        help="Qualidade de 1 a 100 para JPEG/WEBP (padrão: 85).",
    )
    options_group.add_argument(
        "--resize",
        metavar="LxA",
        help="Redimensiona imagens para LARGURAxALTURA (ex.: 1920x1080).",
    )
    options_group.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Não sobrescrever arquivos de saída já existentes.",
    )

    log_group = parser.add_argument_group("Verbosidade")
    log_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Exibe logs detalhados (nível DEBUG).",
    )
    log_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suprime mensagens informativas (apenas avisos/erros).",
    )

    info_group = parser.add_argument_group("Informações")
    info_group.add_argument(
        "--list-formats",
        action="store_true",
        help="Lista os formatos suportados pela ferramenta e encerra.",
    )

    return parser


def _validate_quality(value: int) -> int:
    """Garante que a qualidade está no intervalo aceitável."""
    if not 1 <= value <= 100:
        raise SystemExit("Erro: --quality deve estar entre 1 e 100 (recebido: " f"{value}).")
    return value


def _print_supported_formats() -> None:
    """Imprime tabela de formatos suportados na stdout."""
    engine = build_default_engine()
    sources = sorted(engine.supported_sources())
    targets = sorted(engine.supported_targets())
    print("Formatos de entrada suportados:")
    for fmt in sources:
        print(f"  - {fmt}")
    print()
    print("Formatos de saída suportados:")
    for fmt in targets:
        print(f"  - {fmt}")


def _summarize_batch(result: BatchResult) -> None:
    """Imprime resumo de uma execução em lote no stdout."""
    print()
    print("Resumo do lote:")
    print(f"  Arquivos encontrados: {result.total}")
    print(f"  Convertidos:          {result.converted}")
    print(f"  Pulados:              {len(result.skipped)}")
    print(f"  Falhas:               {len(result.failed)}")

    if result.skipped:
        print("\nArquivos pulados:")
        for path, reason in result.skipped:
            print(f"  - {path.name}: {reason}")
    if result.failed:
        print("\nFalhas:")
        for path, reason in result.failed:
            print(f"  - {path.name}: {reason}")


def run(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada da CLI.

    Args:
        argv: argumentos da linha de comando; se ``None``, usa ``sys.argv``.

    Returns:
        Código de saída do processo.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose and args.quiet:
        parser.error("--verbose e --quiet são mutuamente exclusivos.")

    configure_logging(verbose=args.verbose, quiet=args.quiet)
    logger = get_logger()

    if args.list_formats:
        _print_supported_formats()
        return 0

    quality = _validate_quality(args.quality)
    resize: tuple[int, int] | None = None
    if args.resize:
        try:
            resize = parse_resize(args.resize)
        except ValueError as exc:
            parser.error(str(exc))

    options = ConversionOptions(
        quality=quality,
        resize=resize,
        overwrite=not args.no_overwrite,
    )

    engine = build_default_engine()

    if args.batch:
        return _run_batch(args, engine, options, logger, parser)

    return _run_single(args, engine, options, logger, parser)


def _run_single(
    args: argparse.Namespace,
    engine,
    options: ConversionOptions,
    logger,
    parser: argparse.ArgumentParser,
) -> int:
    """Executa conversão de arquivo único."""
    if not args.input or not args.output:
        parser.error(
            "Argumentos obrigatórios faltando: especifique <input> e "
            "<output>, ou use --batch para conversão em lote."
        )

    input_path = Path(args.input).expanduser()
    output_path = Path(args.output).expanduser()

    try:
        result = engine.convert_file(input_path, output_path, options)
    except ConverterError as exc:
        logger.error("%s", exc)
        return 1

    logger.info("Conversão concluída: %s", result)
    return 0


def _run_batch(
    args: argparse.Namespace,
    engine,
    options: ConversionOptions,
    logger,
    parser: argparse.ArgumentParser,
) -> int:
    """Executa conversão em lote."""
    if not args.input or not args.output:
        parser.error("No modo --batch, especifique a pasta de entrada e a pasta de saída.")
    if not args.to_format:
        parser.error(
            "No modo --batch é obrigatório informar --to com o formato-alvo " "(ex.: --to webp)."
        )

    source_dir = Path(args.input).expanduser()
    target_dir = Path(args.output).expanduser()
    target_format = normalize_extension(args.to_format)

    try:
        result = engine.convert_batch(
            source_dir=source_dir,
            target_dir=target_dir,
            target_format=target_format,
            options=options,
            recursive=args.recursive,
            show_progress=not args.quiet,
        )
    except ConverterError as exc:
        logger.error("%s", exc)
        return 1

    _summarize_batch(result)

    if result.failed:
        return 2
    if result.converted == 0 and result.total > 0:
        return 3
    return 0


def main() -> None:
    """Wrapper que delega para :func:`run` e propaga o exit code."""
    sys.exit(run())
