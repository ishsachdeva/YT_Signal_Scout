"""DOCX-to-Markdown conversion orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import mammoth

from .config import ConverterConfig
from .utils import clean_markdown, discover_docx_files, output_name_for
from .validator import validate_conversion


@dataclass(frozen=True)
class ConversionResult:
    """Outcome for one source document."""

    source: Path
    output: Path | None
    warnings: tuple[str, ...] = ()
    error: str | None = None


def convert_document(
    source_path: Path,
    output_path: Path,
    logger: logging.Logger,
) -> ConversionResult:
    """Convert and validate one document, capturing failures for the summary."""
    try:
        logger.info("Converting %s", source_path.name)
        with source_path.open("rb") as source_file:
            converted = mammoth.convert_to_markdown(
                source_file,
                style_map=[
                    "p[style-name='Code'] => pre:separator('\\n')",
                    "p[style-name='Source Code'] => pre:separator('\\n')",
                ],
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(clean_markdown(converted.value), encoding="utf-8", newline="\n")

        warnings = [
            f"{source_path.name}: {message.message}"
            for message in converted.messages
            if message.type == "warning"
        ]
        warnings.extend(validate_conversion(source_path, output_path).warnings)
        return ConversionResult(source_path, output_path, tuple(warnings))
    except Exception as exc:  # A per-file failure must not hide results for other files.
        logger.exception("Failed to convert %s", source_path.name)
        return ConversionResult(source_path, None, error=f"{source_path.name}: {exc}")


def convert_all(config: ConverterConfig, logger: logging.Logger) -> list[ConversionResult]:
    """Convert every DOCX file using stable discovery and naming."""
    sources = discover_docx_files(config.source_dir)
    if not sources:
        logger.warning("No DOCX files found in %s", config.source_dir)
        return []

    results: list[ConversionResult] = []
    for source in sources:
        output_name = output_name_for(source, config.output_names)
        results.append(convert_document(source, config.output_dir / output_name, logger))
    return results
