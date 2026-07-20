"""Configuration for the document converter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ConverterConfig:
    """Filesystem locations and deterministic output-name mappings."""

    source_dir: Path
    output_dir: Path
    output_names: dict[str, str] = field(default_factory=dict)

    @classmethod
    def project_default(cls) -> "ConverterConfig":
        """Build configuration relative to this module's repository location."""
        project_root = Path(__file__).resolve().parents[2]
        return cls(
            source_dir=project_root / "docs" / "product" / "source",
            output_dir=project_root / "docs" / "product" / "markdown",
            output_names={
                "01_PRD_YT_Signal_Scout.docx": "PRD.md",
                "02_TRD_YT_Signal_Scout.docx": "TRD.md",
                "03_UI_UX_Spec_YT_Signal_Scout.docx": "UI_UX.md",
                "04_Security_Spec_YT_Signal_Scout.docx": "SECURITY.md",
                "05_Feature_Catalogue_YT_Signal_Scout.docx": "FEATURE_CATALOGUE.md",
            },
        )
