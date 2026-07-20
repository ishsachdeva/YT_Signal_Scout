# Document Converter

Version 1 converts every DOCX file in `docs/product/source/` to clean Markdown in
`docs/product/markdown/`. DOCX files remain the source of truth; generated Markdown is
overwritten on each run.

## Installation

From the repository root, create or activate a Python 3.10+ virtual environment, then run:

```text
python -m pip install -r tools/document_converter/requirements.txt
```

## Usage

Run from the converter directory as requested:

```text
cd tools/document_converter
python convert.py
```

The script logs each conversion and prints converted files, warnings, and errors. It returns
a non-zero exit code if any document fails. Validation findings are warnings and do not change
the exit code.

## Directory layout

```text
docs/product/source/       Source-of-truth DOCX files
docs/product/markdown/     Generated Markdown files
tools/document_converter/  Converter source and dependencies
```

## How conversion works

Files are discovered in a deterministic, case-insensitive filename order. Mammoth converts
Word's semantic structure to Markdown, including headings, lists, tables, links, bold text,
and italic text. Paragraphs using Word's `Code` or `Source Code` style are mapped to code
blocks. Output line endings and trailing whitespace are normalized before the Markdown file
is overwritten.

After each conversion, `python-docx` checks whether the source contains tables. The validator
also checks that the output exists, is non-empty, contains a heading, and contains a Markdown
table when the DOCX contains tables. Findings are printed as warnings; conversion exceptions
are printed as errors and never silently ignored.

The five current documents have explicit output names:

| Source | Output |
| --- | --- |
| `01_PRD_YT_Signal_Scout.docx` | `PRD.md` |
| `02_TRD_YT_Signal_Scout.docx` | `TRD.md` |
| `03_UI_UX_Spec_YT_Signal_Scout.docx` | `UI_UX.md` |
| `04_Security_Spec_YT_Signal_Scout.docx` | `SECURITY.md` |
| `05_Feature_Catalogue_YT_Signal_Scout.docx` | `FEATURE_CATALOGUE.md` |

## Limitations

- Conversion quality depends on semantic Word styles. Visual-only formatting may be lost.
- Complex or merged tables may require manual review after conversion.
- Code blocks are detected only when paragraphs use the `Code` or `Source Code` style.
- Images and document-specific layout are not managed by Version 1.
- The table validator confirms Markdown table syntax, not cell-for-cell equivalence.

## Adding a new document

Add a `.docx` file to `docs/product/source/` and run the converter. For an unlisted file, the
tool removes a leading numeric prefix, the `_YT_Signal_Scout` suffix, and a trailing `_Spec`,
then creates an uppercase underscore-separated Markdown name. For example,
`06_Operations_Spec_YT_Signal_Scout.docx` becomes `OPERATIONS.md`. If a precise name is
required, add an entry to `output_names` in `config.py`.
