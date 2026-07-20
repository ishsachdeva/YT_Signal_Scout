"""Small shared helpers for conversion and reporting."""

from __future__ import annotations

import re
from pathlib import Path


def discover_docx_files(source_dir: Path) -> list[Path]:
    """Return DOCX files in a stable, case-insensitive order."""
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")
    return sorted(
        (path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() == ".docx"),
        key=lambda path: path.name.casefold(),
    )


def output_name_for(source: Path, configured_names: dict[str, str]) -> str:
    """Return a configured name or a stable generic name for a new document."""
    if source.name in configured_names:
        return configured_names[source.name]

    stem = re.sub(r"^\d+[_\-\s]*", "", source.stem)
    stem = re.sub(r"_YT_Signal_Scout$", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"_Spec$", "", stem, flags=re.IGNORECASE)
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_").upper()
    if not normalized:
        raise ValueError(f"Cannot derive an output name from: {source.name}")
    return f"{normalized}.md"


def clean_markdown(markdown: str) -> str:
    """Normalize line endings and trailing whitespace without changing content."""
    normalized = markdown.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip() + "\n"
