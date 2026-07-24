# Changelog

This file records user-visible and architectural changes to YT Signal Scout by release.

## Unreleased

### Opportunity Candidate Domain Foundation

- Added an immutable schema-versioned pre-qualification Candidate containing only discovery-source,
  ordered evidence-reference, UTC acquisition-time, and ordered provenance-reference facts.
- Added strict primitive, version, timestamp, enum, duplicate-reference, canonical JSON, SHA-256,
  hashability, dependency-isolation, and golden contract coverage under PD-010 and ADR-032.

### Release boundaries

- No Candidate registry, discovery, acquisition integration, evidence interpretation, qualification,
  promotion, lifecycle, score, rank, confidence, recommendation, persistence, API, workflow, AI, or
  application-startup behavior was added.

### Canonical Opportunity Domain Foundation

- Added an immutable schema-versioned Opportunity identity with opaque Opportunity, Market, and
  Niche identifiers; a bounded proposition; YouTube source identity; and explicit known-or-unknown
  language and region context.
- Added strict validation, deterministic compact UTF-8 JSON, SHA-256 content identity, PD-009,
  ADR-031, dependency guards, and behavior-focused golden contract tests.

### Release boundaries

- No discovery, evidence qualification, lifecycle, classification, analytics, scoring, ranking,
  filtering, recommendation, persistence, API, workflow, AI, external service, or startup behavior
  was added.

### v0.10.1 - Personal Creator Profile Foundation

- Added an immutable schema-versioned Personal Creator Profile with closed self-declared production
  preferences/constraints and explicit Unknown semantics.
- Added strict validation, deterministic compact UTF-8 JSON, SHA-256 content identity, public Python
  exports, PD-008, ADR-030, and behavior-focused contract tests.

### Release boundaries

- No persistence, API, UI, inference, recommendation, opportunity filtering/scoring/ranking,
  confidence formula, AI execution, external integration, or application-startup behavior was added.

### v0.10.0a - Product Foundation Refinement

- Added Product Governance, Product Lifecycle, and the canonical Product Research Questions backlog.
- Added explicit Vision, Hypothesis, Research In Progress, Validated, and Implemented knowledge-state
  governance across Product Architecture documents.
- Added decision classifications, research-to-implementation traceability, and principles for
  falsifiability, unknown-state preservation, research precedence, language consistency, explainable
  AI, and explicit knowledge status.

### Release boundaries

- Additive documentation refinement only: no Product algorithm, confidence formula, scoring,
  recommendation logic, production code, API, test, research framework, technical architecture,
  persistence, dependency, or runtime behavior changed.

### v0.10.0 - Product Vision & Domain Foundation

- Added the authoritative Product Architecture foundation covering vision, principles, ubiquitous
  language, personas, journeys, Opportunity Engine, discovery capabilities, Creator Profile,
  Opportunity Confidence, recommendation philosophy, feature registry, roadmap, and decisions.
- Added ADR-029 to separate Product Architecture from Technical Architecture and require future
  technical decisions to trace to Product intent.
- Reframed the long-term platform around Opportunities while retaining channels, videos, topics,
  and trends as evidence and preserving existing implementation-status boundaries.

### Release boundaries

- Documentation only: no production code, analytics, research pipeline, API, algorithm, confidence
  formula, recommendation logic, AI, persistence, dependency, or runtime behaviour changed.

### v0.9.9 - Governed Channel Intelligence Framework

- Added immutable schema-versioned Channel Intelligence definitions, configuration, requests,
  summaries, metadata, manifests, results, validation, canonicalization, and service contracts.
- Added deterministic population, format, subscriber-relative, upload, distribution, exclusion,
  missing-value, canonical-ordering, and SHA-256 source/result integrity facts.
- Added ADR-028, the canonical format specification, and normal/edge/corruption/math coverage.

### Release boundaries

- No scoring, ranking, AI, recommendation, confidence, cohort or threshold comparison, signal,
  production policy, persistence, API, workflow, or external-service integration was added.

### Fixed

- Narrowed governed pipeline exception translation to exact upstream integrity/binding failures so
  programming errors are not masked and callers retain typed digest distinctions.
- Rejected Boolean research counts/cohort sizes and unknown direct-construction fields across the
  reused immutable backtesting contracts.

### Added

- Complete synthetic research-pipeline integrity coverage, public-export/dependency guards, and
  the v0.9.8.1 Research Architecture Stabilization audit with validation/digest traceability.

### Release boundaries

- No real research was executed and no new research capability was added.
- No threshold or candidate was compared, ranked, selected, or recommended; no Product decision
  was created and no runtime behavior changed.
- No API, persistence, workflow, AI, production signal, or external artifact importer was added.

## 0.9.8 - 2026-07-24

### Added

- Governed Statistical Evaluation schema version 1 with immutable definitions, configuration,
  requests, approved metrics, Wilson intervals, metadata, manifests, and results.
- Decimal-based deterministic calculation of accuracy, precision, recall/sensitivity, specificity,
  negative predictive value, false-positive/negative rates, balanced accuracy, F1, and MCC.
- Two-sided 95% Wilson intervals for accuracy, precision, recall, specificity, and the governed
  balanced-accuracy plug-in convention.

### Release boundaries

- No real research statistics were calculated and no threshold comparison, ranking, selection,
  interpretation, recommendation, Product decision, persistence, API, workflow, AI, or runtime
  behavior was created.

## 0.9.7 - 2026-07-24

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
