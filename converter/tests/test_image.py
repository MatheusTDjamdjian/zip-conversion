"""Testes do conversor de imagens."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from converter.converters import ConversionOptions, ImageConverter
from converter.exceptions import ConversionError


def test_png_to_jpeg(sample_png: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.jpg"
    ImageConverter().convert(sample_png, output, ConversionOptions(quality=90))
    assert output.exists()
    with Image.open(output) as img:
        assert img.format == "JPEG"
        assert img.size == (4, 4)


def test_png_to_webp(sample_png: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.webp"
    ImageConverter().convert(sample_png, output, ConversionOptions(quality=80))
    assert output.exists()
    with Image.open(output) as img:
        assert img.format == "WEBP"


def test_png_to_bmp(sample_png: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.bmp"
    ImageConverter().convert(sample_png, output, ConversionOptions())
    assert output.exists()
    with Image.open(output) as img:
        assert img.format == "BMP"


def test_png_to_gif(sample_png: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.gif"
    ImageConverter().convert(sample_png, output, ConversionOptions())
    assert output.exists()
    with Image.open(output) as img:
        assert img.format == "GIF"


def test_png_to_tiff(sample_png: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.tiff"
    ImageConverter().convert(sample_png, output, ConversionOptions())
    assert output.exists()
    with Image.open(output) as img:
        assert img.format == "TIFF"


def test_resize_option(sample_png: Path, tmp_path: Path) -> None:
    output = tmp_path / "resized.png"
    ImageConverter().convert(sample_png, output, ConversionOptions(resize=(16, 8)))
    with Image.open(output) as img:
        assert img.size == (16, 8)


def test_rgba_to_jpeg_flattens(sample_rgba_png: Path, tmp_path: Path) -> None:
    output = tmp_path / "flat.jpg"
    ImageConverter().convert(sample_rgba_png, output, ConversionOptions())
    with Image.open(output) as img:
        assert img.format == "JPEG"
        assert img.mode == "RGB"


def test_invalid_image_raises_conversion_error(tmp_path: Path) -> None:
    bogus = tmp_path / "fake.png"
    bogus.write_bytes(b"not really an image")
    with pytest.raises(ConversionError):
        ImageConverter().convert(bogus, tmp_path / "out.jpg", ConversionOptions())


def test_supports_matrix() -> None:
    converter = ImageConverter()
    assert converter.supports("png", "jpg")
    assert converter.supports("webp", "bmp")
    assert not converter.supports("pdf", "png")
