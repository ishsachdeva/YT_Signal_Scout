# ADR-010: Acquisition Provenance and Subscriber-Relative Qualification

**Status:** Accepted

**Date:** 2026-07-22

**Owner:** Product & Engineering

## Supersedes

None. This decision refines the future qualification boundary retained by ADR-008 and preserves
the calculator orchestration established by ADR-009.

---

# 1. Decision Summary

Introduce a separate immutable video-acquisition result that carries canonical videos and typed
acquisition provenance together. Subscriber-relative processing will classify the unique canonical
resources once, qualify the dataset using that classification and provenance, and always compute
the existing factual analytics. A new immutable analysis result will return qualification and
analytics together. Downstream signal evaluation must not interpret unqualified analytics.

Qualification uses a narrowly defined **requested-ID resolution rate**, not a claim about complete
channel retrieval:

```text
enriched_unique_video_count / enrichment_requested_unique_count
```

The approved threshold is `>= 0.60`, inclusive. Pagination completeness is a separate
qualification fact and is never inferred from that rate.

# 2. Context

Search and uploads acquisition currently return canonical videos after stable enrichment. The
service knows discovery positions, unique IDs submitted to `videos.list`, returned resources,
omissions, and pagination state while executing, but the existing `SearchResult` does not preserve
those facts as a coherent downstream contract. Its pagination fields also do not establish an
expected-channel-population denominator.

Eligible Video Policy v1 already approves a minimum of five eligible standard videos and a 60%
completeness threshold. It also states that eligibility, qualification, calculations, and signals
are separate responsibilities. Qualification cannot implement the approved thresholds until
acquisition provenance and the meaning of completeness are explicit.

# 3. Problem Statement

How should acquisition facts cross into subscriber-relative qualification, what exactly should
qualification decide, and how should unqualified factual analytics be represented without
fabricating expected-population coverage or duplicating eligibility and signal policy?

# 4. Decision Drivers

- Deterministic and auditable qualification
- No fabricated expected population
- Transport/domain separation
- Preservation of discovery and duplicate provenance
- Compatibility with immutable canonical models and existing calculators
- Explicit downstream signal safety
- Future persistence compatibility
- Minimal overlapping policy

# 5. Goals

- Preserve acquisition provenance at its source.
- Give every population count one precise meaning.
- Distinguish requested-ID resolution, pagination coverage, and eligibility.
- Define a closed, ordered qualification-failure model.
- Preserve factual analytics for unqualified datasets.
- Keep invalid inputs distinct from normal qualification failures.

# 6. Alternatives Considered

## Option A — Extend `SearchResult`

### Pros

- Reuses an existing return type.
- Minimizes the number of top-level acquisition models.

### Cons

- `SearchResult` also represents channels and generic pagination.
- Mixes video enrichment provenance into a broad discovery model.
- Existing field semantics cannot represent all required populations safely.
- Produces a larger compatibility burden for unrelated channel search.

Rejected.

## Option B — Separate typed video-acquisition result

### Pros

- Keeps canonical videos, provenance, and pagination from one acquisition together.
- Lets search and uploads share explicit population semantics without pretending their upstream
  totals mean the same thing.
- Prevents callers from constructing inconsistent primitive counts.
- Supports deterministic tests and future persistence.

### Cons

- Video acquisition return contracts must evolve.
- Callers must select the analytics-safe unique canonical collection explicitly.

Selected.

## Option C — Construct provenance outside `YouTubeService`

### Pros

- Avoids changing acquisition return models.

### Cons

- The necessary facts are most accurate inside acquisition orchestration.
- Callers cannot recover omitted IDs or cross-page deduplication reliably after the fact.
- Multiple callers could produce contradictory provenance.

Rejected.

## Option D — Pass primitive counts to qualification

### Pros

- Small qualification method signature in concept.

### Cons

- Counts lose their scope, uniqueness, and pagination semantics.
- Invalid combinations become easy to construct.
- Weak future persistence and evidence provenance.

Rejected.

# 7. Decision

## 7.1 Acquisition ownership and result

`YouTubeService` owns construction of a future immutable `VideoAcquisitionResult` because it alone
observes discovery, stable deduplication, enrichment responses, omissions, and pagination.

The conceptual result contains:

```text
VideoAcquisitionResult
    resolved_discovery_videos
    unique_canonical_videos
    provenance
```

- `resolved_discovery_videos` preserves successfully enriched discovery positions, including
  duplicates, in source order. Duplicate positions may reference the same immutable `Video`.
- `unique_canonical_videos` contains one canonical object per resolved video ID in first-discovery
  order. It is the only collection used to construct `ChannelAnalytics`.
- `provenance` contains immutable population and pagination facts for the acquisition invocation.

Search-video and uploads-video acquisition will return this focused result. Channel search remains
on the existing generic `SearchResult`. Direct single-video retrieval remains unchanged.

The conceptual provenance contracts are:

```text
VideoAcquisitionProvenance
    source                         SEARCH | UPLOADS_PLAYLIST
    source_channel_id              required for UPLOADS_PLAYLIST; absent for SEARCH
    discovery_request_capacity
    discovered_position_count
    discovered_unique_video_count
    enrichment_requested_unique_count
    enriched_unique_video_count
    enriched_output_position_count
    omitted_unique_video_count
    pagination

PaginationProvenance
    status                         COMPLETE | TRUNCATED
    pages_fetched
    page_size_requested
    page_limit
    next_page_token_present
    upstream_total_results         optional, informational only
```

Counts are non-negative and satisfy these invariants:

```text
enriched_unique_video_count
    <= enrichment_requested_unique_count
    == discovered_unique_video_count
    <= discovered_position_count

omitted_unique_video_count
    == enrichment_requested_unique_count - enriched_unique_video_count

enriched_output_position_count
    <= discovered_position_count
```

An empty discovery has zero for all population counts. Pagination status is `COMPLETE` exactly
when `next_page_token_present` is false and `TRUNCATED` exactly when it is true. Violations are
invalid provenance and raise validation errors.

General search can discover videos from multiple channels. Its provenance is valid acquisition
evidence but is not a channel-scoped population and cannot qualify one channel. Subscriber-relative
qualification accepts only `UPLOADS_PLAYLIST` provenance whose `source_channel_id` matches the
canonical channel. Search remains a channel-discovery input; after selecting a channel, callers
must perform that channel's uploads acquisition before subscriber-relative qualification. Passing
search-scoped or mismatched-channel provenance is invalid input, not a normal qualification
failure.

## 7.2 Population definitions

All counts cover one bounded acquisition invocation.

| Population | Definition | Counting basis |
|---|---|---|
| Discovery request capacity | Sum of `maxResults` requested from discovery endpoints for pages actually requested | Positions; an upper bound, not an expected population |
| Discovered position count | Valid video-ID positions returned by fetched discovery pages | Positions; duplicates count |
| Discovered unique video count | Stable first-seen set of valid discovered video IDs | Unique entities |
| Enrichment-requested unique count | Discovered unique IDs actually submitted to `videos.list`; cross-page duplicates are excluded | Unique entities |
| Enriched unique video count | Requested IDs for which a complete resource was returned and parsed into one canonical `Video` | Unique entities |
| Enriched output position count | Discovery positions whose IDs resolved successfully after duplicate reconstruction | Positions; duplicates count |
| Omitted unique video count | Enrichment-requested unique count minus enriched unique video count | Unique entities |
| Eligible standard-video count | Standard videos accepted by Eligible Video Policy v1 | Unique entities from classification; not acquisition provenance |

A malformed discovery ID or malformed complete resource is invalid transport input and fails the
acquisition; it is not silently excluded from a denominator. The vague term `requested population`
must not be used without its qualified name. Discovery request capacity, enrichment-requested
unique count, and expected channel population are different facts.

## 7.3 Completeness terminology

The only approved percentage available from current official response facts is
`requested_id_resolution_rate`:

```text
requested_id_resolution_rate =
    enriched_unique_video_count / enrichment_requested_unique_count
```

The inclusive qualification threshold is `0.60`. Implementations compare the integer numerator
and denominator without pre-comparison rounding. When the denominator is zero, the rate is
undefined (`None`) and does not independently fail resolution; the eligible-sample condition still
fails.

This rate measures whether IDs actually sent for enrichment resolved to canonical resources. It is
not named retrieval completeness because it does not measure the full channel or search universe.

The following are prohibited formulas:

- returned videos / upstream `totalResults` — upstream totals do not describe the bounded resolved
  ID population consistently and may exceed intentionally fetched pages;
- returned videos / requested page size — page size is capacity, not an observed population;
- eligible videos / discovered videos — this is eligibility yield, not acquisition response;
- supplied videos / supplied videos — this fabricates completeness by construction.

Canonical parsing is fail-fast. Therefore a successful result has canonical parsing success for
every resource counted as enriched; no separate canonicalization rate is needed.

## 7.4 Pagination provenance

Use the minimum closed state:

```text
PaginationStatus.COMPLETE
PaginationStatus.TRUNCATED
```

`COMPLETE` means the final fetched discovery response exposed no next-page token. `TRUNCATED` means
acquisition stopped while a next-page token remained, whether because search returns one bounded
page or uploads reached the caller's `max_pages` limit. Intentional truncation remains truncation
for qualification.

Provenance also records discovery source, pages fetched, page-size request, configured page limit,
whether a next token remained, and optional upstream `totalResults`. Upstream total may be retained
as informational provenance but is never a completeness denominator. Unknown upstream total needs
no pagination enum value because it is orthogonal to whether another page token remained.

## 7.5 Qualification scope

Subscriber-relative qualification consumes:

- immutable acquisition provenance;
- one `EligibleVideoClassification` built from `unique_canonical_videos`;
- canonical channel subscriber statistics;
- explicit evaluation time.

The provenance must be channel-scoped `UPLOADS_PLAYLIST` provenance. Search-query provenance is
never partitioned or guessed into per-channel qualification denominators.

It decides only:

- pagination is complete;
- requested-ID resolution rate is at least 60% when defined;
- subscriber state supplies a visible positive denominator;
- at least five eligible standard videos exist.

Age, privacy, availability, publication, view-count, live-state, and format rules remain exclusively
owned by `EligibleVideoClassifier`. Qualification consumes the resulting eligible count and
exclusions; it does not repeat individual-video policy. There is no independent minimum canonical
video count beyond the approved eligible minimum.

## 7.6 Subscriber state

Qualification derives subscriber facts from canonical `Channel.statistics`; callers do not pass a
second potentially contradictory primitive count.

The qualification result records a closed subscriber state:

```text
AVAILABLE_POSITIVE
HIDDEN
UNAVAILABLE
NOT_POSITIVE
```

| Canonical state | Treatment |
|---|---|
| Statistics absent | Normal failure: `SUBSCRIBER_COUNT_UNAVAILABLE` |
| Hidden true, count absent | Normal failure: `SUBSCRIBER_COUNT_HIDDEN` |
| Hidden false, count absent | Normal failure: `SUBSCRIBER_COUNT_UNAVAILABLE` |
| Hidden false, count zero | Normal failure: `SUBSCRIBER_COUNT_NOT_POSITIVE` |
| Hidden false, count positive | Valid denominator |
| Negative count | Invalid canonical input; validation exception |
| Hidden true with numeric count | Contradictory canonical input; validation exception |

Validation of contradictions precedes qualification. Among normal states the rows are mutually
exclusive, so only one subscriber reason can appear.

## 7.7 Duplicates

Duplicate discovery positions remain acquisition provenance and remain visible in
`resolved_discovery_videos`. Qualification and analytics consume `unique_canonical_videos`, so a
discovered entity is classified and calculated once. This stable collapse is explicit in the
acquisition result and is not an eligibility decision.

If a caller independently constructs a `ChannelAnalytics` dataset containing duplicate video IDs,
existing analytics validation remains authoritative and raises. Qualification does not repair or
convert invalid analytics input into a normal failure.

## 7.8 Canonical incompleteness

Do not introduce a general `CANONICAL_DATA_INCOMPLETE` failure. It would overlap with eligibility
exclusions and would not identify an actionable condition. Missing publication time, unknown
privacy or availability, unresolved format, and missing view count remain structured classifier
exclusions. They affect qualification only through the eligible standard-video count. Subscriber
unavailability has its own dataset-level reasons.

## 7.9 Failure model

Qualification returns all applicable normal failures in this fixed order:

1. `ACQUISITION_TRUNCATED`
2. `INSUFFICIENT_REQUESTED_ID_RESOLUTION`
3. `SUBSCRIBER_COUNT_HIDDEN`
4. `SUBSCRIBER_COUNT_UNAVAILABLE`
5. `SUBSCRIBER_COUNT_NOT_POSITIVE`
6. `INSUFFICIENT_ELIGIBLE_STANDARD_VIDEOS`

The reasons are a closed enum stored as an immutable ordered tuple. Supporting evidence is not
duplicated into free-form reason strings; it lives in typed qualification fields: acquisition
provenance, requested-ID resolution numerator/denominator/rate, subscriber state, eligible count,
required thresholds, evaluation time, and policy version. `qualified` is true exactly when the
failure tuple is empty.

Invalid provenance invariants, malformed timestamps, duplicate IDs in the analytics-safe unique
collection, negative counts, and contradictory subscriber facts raise validation exceptions
instead of returning qualification failures.

Representative truth table:

| Pagination | Resolution | Subscriber state | Eligible standard | Outcome |
|---|---:|---|---:|---|
| Complete | 100% | Visible positive | 5 | Qualified |
| Complete | 60% | Visible positive | 5 | Qualified |
| Complete | 59% | Visible positive | 5 | Insufficient requested-ID resolution |
| Truncated | 100% | Visible positive | 5 | Acquisition truncated |
| Complete | 100% | Hidden | 5 | Subscriber count hidden |
| Complete | 100% | Missing | 5 | Subscriber count unavailable |
| Complete | 100% | Zero | 5 | Subscriber count not positive |
| Complete | 100% | Visible positive | 4 | Insufficient eligible standard videos |
| Truncated | 50% | Missing | 0 | All four applicable reasons in fixed order |
| Complete | Undefined (zero requested IDs) | Visible positive | 0 | Insufficient eligible standard videos |

## 7.10 Qualification and analytics

Adopt **Model B: analytics always computes factual results**.

The pipeline is:

```text
VideoAcquisitionResult + canonical Channel
    -> analytics-safe unique ChannelAnalytics
    -> EligibleVideoClassifier (once)
    -> SubscriberRelativeQualification
    -> SubscriberRelativeAnalyticsOrchestrator (existing calculators, once each)
    -> SubscriberRelativeResultAssembler
    -> SubscriberRelativeAnalysisResult(qualification, analytics)
```

The eligible count calculator always runs. The median calculator also runs; it receives the valid
positive subscriber count when available and otherwise receives `None`, preserving its existing
nullable factual result. Truncation, low resolution, or a small eligible population does not erase
the facts that can be calculated from the supplied snapshot.

Signals must not receive bare subscriber-relative analytics. Future signal-facing orchestration
consumes `SubscriberRelativeAnalysisResult` and permits business signal evaluation only when
`qualification.qualified` is true. Signal rules do not recreate qualification policy. The existing
Signal Engine and calculators remain unchanged by this decision.

## 7.11 Result contracts

The conceptual immutable contracts are:

```text
SubscriberRelativeQualification
    qualified
    failures
    provenance
    requested_id_resolution_rate
    eligible_standard_video_count
    subscriber_state
    evaluated_at
    policy_version

SubscriberRelativeAnalysisResult
    qualification
    analytics
```

The future public application entry point is conceptually:

```text
analyze(
    channel: Channel,
    acquisition: VideoAcquisitionResult,
    evaluation_time: datetime,
) -> SubscriberRelativeAnalysisResult
```

It validates channel-scoped provenance, constructs `ChannelAnalytics` from
`unique_canonical_videos` with `generated_at=evaluation_time`, classifies once, qualifies once,
runs both calculators once, and assembles the combined result. It replaces the separately supplied
subscriber-count primitive with canonical `channel.statistics`.

`SubscriberRelativeAnalytics` remains the factual calculator aggregate. The qualification result
references acquisition provenance rather than copying its population fields. Classifier
exclusions remain owned by `EligibleVideoClassification`; they may be retained by application
orchestration for evidence but are not duplicated into every qualification failure.

# 8. Decision Rationale

A separate acquisition result preserves facts where they are observed and avoids overloading
generic pagination. Narrow terminology prevents requested-ID response quality from masquerading
as full-channel retrieval. Returning qualification alongside factual analytics preserves existing
calculator semantics while giving downstream signals one explicit safety gate. Closed accumulated
reasons make failure behavior deterministic and explainable without treating invalid input as a
normal business outcome.

# 9. Related Engineering Principles

- EP-001 Build for Maintainability Before Optimization
- EP-002 Separation of Concerns
- EP-003 Single Responsibility Principle
- EP-004 Deterministic Business Logic
- EP-005 Dependency Injection
- EP-006 Immutable Models

# 10. Consequences

## Positive

- Qualification becomes reproducible and evidence-backed.
- Acquisition, eligibility, qualification, analytics, and signals retain distinct ownership.
- Duplicate and omission semantics remain explicit.
- Factual analytics remain available for diagnostics even when signal use is prohibited.
- Provenance can be persisted later without reverse-engineering transport behavior.

## Negative

- Video acquisition and subscriber-relative service return contracts must evolve together.
- Callers must distinguish discovery-position videos from unique analytics-safe videos.
- Search discovery requires a subsequent channel-scoped uploads acquisition before qualification.

## Risks

- Callers could bypass the analysis result and pass bare analytics to future rules.
- Upstream `totalResults` may be mistaken for a denominator despite explicit prohibition.
- Qualification may exclude useful partial datasets from signal evaluation, by design.

# 11. Implementation Impact

### Affected folders

- `backend/app/services/youtube/`
- `backend/app/services/analytics/`
- `backend/tests/`
- application composition

### Affected modules

- New acquisition provenance and video-acquisition result models
- Video search and uploads return contracts
- New qualification models and service
- Subscriber-relative application orchestration and result contract
- Composition and integration tests

### Migration required?

Yes, for in-process callers. Existing video acquisition callers must consume
`VideoAcquisitionResult`, and subscriber-relative callers must consume
`SubscriberRelativeAnalysisResult`. No persisted-data migration exists today.

### Breaking changes?

Yes, at the application service contract level. Canonical `Video`, calculators,
`SubscriberRelativeAnalytics`, and Signal Engine contracts remain unchanged.

# 12. Security Impact

No private analytics or new credentials are introduced. Hidden subscribers remain unestimated.
Typed provenance reduces the risk of fabricated completeness claims.

# 13. Performance Impact

The new work is bounded in-memory counting and validation. Classification and each existing
calculator still execute once. No new network request is required.

# 14. Cost Impact

No infrastructure cost. Existing API requests produce the provenance facts.

# 15. Operational Impact

Diagnostics should expose policy version, pagination state, population counts, resolution rate,
and ordered qualification reasons without logging raw transport payloads or page tokens.

# 16. Future Revisit Criteria

Revisit when:

- the product approves qualification over an intentionally bounded cohort rather than complete
  pagination;
- a defensible expected-channel-population snapshot becomes available;
- acquisition provenance is persisted or replayed;
- new acquisition sources require source-neutral provenance semantics;
- production evidence needs classifier exclusion summaries.

# 17. References

- Signal Catalog v1.2, Eligible Video Policy v1
- ADR-002: Separate Raw Analytics, Deterministic Metrics, and Signal Generation
- ADR-008: Establish Explicit Format-Specific Eligible Video Bases
- ADR-009: Separate Subscriber-Relative Orchestration
- YT Signal Scout Architecture
