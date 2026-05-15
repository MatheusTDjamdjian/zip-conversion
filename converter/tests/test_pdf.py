"""Testes para conversores envolvendo PDF."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from converter.converters import (
    ConversionOptions,
    DocxToPdfConverter,
    PdfToImageConverter,
    TxtToPdfConverter,
)
from converter.exceptions import ConversionError


def test_txt_to_pdf_creates_valid_file(sample_txt: Path, tmp_path: Path) -> None:
    output = tmp_path / "doc.pdf"
    TxtToPdfConverter().convert(sample_txt, output, ConversionOptions())
    assert output.exists()
    data = output.read_bytes()
    assert data.startswith(b"%PDF-"), "Arquivo gerado não começa com cabeçalho PDF."
    assert b"%%EOF" in data


def test_docx_to_pdf_creates_valid_file(sample_docx: Path, tmp_path: Path) -> None:
    output = tmp_path / "doc.pdf"
    DocxToPdfConverter().convert(sample_docx, output, ConversionOptions())
    assert output.exists()
    assert output.read_bytes().startswith(b"%PDF-")


def test_pdf_to_png_single_page(sample_pdf: Path, tmp_path: Path) -> None:
    output = tmp_path / "page.png"
    PdfToImageConverter().convert(sample_pdf, output, ConversionOptions())
    assert output.exists()
    with Image.open(output) as img:
        assert img.format == "PNG"


def test_pdf_to_image_with_resize(sample_pdf: Path, tmp_path: Path) -> None:
    output = tmp_path / "page.png"
    PdfToImageConverter().convert(sample_pdf, output, ConversionOptions(resize=(400, 600)))
    with Image.open(output) as img:
        assert img.size == (400, 600)


def test_invalid_pdf_raises(tmp_path: Path) -> None:
    bogus = tmp_path / "fake.pdf"
    bogus.write_bytes(b"not a pdf")
    with pytest.raises(ConversionError):
        PdfToImageConverter().convert(bogus, tmp_path / "out.png", ConversionOptions())


def test_txt_with_latin1_fallback(tmp_path: Path) -> None:
    src = tmp_path / "weird.txt"
    src.write_bytes("Olá mundo".encode("latin-1"))
    output = tmp_path / "weird.pdf"
    TxtToPdfConverter().convert(src, output, ConversionOptions())
    assert output.exists()


def test_pdf_converter_supports_matrix() -> None:
    conv = PdfToImageConverter()
    assert conv.supports("pdf", "png")
    assert conv.supports("pdf", "webp")
    assert not conv.supports("pdf", "docx")


def test_txt_converter_supports_matrix() -> None:
    conv = TxtToPdfConverter()
    assert conv.supports("txt", "pdf")
    assert not conv.supports("txt", "png")


def test_docx_converter_supports_matrix() -> None:
    conv = DocxToPdfConverter()
    assert conv.supports("docx", "pdf")
    assert not conv.supports("doc", "pdf")
