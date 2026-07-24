# Governed Study Execution Contract

Study Execution schema version 1 defines the deterministic, non-analytical boundary for one
offline research study.

## Inputs

`StudyExecutionRequest` contains a unique execution identity, caller-supplied chronological
timezone-aware request/start/completion timestamps, one `StudyDefinition`, and one
`StudyInputBundle`. The bundle contains exactly one:

- Historical Dataset import result (schema 2);
- canonically ordered Evidence Pack collection (schema 1), with exactly one pack per observation;
- Labelling Rubric import result (schema 1);
- Ground Truth Label Set import result (schema 1), with exactly one label per observation; and
- Study Configuration.

The configuration pins all supported input schema versions. The definition binds its exact
configuration identity/version and a versioned research protocol.

## Output

`StudyExecutionResult` contains:

- factual execution and study metadata;
- a context identifying dataset, evidence definition, rubric, labels, configuration, and cohort
  counts; and
- a manifest carrying every governed content digest plus a canonical result digest.

It deliberately contains no analytical report or interpreted result.

## Canonical serialization

`StudyExecutionCanonicalizer.serialize_result()` emits UTF-8 JSON with lexicographically sorted
object keys, no insignificant whitespace, Unicode retained, arrays retained in governed order, and
non-finite numbers rejected. The result SHA-256 excludes only its own digest field and covers the
complete metadata, context, and remaining manifest.

## Failure behavior

Unknown or missing typed fields fail Pydantic validation. `StudyExecutionValidationError` rejects
identity, observation, binding, schema, ordering, duplicate, or digest mismatches.
`StudyExecutionDigestMismatchError` rejects altered serialized execution content. Validation is
all-or-nothing and returns no partial result.

The service performs no file I/O and has no execution importer. Existing governed artifact
importers remain the sole JSON trust boundaries for dataset, evidence, rubric, and labels.

