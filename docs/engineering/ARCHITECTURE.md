# YT Signal Scout Architecture

## System Shape

YT Signal Scout is a modular monolith with explicit module boundaries. Application services consume typed domain models rather than vendor-specific response objects, and each downstream stage owns one responsibility.

## Analytics Pipeline

The target analytics architecture is:

```text
YouTube API
    |
    v
Raw API DTOs
    |
    v
Canonical Domain Models
    |
    v
Validation
    |
    v
Deterministic Calculators
    |
    v
Calculator Registry
    |
    v
Analytics Assembler
    |
    v
CalculatedChannelAnalytics
    |
    v
Signal Engine
    |
    v
AI Narrative Engine
```

The YouTube acquisition layer owns interaction with the external API and conversion from upstream response shapes into immutable canonical models. The canonical models expose only the subset of public YouTube data with expected long-term application value.

## Transport and Domain Boundary

The transport layer owns YouTube-specific response formats and converts them into domain concepts before constructing canonical models. Canonical models intentionally hide upstream transport representations from analytics and every downstream layer.

For example, YouTube's `duration="PT5M30S"` transport value becomes `timedelta(minutes=5, seconds=30)` in the canonical `Video` model. Likewise, `privacyStatus="public"` becomes `PrivacyStatus.PUBLIC`.

This boundary prevents external naming and serialization formats from leaking into deterministic calculators, signals, or narratives.

The analytics layer consumes those canonical models. Shared validation establishes calculator preconditions, and each deterministic calculator produces exactly one typed metric without orchestration, scoring, signal detection, or AI behavior.

The calculator registry owns an explicitly injected, ordered calculator sequence. It executes each calculator once in registration order and returns an immutable result tuple. Duplicate metric identities are rejected during construction. Execution is fail-fast: calculator exceptions propagate unchanged, no partial result collection is returned, and later calculators are not executed.

The future analytics assembler will consume metric results, validate their completeness and uniqueness, and construct `CalculatedChannelAnalytics`. The registry will remain unaware of the aggregate, and the aggregate will remain a pure immutable data contract without mapping or orchestration behavior.

Implementation of the analytics assembler and population of `CalculatedChannelAnalytics` remain future work. The future signal engine will interpret deterministic results through explicit business rules. The AI narrative engine will be the final consumer and will explain typed evidence rather than calculate metrics or signals.

## Dependency Direction

Dependencies flow downward through the pipeline. Downstream stages may depend on typed outputs from the stage above, but upstream acquisition and deterministic calculation must not depend on signal or narrative concerns.

Raw API response shapes and Google SDK types must not cross the canonical domain-model boundary.

## Implementation Status

### Implemented Calculators

- ChannelAge
- AverageViews
- MedianViews
- ViewsPerDay
- UploadFrequency
- UploadConsistency
- ViewDistribution
- ViewOutlier
- ViewGrowthRate
- ViewEngagementRate

### Implemented Orchestration

- Calculator Registry

### Planned Pipeline Stages

- Analytics Assembler
- CalculatedChannelAnalytics population
- Signal Engine
- AI Narrative Engine

See ADR-002 for analytics-layer separation and ADR-003 for the canonical YouTube domain-model decision.
