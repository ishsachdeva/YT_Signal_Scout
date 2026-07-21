# ADR-003: YT-003 — Rich YouTube Domain Model Before Analytics Expansion

**Status:** Accepted

**Date:** 2026-07-21

**Owner:** Product & Engineering

## Supersedes

None

---

# 1. Decision Summary

The canonical YouTube domain model will expose the intentional subset of YouTube Data API v3 fields needed by deterministic analytics and downstream consumers before the analytics layer expands further.

---

# 2. Context

Deterministic analytics are beginning to require richer video metadata than publication timestamps and view counts. Future calculators, the calculator registry, signal generation, and AI-generated narratives will need stable access to selected public statistics, content metadata, and publication status.

Adding each field only after dependent analytics are implemented would repeatedly change the shared domain boundary and create unnecessary churn across otherwise independent layers.

---

# 3. Problem Statement

How should the canonical YouTube video model evolve to support planned analytics and downstream interpretation without either repeatedly changing its contract or mirroring the entire upstream API resource?

---

# 4. Decision Drivers

- Stable analytics contracts
- Strong typing
- Separation of acquisition and analytics concerns
- Maintainability
- Long-term analytical value
- Simplicity

---

# 5. Goals

- Establish a stable canonical video model before further analytics expansion.
- Model public fields with expected analytical, signal, or narrative value.
- Keep upstream transport and response shapes outside the analytics layer.
- Avoid fields without a foreseeable application use.

---

# 6. Alternatives Considered

## Option A — Add fields only when immediately needed

### Pros

- Smallest possible model at each milestone

### Cons

- Repeated architectural churn
- More frequent changes to shared contracts
- Downstream refactoring after calculators are implemented

This option was rejected because incremental contract changes would repeatedly disturb the analytics boundary.

---

## Option B — Mirror the entire YouTube API video resource

### Pros

- Every upstream field is immediately available

### Cons

- Unnecessarily large domain model
- Strong coupling to the external API
- Validation and maintenance burden for fields without product value

This option was rejected because most upstream fields have no long-term analytical value for YT Signal Scout.

---

## Option C — Model an intentional analytics-oriented subset

### Pros

- Stable, strongly typed domain boundary
- Lower coupling to upstream response shapes
- Supports planned calculators, signals, and narratives

### Cons

- Slightly larger model before every field is consumed
- Additional parsing and validation will be required later

---

# 7. Decision

Adopt Option C.

The canonical `Video` model will expose the subset of the YouTube Data API v3 `snippet`, `statistics`, `contentDetails`, and `status` parts required by:

- deterministic analytics
- calculator registry orchestration
- the signal engine
- the AI narrative engine

In addition to existing fields, the model will include like count, comment count, duration, tags, category ID, default language, and privacy status. Duration will use `timedelta`, and privacy status will use a strongly typed `PrivacyStatus` enum so that the canonical model represents domain concepts rather than upstream strings. It will not attempt to mirror every field exposed by the API. Fields are admitted only when they have foreseeable analytical or narrative value.

Raw API response shapes remain an acquisition concern. The acquisition layer will convert values such as ISO 8601 duration strings and privacy-status strings into their canonical domain types. Parsing the newly added properties is intentionally deferred to a separate milestone.

---

# 8. Decision Rationale

An intentional subset preserves a stable internal contract without making the application domain a copy of an external vendor schema. Adding the selected fields now reduces breaking refactors as calculators and downstream engines are introduced, while retaining clear ownership between acquisition, validation, deterministic calculation, signal interpretation, and narrative generation.

---

# 9. Related Engineering Principles

- EP-001 Build for Maintainability Before Optimization
- EP-002 Separation of Concerns
- EP-003 Single Responsibility Principle
- EP-004 Deterministic Business Logic
- EP-006 Immutable Models

---

# 10. Consequences

## Positive

- More stable analytics layer
- Cleaner architectural evolution
- Fewer breaking refactors
- Simpler future registry integration
- Stronger typing across boundaries
- Richer metadata for future AI narratives

## Negative

- Slightly larger canonical domain model
- Some fields will remain unused initially
- Additional parsing and validation work is required later

## Risks

- Future contributors may add upstream fields without demonstrating long-term application value.
- Optional public statistics may be mistaken for guaranteed values unless consumers validate their requirements.

---

# 11. Implementation Impact

### Affected folders

- backend/app/services/youtube/
- docs/engineering/

### Affected modules

- `Video`
- Future YouTube response parsing
- Future deterministic calculators and downstream consumers

### Migration required?

No

### Breaking changes?

No. New fields are optional and preserve existing construction patterns.

---

# 12. Security Impact

No direct security impact. The decision covers public YouTube metadata only and does not authorize collection of private analytics.

---

# 13. Performance Impact

Negligible model-level overhead. Future acquisition requests may return larger payloads when the additional parts are requested.

---

# 14. Cost Impact

No immediate infrastructure or operational cost impact.

---

# 15. Operational Impact

Future acquisition parsing and contract tests must preserve optional-field behavior when YouTube omits public statistics or metadata.

---

# 16. Future Revisit Criteria

Revisit this decision if:

- planned analytics require a field outside the selected subset
- YouTube changes the availability or semantics of a selected field
- a selected field proves to have no analytical, signal, or narrative value
- a new source requires a source-neutral canonical representation

---

# 17. References

- Product Requirements Document
- Technical Requirements Document
- Feature Catalogue
- YouTube Data API v3 video resource documentation
- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation
- Engineering Principles
