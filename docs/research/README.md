# Research Documentation

This directory contains canonical, analytics-owned research methods. Research documents define
how evidence is produced and reviewed; they do not approve Product policy, change architecture,
or authorize runtime behavior.

## Canonical protocols

- [SIG-002 Research Protocol](SIG-002_RESEARCH_PROTOCOL.md) defines the reproducible dataset,
  labelling, threshold-evaluation, boundary-testing, artifact, and acceptance methodology for all
  SIG-002 threshold studies.
- [Governed Study Execution Contract](../engineering/STUDY_EXECUTION_FORMAT.md) defines the
  deterministic input-validation and non-analytical execution boundary used before later research
  analysis.
- [Labelled Evaluation Contract](../engineering/LABELLED_EVALUATION_FORMAT.md) defines the factual
  per-observation comparison boundary used before any statistical aggregation.

Study-specific datasets, configurations, executions, reports, labels, and reviews are not stored
here unless a separately approved milestone explicitly adds them.
