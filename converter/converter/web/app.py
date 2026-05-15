"""Aplicação Flask que expõe o conversor via navegador.

Mantém o mínimo de estado: cada conversão usa um diretório
temporário descartado ao final. Arquivos resultantes são lidos
em memória antes da resposta para sobreviver à limpeza do
``TemporaryDirectory``.
"""

from __future__ import annotations

import io
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from flask import Flask, Response, render_template, request, send_file
from werkzeug.utils import secure_filename

from ..converters import ConversionOptions
from ..core import ConversionEngine, build_default_engine
from ..exceptions import ConverterError
from ..utils import parse_resize

_DEFAULT_MAX_UPLOAD_MB = 64


@dataclass(frozen=True)
class _Context:
    """Estado compartilhado entre handlers do app."""

    engine: ConversionEngine
    sources: list[str]
    targets: list[str]
    max_upload_mb: int


def _render_error(ctx: _Context, message: str, status: int) -> tuple[str, int]:
    """Renderiza o template inicial com mensagem de erro."""
    return (
        render_template(
            "index.html",
            sources=ctx.sources,
            targets=ctx.targets,
            max_upload_mb=ctx.max_upload_mb,
            error=message,
        ),
        status,
    )


def _parse_options(form) -> tuple[ConversionOptions | None, str | None]:
    """Faz parse das opções do formulário.

    Returns:
        Tupla ``(options, erro)``. Se ``erro`` for ``None``, ``options``
        está preenchido. Caso contrário, ``options`` é ``None``.
    """
    try:
        quality = int(form.get("quality") or 85)
    except ValueError:
        return None, "Qualidade deve ser um número inteiro."
    if not 1 <= quality <= 100:
        return None, "Qualidade deve estar entre 1 e 100."

    resize_raw = (form.get("resize") or "").strip()
    resize: tuple[int, int] | None = None
    if resize_raw:
        try:
            resize = parse_resize(resize_raw)
        except ValueError as exc:
            return None, str(exc)

    return ConversionOptions(quality=quality, resize=resize), None


def _send_single(file: Path) -> Response:
    """Envia um único arquivo gerado como download."""
    buffer = io.BytesIO(file.read_bytes())
    return send_file(
        buffer,
        as_attachment=True,
        download_name=file.name,
        mimetype="application/octet-stream",
    )


def _send_zip(files: list[Path], download_name: str) -> Response:
    """Empacota múltiplos arquivos em ZIP e envia como download."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            zf.write(file, arcname=file.name)
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=download_name,
    )


def _do_conversion(ctx: _Context, uploaded, target_format: str, options: ConversionOptions):
    """Executa a conversão e devolve a resposta (download ou erro)."""
    with tempfile.TemporaryDirectory(prefix="converter-web-") as tmpdir:
        workdir = Path(tmpdir)
        input_dir = workdir / "input"
        output_dir = workdir / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        safe_name = secure_filename(uploaded.filename) or "entrada"
        input_path = input_dir / safe_name
        uploaded.save(input_path)

        output_path = output_dir / f"{Path(safe_name).stem}.{target_format}"

        try:
            ctx.engine.convert_file(input_path, output_path, options)
        except ConverterError as exc:
            return _render_error(ctx, str(exc), status=400)

        produced = sorted(output_dir.iterdir())
        if not produced:
            return _render_error(
                ctx,
                "A conversão não gerou nenhum arquivo. Tente outro formato.",
                status=500,
            )
        if len(produced) == 1:
            return _send_single(produced[0])
        return _send_zip(produced, f"{Path(safe_name).stem}_convertido.zip")


def create_app(max_upload_mb: int = _DEFAULT_MAX_UPLOAD_MB) -> Flask:
    """Cria a aplicação Flask pronta para servir.

    Args:
        max_upload_mb: limite (em MiB) para uploads. Acima disso,
            o servidor retorna 413.
    """
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = max_upload_mb * 1024 * 1024
    engine = build_default_engine()
    ctx = _Context(
        engine=engine,
        sources=sorted(engine.supported_sources()),
        targets=sorted(engine.supported_targets()),
        max_upload_mb=max_upload_mb,
    )

    @app.get("/")
    def index() -> str:
        """Renderiza a página inicial com o formulário de upload."""
        return render_template(
            "index.html",
            sources=ctx.sources,
            targets=ctx.targets,
            max_upload_mb=ctx.max_upload_mb,
            error=None,
        )

    @app.post("/convert")
    def convert():
        """Recebe um arquivo, converte e devolve o resultado para download."""
        uploaded = request.files.get("file")
        target_format = (request.form.get("target_format") or "").strip().lstrip(".")

        if uploaded is None or not uploaded.filename:
            return _render_error(ctx, "Selecione um arquivo para enviar.", status=400)
        if not target_format:
            return _render_error(ctx, "Escolha um formato de destino.", status=400)

        options, err = _parse_options(request.form)
        if err is not None or options is None:
            return _render_error(ctx, err or "Opções inválidas.", status=400)

        return _do_conversion(ctx, uploaded, target_format, options)

    @app.errorhandler(413)
    def _too_large(_exc):
        """Mensagem amigável quando o upload excede o limite."""
        return _render_error(
            ctx,
            f"Arquivo grande demais. Limite atual: {ctx.max_upload_mb} MiB.",
            status=413,
        )

    return app
