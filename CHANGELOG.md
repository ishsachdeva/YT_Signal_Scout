# Changelog

This file records user-visible and architectural changes to YT Signal Scout by release.

## Unreleased

### Added

- Governed Evaluation Aggregation schema version 1 with immutable definitions, configuration,
  requests, counts-only summaries, metadata, manifests, and results.
- Deterministic counting of all six observation-level outcomes with exact total invariants,
  source-evaluation validation, and canonical SHA-256 result integrity.

### Release boundaries

- No aggregation was run on real research data and no percentage, rate, statistical metric,
  threshold recommendation, Product decision, persistence, API, workflow, or runtime behavior was
  created.

## 0.9.6 - 2026-07-24

### Added

- Deterministic Labelled Evaluation schema version 1 with immutable definitions, configuration,
  predictions, per-observation outcomes, metadata, manifests, and results.
- Exact cohort, dataset, execution, ground-truth, ordering, vocabulary, version, and digest
  validation plus canonical SHA-256 result serialization.

### Release boundaries

- No evaluation was executed and no aggregate, metric, confusion-matrix total, threshold,
  recommendation, Product decision, persistence, API, workflow, or runtime behavior was created.

## 0.9.5 - 2026-07-24

### Added

- Governed Study Definition and Execution schema version 1 with immutable configuration, input
  bundle, request, metadata, context, manifest, and result contracts.
- Pure synchronous study orchestration with cohort-wide dataset, observation, evidence, rubric,
  ground-truth, schema-version, digest, canonical-order, and identity validation.
- Canonical UTF-8 serialization and SHA-256 integrity for immutable execution results.

### Release boundaries

- No study was executed and no threshold, metric, statistic, recommendation, Product decision,
  persistence, API, workflow, or runtime behavior was created.

## 0.9.4 - 2026-07-24

### Added

- Canonical SIG-002 Research Protocol covering governed datasets, independent channel labels,
  deterministic classification metrics, Wilson intervals, sensitivity and boundary testing,
  immutable study artifacts, acceptance criteria, and the Product evidence boundary.
- Historical Dataset JSON schema version 2 with immutable custody and collection provenance,
  observation-cutoff validation, canonical UTF-8 serialization, SHA-256 integrity verification,
  and typed digest failures.
- Corrected release-governance contracts so production eligibility depends on an approved
  versioned Product decision and required release reviews, never manual runtime authorization.
- Immutable Ground Truth Label schema version 1 with dataset/evidence binding, two independent
  reviews, disagreement adjudication, supersession history, canonical serialization, strict import,
  SHA-256 integrity, and typed failures.
- Immutable Evidence Pack and Labelling Rubric schema version 1 contracts with typed reviewer
  facts, exact snapshot and definition binding, closed decision states and reason codes, strict
  canonical import, SHA-256 integrity, and ground-truth label reference validation.

### Release boundaries

- No research was executed and no dataset, labels, study report, or threshold recommendation was
  created.
- SIG-002 remains blocked; no production threshold or production runtime behavior changed.
- No historical dataset was created or imported, and no research execution or labelling occurred.
- No ground-truth label artifact was created and no channel was labelled.
- No evidence pack, rubric instance, label, dataset, or research result was created or generated.

## 0.6.0 - 2026-07-22

### Added

- Immutable video-acquisition results with discovery, enrichment, omission, and pagination
  provenance.
- Deterministic eligible-video classification and subscriber-relative dataset qualification with
  typed failure reasons.
- Subscriber-relative analytics for eligible standard-video count and median view-to-subscriber
  ratio, returned with qualification in `SubscriberRelativeAnalysisResult`.
- Immutable, policy-free `SignalEvidenceBundle` construction for qualified and unqualified
  subscriber-relative analysis facts.
- Offline deterministic subscriber-band and median-VSR threshold backtesting with versioned
  research configuration, typed exclusions, factual distributions, and immutable reports.

### Changed

- Video search and uploads acquisition now retain canonical unique-video populations and complete
  typed provenance alongside source-ordered resolved discovery positions.
- Subscriber-relative processing now keeps acquisition, eligibility, qualification, calculation,
  evidence construction, and offline research as separate deterministic responsibilities.

### Release boundaries

- No production signal rule is approved, registered, or emitted in this release.
- SIG-002 remains blocked pending a governed historical dataset, threshold research, and explicit
  Product and Analytics approval.
- Offline backtesting evaluates supplied candidate configurations but never selects or recommends
  a production threshold.
