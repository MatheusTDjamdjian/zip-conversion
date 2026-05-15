"""Fixtures compartilhadas para a suíte de testes.

Geram arquivos de exemplo (pequenos) em tempo de execução para
não inflar o repositório. Quando uma fixture estática é necessária
(ex.: DOCX), ela mora em ``tests/fixtures/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def sample_png(tmp_path: Path) -> Path:
    """Cria um PNG 4x4 colorido em ``tmp_path``."""
    from PIL import Image

    path = tmp_path / "sample.png"
    img = Image.new("RGB", (4, 4), color=(255, 100, 50))
    img.save(path, format="PNG")
    return path


@pytest.fixture()
def sample_rgba_png(tmp_path: Path) -> Path:
    """Cria um PNG 4x4 com canal alfa em ``tmp_path``."""
    from PIL import Image

    path = tmp_path / "rgba.png"
    img = Image.new("RGBA", (4, 4), color=(255, 100, 50, 128))
    img.save(path, format="PNG")
    return path


@pytest.fixture()
def sample_txt(tmp_path: Path) -> Path:
    """Cria um arquivo TXT pequeno em ``tmp_path``."""
    path = tmp_path / "documento.txt"
    path.write_text(
        "Linha 1: relatório de teste.\n" "Linha 2: acentuação ãéíóú çÇ.\n" "Linha 3: fim.\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def sample_pdf(tmp_path: Path, sample_txt: Path) -> Path:
    """Gera um PDF simples a partir de um TXT usando o próprio TxtToPdfConverter."""
    from converter.converters import ConversionOptions, TxtToPdfConverter

    pdf_path = tmp_path / "documento.pdf"
    TxtToPdfConverter().convert(sample_txt, pdf_path, ConversionOptions())
    return pdf_path


@pytest.fixture()
def sample_docx(tmp_path: Path) -> Path:
    """Cria um DOCX mínimo em ``tmp_path``."""
    from docx import Document

    path = tmp_path / "documento.docx"
    doc = Document()
    doc.add_paragraph("Parágrafo 1: teste de DOCX.")
    doc.add_paragraph("Parágrafo 2: com acentuação.")
    doc.save(str(path))
    return path
