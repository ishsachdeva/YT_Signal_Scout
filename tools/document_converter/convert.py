"""Command-line entry point for converting product documentation."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from document_converter.config import ConverterConfig
from document_converter.converter import ConversionResult, convert_all


def _print_summary(results: list[ConversionResult]) -> None:
    converted = [result for result in results if result.error is None and result.output]
    warnings = [warning for result in results for warning in result.warnings]
    errors = [result.error for result in results if result.error]

    print("Converted:")
    if converted:
        success_marker = _supported_success_marker()
        for result in converted:
            print(f"{success_marker} {result.output.name}")
    else:
        print("(none)")

    print(f"\nWarnings:\n{len(warnings)}")
    for warning in warnings:
        print(f"- {warning}")

    print(f"\nErrors:\n{len(errors)}")
    for error in errors:
        print(f"- {error}")


def _supported_success_marker() -> str:
    """Use a checkmark when supported, with a safe legacy-console fallback."""
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "✓".encode(encoding)
    except UnicodeEncodeError:
        return "[OK]"
    return "✓"


def main() -> int:
    """Run conversion and return a process exit code."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger("document_converter")

    try:
        results = convert_all(ConverterConfig.project_default(), logger)
    except Exception as exc:
        logger.error("Conversion could not start: %s", exc)
        _print_summary([ConversionResult(Path("."), None, error=str(exc))])
        return 1

    _print_summary(results)
    return 1 if any(result.error for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
