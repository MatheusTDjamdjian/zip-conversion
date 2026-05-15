"""Testes da interface web (Flask)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from converter.web.app import create_app


@pytest.fixture()
def client():
    app = create_app(max_upload_mb=8)
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_index_renders(client) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.data.decode("utf-8")
    assert "converter" in body.lower()
    assert "Converter para" in body


def test_convert_png_to_webp(client, sample_png: Path) -> None:
    with sample_png.open("rb") as fh:
        resp = client.post(
            "/convert",
            data={
                "file": (fh, "imagem.png"),
                "target_format": "webp",
                "quality": "85",
            },
            content_type="multipart/form-data",
        )
    assert resp.status_code == 200
    assert resp.headers["Content-Disposition"].startswith("attachment")
    assert resp.data[:4] == b"RIFF", "Resposta não parece ser um WEBP válido."


def test_convert_with_resize(client, sample_png: Path) -> None:
    from PIL import Image

    with sample_png.open("rb") as fh:
        resp = client.post(
            "/convert",
            data={
                "file": (fh, "imagem.png"),
                "target_format": "png",
                "resize": "32x16",
            },
            content_type="multipart/form-data",
        )
    assert resp.status_code == 200
    with Image.open(io.BytesIO(resp.data)) as img:
        assert img.size == (32, 16)


def test_convert_missing_file_shows_error(client) -> None:
    resp = client.post(
        "/convert",
        data={"target_format": "webp"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert "Selecione um arquivo" in resp.data.decode("utf-8")


def test_convert_missing_target_shows_error(client, sample_png: Path) -> None:
    with sample_png.open("rb") as fh:
        resp = client.post(
            "/convert",
            data={"file": (fh, "imagem.png")},
            content_type="multipart/form-data",
        )
    assert resp.status_code == 400
    assert "formato" in resp.data.decode("utf-8").lower()


def test_convert_invalid_quality(client, sample_png: Path) -> None:
    with sample_png.open("rb") as fh:
        resp = client.post(
            "/convert",
            data={
                "file": (fh, "imagem.png"),
                "target_format": "jpg",
                "quality": "999",
            },
            content_type="multipart/form-data",
        )
    assert resp.status_code == 400
    assert "Qualidade" in resp.data.decode("utf-8")


def test_convert_invalid_resize(client, sample_png: Path) -> None:
    with sample_png.open("rb") as fh:
        resp = client.post(
            "/convert",
            data={
                "file": (fh, "imagem.png"),
                "target_format": "png",
                "resize": "totally-broken",
            },
            content_type="multipart/form-data",
        )
    assert resp.status_code == 400


def test_convert_unsupported_combo(client, sample_png: Path) -> None:
    with sample_png.open("rb") as fh:
        resp = client.post(
            "/convert",
            data={
                "file": (fh, "imagem.png"),
                "target_format": "docx",
            },
            content_type="multipart/form-data",
        )
    assert resp.status_code == 400
    body = resp.data.decode("utf-8")
    assert "suportada" in body.lower() or "suportado" in body.lower()


def test_convert_multipage_pdf_returns_zip(client, tmp_path: Path) -> None:
    """PDF com várias páginas deve voltar empacotado em ZIP."""
    from converter.converters import (
        ConversionOptions,
        TxtToPdfConverter,
    )

    txt = tmp_path / "long.txt"
    txt.write_text("linha\n" * 400, encoding="utf-8")
    pdf_path = tmp_path / "long.pdf"
    TxtToPdfConverter().convert(txt, pdf_path, ConversionOptions())

    with pdf_path.open("rb") as fh:
        resp = client.post(
            "/convert",
            data={
                "file": (fh, "long.pdf"),
                "target_format": "png",
            },
            content_type="multipart/form-data",
        )
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(resp.data)) as zf:
        names = zf.namelist()
    assert len(names) > 1
    assert all(name.endswith(".png") for name in names)
