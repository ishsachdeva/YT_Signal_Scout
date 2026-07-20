"""Deterministic DOCX-to-Markdown conversion utilities."""

from .config import ConverterConfig
from .converter import ConversionResult, convert_all, convert_document

__all__ = [
    "ConversionResult",
    "ConverterConfig",
    "convert_all",
    "convert_document",
]
