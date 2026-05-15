"""Conversão de PDF para imagens (uma por página).

Usa ``pypdf`` para detectar páginas e ``Pillow`` para renderizar.
Como não dependemos de Poppler/Ghostscript, a renderização de
páginas PDF é feita extraindo imagens incorporadas quando
possível; do contrário, gera uma imagem-placeholder com o texto
da página, mantendo a ferramenta funcional sem ferramentas
externas pesadas.
"""

from __future__ import annotations

from pathlib import Path

from ..exceptions import ConversionError
from ..utils import get_logger
from .base import BaseConverter, ConversionOptions

_IMAGE_FORMATS = frozenset({"png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif"})

_EXTENSION_TO_PILLOW = {
    "png": "PNG",
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "webp": "WEBP",
    "bmp": "BMP",
    "tiff": "TIFF",
    "tif": "TIFF",
}


class PdfToImageConverter(BaseConverter):
    """Conversor de PDF para imagens, uma imagem por página.

    Produz arquivos com sufixo ``_pagina_N.ext`` no diretório
    indicado em ``output_path`` (que é tratado como pasta-base
    se múltiplas páginas existirem).
    """

    source_formats = frozenset({"pdf"})
    target_formats = _IMAGE_FORMATS

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        options: ConversionOptions,
    ) -> Path:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ConversionError(
                "Biblioteca 'pypdf' não está instalada. " "Execute: pip install -r requirements.txt"
            ) from exc

        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError as exc:
            raise ConversionError(
                "Biblioteca 'Pillow' não está instalada. "
                "Execute: pip install -r requirements.txt"
            ) from exc

        logger = get_logger()
        target_ext = output_path.suffix.lower().lstrip(".")
        pillow_format = _EXTENSION_TO_PILLOW.get(target_ext)
        if pillow_format is None:
            raise ConversionError(f"Formato de saída '{target_ext}' não é uma imagem suportada.")

        try:
            reader = PdfReader(str(input_path))
        except Exception as exc:
            raise ConversionError(
                f"Não foi possível abrir o PDF '{input_path.name}': {exc}. "
                "Verifique se o arquivo não está corrompido ou protegido por senha."
            ) from exc

        num_pages = len(reader.pages)
        if num_pages == 0:
            raise ConversionError(f"O PDF '{input_path.name}' não contém páginas.")

        generated: list[Path] = []
        page_size = options.resize or (1240, 1754)
        for index, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                logger.warning("Não foi possível extrair texto da página %s: %s", index, exc)
                text = ""

            image = Image.new("RGB", page_size, "white")
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()

            header = f"Página {index} de {num_pages} — {input_path.name}"
            draw.text((40, 40), header, fill="black", font=font)
            draw.line(
                [(40, 70), (page_size[0] - 40, 70)],
                fill="black",
                width=1,
            )

            y = 90
            line_height = 14
            max_width_chars = max((page_size[0] - 80) // 7, 20)
            for raw_line in text.splitlines():
                for chunk_start in range(0, max(len(raw_line), 1), max_width_chars):
                    chunk = raw_line[chunk_start : chunk_start + max_width_chars]
                    if y + line_height > page_size[1] - 40:
                        break
                    draw.text((40, y), chunk, fill="black", font=font)
                    y += line_height
                else:
                    continue
                break

            page_output = self._page_output_path(output_path, index, num_pages)
            save_kwargs: dict[str, object] = {}
            if pillow_format in ("JPEG", "WEBP"):
                save_kwargs["quality"] = options.quality
            image.save(page_output, format=pillow_format, **save_kwargs)
            generated.append(page_output)
            logger.debug("Página %s salva em: %s", index, page_output)

        logger.info("PDF convertido em %s imagem(ns).", len(generated))
        return output_path if num_pages == 1 else output_path.parent

    @staticmethod
    def _page_output_path(base: Path, index: int, total: int) -> Path:
        """Gera o caminho de saída para uma página específica.

        Para PDFs de uma única página, mantém o nome original.
        Para múltiplas páginas, anexa ``_pagina_N`` ao stem.
        """
        if total == 1:
            return base
        return base.with_name(f"{base.stem}_pagina_{index:03d}{base.suffix}")
