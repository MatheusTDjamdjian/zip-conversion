"""Ponto de entrada para ``python -m converter.web``.

Sobe o servidor Flask e abre o navegador na URL local. Use
``--no-browser`` em ambientes sem GUI.
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from threading import Timer

from .app import create_app


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos do servidor web."""
    parser = argparse.ArgumentParser(
        prog="converter.web",
        description=(
            "Sobe a interface web local do converter. Acesse "
            "http://localhost:5000 no navegador para usar."
        ),
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Endereço de escuta (padrão: 127.0.0.1 — apenas local).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Porta TCP (padrão: 5000).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Não tentar abrir o navegador automaticamente.",
    )
    parser.add_argument(
        "--max-upload-mb",
        type=int,
        default=64,
        help="Tamanho máximo de upload em MiB (padrão: 64).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Executa o servidor."""
    args = build_parser().parse_args(argv)
    app = create_app(max_upload_mb=args.max_upload_mb)

    url = f"http://{'localhost' if args.host == '0.0.0.0' else args.host}:{args.port}/"
    print(f"Servidor web em {url} — pressione Ctrl+C para encerrar.")

    if not args.no_browser:
        Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
