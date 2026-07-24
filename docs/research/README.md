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
- [Evaluation Aggregation Contract](../engineering/EVALUATION_AGGREGATION_FORMAT.md) defines the
  counts-only cohort boundary used before derived statistical metrics.
- [Statistical Evaluation Contract](../engineering/STATISTICAL_EVALUATION_FORMAT.md) defines the
  complete approved mathematical artifact without interpretation or candidate comparison.
- [Research Architecture Stabilization Audit](../engineering/RESEARCH_ARCHITECTURE_STABILIZATION.md)
  records the verified end-to-end pipeline state and synthetic integrity coverage.

Study-specific datasets, configurations, executions, reports, labels, and reviews are not stored
here unless a separately approved milestone explicitly adds them.
