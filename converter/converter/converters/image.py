"""Conversão entre formatos de imagem usando Pillow."""

from __future__ import annotations

from pathlib import Path

from ..exceptions import ConversionError
from ..utils import get_logger
from .base import BaseConverter, ConversionOptions

_FORMATS = frozenset({"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "tif"})

_EXTENSION_TO_PILLOW = {
    "png": "PNG",
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "webp": "WEBP",
    "bmp": "BMP",
    "gif": "GIF",
    "tiff": "TIFF",
    "tif": "TIFF",
}


class ImageConverter(BaseConverter):
    """Conversor de imagens entre PNG, JPG, WEBP, BMP, GIF e TIFF.

    Aplica redimensionamento opcional e qualidade configurável para
    formatos com compressão lossy (JPEG/WEBP).
    """

    source_formats = _FORMATS
    target_formats = _FORMATS

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        options: ConversionOptions,
    ) -> Path:
        try:
            from PIL import Image
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
            with Image.open(input_path) as img:
                img.load()
                logger.debug(
                    "Imagem aberta: %s (%sx%s, modo %s)",
                    input_path.name,
                    img.width,
                    img.height,
                    img.mode,
                )

                if options.resize is not None:
                    img = img.resize(options.resize, Image.Resampling.LANCZOS)
                    logger.debug("Redimensionada para %sx%s", *options.resize)

                if pillow_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
                    img = background
                elif pillow_format == "BMP" and img.mode == "RGBA":
                    img = img.convert("RGB")

                save_kwargs: dict[str, object] = {}
                if pillow_format in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = options.quality
                if pillow_format == "JPEG":
                    save_kwargs["optimize"] = True

                img.save(output_path, format=pillow_format, **save_kwargs)
        except FileNotFoundError as exc:
            raise ConversionError(f"Não foi possível abrir '{input_path}'.") from exc
        except OSError as exc:
            raise ConversionError(
                f"Erro ao processar a imagem '{input_path.name}': {exc}. "
                "O arquivo pode estar corrompido ou ser de um formato não reconhecido."
            ) from exc

        logger.debug("Imagem salva em: %s", output_path)
        return output_path
