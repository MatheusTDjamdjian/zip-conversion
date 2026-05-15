"""Conversão de documentos: DOCX→PDF e TXT→PDF.

A geração de PDF é feita manualmente, escrevendo a estrutura
mínima de um PDF válido (objetos, xref, trailer) usando apenas
a biblioteca padrão. Isso evita dependências pesadas como
ReportLab e mantém a ferramenta leve e portável.
"""

from __future__ import annotations

import zlib
from pathlib import Path

from ..exceptions import ConversionError
from ..utils import get_logger
from .base import BaseConverter, ConversionOptions


class _SimplePdfWriter:
    """Escritor minimalista de PDF usando apenas a biblioteca padrão.

    Suporta texto em fonte Helvetica com quebra automática em páginas.
    Não pretende substituir bibliotecas completas — apenas atender
    casos simples (TXT→PDF, DOCX→PDF) sem dependências extras.
    """

    PAGE_WIDTH = 595
    PAGE_HEIGHT = 842
    MARGIN_LEFT = 50
    MARGIN_TOP = 50
    MARGIN_BOTTOM = 50
    FONT_SIZE = 11
    LINE_HEIGHT = 14
    CHARS_PER_LINE = 90

    def __init__(self) -> None:
        self._pages_content: list[str] = []

    def add_text(self, text: str) -> None:
        """Adiciona texto, gerando novas páginas conforme necessário."""
        if not text:
            text = ""
        lines = self._wrap_lines(text)
        max_lines_per_page = (
            self.PAGE_HEIGHT - self.MARGIN_TOP - self.MARGIN_BOTTOM
        ) // self.LINE_HEIGHT

        for start in range(0, max(len(lines), 1), max_lines_per_page):
            chunk = lines[start : start + max_lines_per_page] or [""]
            self._pages_content.append(self._build_page_stream(chunk))

    def write(self, path: Path) -> None:
        """Escreve o PDF montado para ``path``."""
        if not self._pages_content:
            self._pages_content.append(self._build_page_stream([""]))

        objects: list[bytes] = []

        catalog_id = 1
        pages_id = 2
        font_id = 3
        first_page_id = 4

        page_ids = list(range(first_page_id, first_page_id + 2 * len(self._pages_content), 2))

        objects.append(
            self._format_object(
                catalog_id,
                b"<< /Type /Catalog /Pages " + f"{pages_id} 0 R".encode() + b" >>",
            )
        )

        kids = b" ".join(f"{pid} 0 R".encode() for pid in page_ids)
        objects.append(
            self._format_object(
                pages_id,
                b"<< /Type /Pages /Count "
                + str(len(self._pages_content)).encode()
                + b" /Kids ["
                + kids
                + b"] /MediaBox [0 0 "
                + str(self.PAGE_WIDTH).encode()
                + b" "
                + str(self.PAGE_HEIGHT).encode()
                + b"] >>",
            )
        )

        objects.append(
            self._format_object(
                font_id,
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            )
        )

        for index, stream in enumerate(self._pages_content):
            page_obj_id = page_ids[index]
            content_obj_id = page_obj_id + 1

            objects.append(
                self._format_object(
                    page_obj_id,
                    b"<< /Type /Page /Parent "
                    + f"{pages_id} 0 R".encode()
                    + b" /Resources << /Font << /F1 "
                    + f"{font_id} 0 R".encode()
                    + b" >> >> /Contents "
                    + f"{content_obj_id} 0 R".encode()
                    + b" >>",
                )
            )

            compressed = zlib.compress(stream.encode("latin-1", errors="replace"))
            content_dict = (
                b"<< /Filter /FlateDecode /Length " + str(len(compressed)).encode() + b" >>"
            )
            objects.append(
                self._format_object(
                    content_obj_id,
                    content_dict + b"\nstream\n" + compressed + b"\nendstream",
                )
            )

        objects.sort(key=lambda chunk: int(chunk.split(b" ", 1)[0]))

        with path.open("wb") as fh:
            fh.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            offsets: list[int] = [0]
            for obj in objects:
                offsets.append(fh.tell())
                fh.write(obj)
                fh.write(b"\n")

            xref_offset = fh.tell()
            fh.write(b"xref\n")
            fh.write(f"0 {len(offsets)}\n".encode())
            fh.write(b"0000000000 65535 f \n")
            for offset in offsets[1:]:
                fh.write(f"{offset:010d} 00000 n \n".encode())

            fh.write(b"trailer\n")
            fh.write(
                b"<< /Size "
                + str(len(offsets)).encode()
                + b" /Root "
                + f"{catalog_id} 0 R".encode()
                + b" >>\n"
            )
            fh.write(b"startxref\n")
            fh.write(f"{xref_offset}\n".encode())
            fh.write(b"%%EOF\n")

    def _wrap_lines(self, text: str) -> list[str]:
        """Quebra cada linha em segmentos de tamanho fixo."""
        result: list[str] = []
        for raw in text.splitlines() or [""]:
            if not raw:
                result.append("")
                continue
            for start in range(0, len(raw), self.CHARS_PER_LINE):
                result.append(raw[start : start + self.CHARS_PER_LINE])
        return result

    def _build_page_stream(self, lines: list[str]) -> str:
        """Monta o stream de conteúdo PDF para uma página."""
        y = self.PAGE_HEIGHT - self.MARGIN_TOP
        parts = ["BT", f"/F1 {self.FONT_SIZE} Tf", f"{self.LINE_HEIGHT} TL"]
        parts.append(f"{self.MARGIN_LEFT} {y} Td")
        for index, line in enumerate(lines):
            escaped = self._escape_pdf_string(line)
            if index == 0:
                parts.append(f"({escaped}) Tj")
            else:
                parts.append("T*")
                parts.append(f"({escaped}) Tj")
        parts.append("ET")
        return "\n".join(parts)

    @staticmethod
    def _escape_pdf_string(text: str) -> str:
        """Escapa caracteres reservados em strings PDF."""
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    @staticmethod
    def _format_object(obj_id: int, body: bytes) -> bytes:
        """Formata um objeto PDF indireto."""
        return f"{obj_id} 0 obj\n".encode() + body + b"\nendobj"


class TxtToPdfConverter(BaseConverter):
    """Conversor de TXT para PDF, preservando quebras de linha."""

    source_formats = frozenset({"txt"})
    target_formats = frozenset({"pdf"})

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        options: ConversionOptions,
    ) -> Path:
        del options
        logger = get_logger()
        try:
            text = input_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = input_path.read_text(encoding="latin-1")
                logger.debug("Texto lido com fallback latin-1.")
            except OSError as exc:
                raise ConversionError(f"Falha ao ler '{input_path.name}': {exc}.") from exc
        except OSError as exc:
            raise ConversionError(f"Falha ao ler '{input_path.name}': {exc}.") from exc

        writer = _SimplePdfWriter()
        writer.add_text(text)
        try:
            writer.write(output_path)
        except OSError as exc:
            raise ConversionError(f"Falha ao escrever PDF em '{output_path}': {exc}.") from exc

        logger.debug("TXT convertido em PDF: %s", output_path)
        return output_path


class DocxToPdfConverter(BaseConverter):
    """Conversor simples de DOCX para PDF, preservando texto puro.

    Não tenta reproduzir formatação avançada (estilos, tabelas
    complexas, imagens). Para isso, recomende ao usuário utilizar
    o LibreOffice em linha de comando como pós-processamento.
    """

    source_formats = frozenset({"docx"})
    target_formats = frozenset({"pdf"})

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        options: ConversionOptions,
    ) -> Path:
        del options
        try:
            from docx import Document
        except ImportError as exc:
            raise ConversionError(
                "Biblioteca 'python-docx' não está instalada. "
                "Execute: pip install -r requirements.txt"
            ) from exc

        logger = get_logger()
        try:
            document = Document(str(input_path))
        except Exception as exc:
            raise ConversionError(
                f"Não foi possível abrir '{input_path.name}': {exc}. "
                "Verifique se o arquivo é um DOCX válido."
            ) from exc

        paragraphs = [p.text for p in document.paragraphs]
        text = "\n".join(paragraphs)

        writer = _SimplePdfWriter()
        writer.add_text(text)
        try:
            writer.write(output_path)
        except OSError as exc:
            raise ConversionError(f"Falha ao escrever PDF em '{output_path}': {exc}.") from exc

        logger.debug("DOCX convertido em PDF: %s", output_path)
        return output_path
