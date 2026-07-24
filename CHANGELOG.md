# Changelog

This file records user-visible and architectural changes to YT Signal Scout by release.

## Unreleased

### Added

- Canonical SIG-002 Research Protocol covering governed datasets, independent channel labels,
  deterministic classification metrics, Wilson intervals, sensitivity and boundary testing,
  immutable study artifacts, acceptance criteria, and the Product evidence boundary.

### Release boundaries

- No research was executed and no dataset, labels, study report, or threshold recommendation was
  created.
- SIG-002 remains blocked; no production threshold, runtime behavior, or public contract changed.

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
