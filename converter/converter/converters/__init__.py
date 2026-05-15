"""Pacote de conversores.

Cada conversor implementa o protocolo ``BaseConverter`` e é
registrado no ``core`` para descoberta dinâmica.
"""

from .base import BaseConverter, ConversionOptions
from .document import DocxToPdfConverter, TxtToPdfConverter
from .image import ImageConverter
from .pdf import PdfToImageConverter

__all__ = [
    "BaseConverter",
    "ConversionOptions",
    "DocxToPdfConverter",
    "ImageConverter",
    "PdfToImageConverter",
    "TxtToPdfConverter",
]
