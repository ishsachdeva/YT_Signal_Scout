# SIG-002 Research Protocol and Evaluation Methodology

**Protocol ID:** `SIG-002-RP-001`  
**Protocol version:** 1  
**Status:** Active  
**Effective date:** 2026-07-24  
**Accountable owner:** Analytics Owner  
**Required reviewers:** Product Owner; Architecture Owner  
**Applies to:** Every study offered as evidence for a SIG-002 threshold decision

## 1. Purpose and authority

This is the canonical methodology for producing reproducible evidence about candidate thresholds
for SIG-002, High Median Subscriber-Relative Reach. Given the same immutable dataset, labels,
study configuration, protocol version, and implementation version, independent engineers must
obtain identical factual results and the same study-validity disposition.

The protocol supports Product review; it does not select, recommend, approve, or publish a
threshold. Product owns the eventual threshold, comparator, equality behavior, and business
evidence through PDR-001 and the Signal Catalog. Analytics owns this methodology and the validity
of its interpretation. Accepted ADRs own research contracts and execution boundaries.

### Goals

- Establish one pre-registered, deterministic procedure for dataset selection, labelling,
  evaluation, boundary tests, study artifacts, and quality review.
- Measure candidate classification behavior against governed human labels.
- Preserve exclusions and missing facts without silently converting them into negative outcomes.
- Supply Product with factual, reviewable evidence and explicit limitations.

### Out of scope

- Choosing, recommending, approving, or publishing a production threshold or comparator.
- Executing a study, importing or creating a dataset, or labelling channels in this milestone.
- Ranking channels, generating a Momentum Score, or predicting growth or future performance.
- Changing Eligible Video Policy v1, qualification, analytics, runtime contracts, APIs, or Python.
- Treating research approval, recommendation, or eligibility as production authorization.

## 2. Research principles

Every study MUST be:

- **Deterministic:** no random split, sampling, tie resolution, clock read, implicit default, or
  order-dependent calculation is permitted.
- **Repeatable:** all inputs, versions, transformations, exclusions, and commands are recorded.
- **Versioned:** protocol, dataset, label set, configuration, calculation implementation, and
  artifact schemas have immutable identities and positive versions.
- **Evidence-first:** conclusions cite generated facts and limitations, never intuition alone.
- **Pre-registered:** dataset-selection rules, strata, candidates, comparator set, labels, metrics,
  and sensitivity variants are frozen before threshold results are inspected.
- **Non-manual in calculation:** humans may label and review through governed artifacts; they MUST
  NOT edit imported facts, calculation outputs, tables, or chart values by hand.
- **Explicit:** undocumented assumptions, hidden calculations, undocumented exclusions, and
  spreadsheet-only transformations invalidate the study.

Changing a frozen input creates a new version and a new study execution. It never overwrites an
existing artifact.

## 3. Required study registration

Before execution, the study definition MUST freeze:

1. study ID, version, purpose, protocol ID/version, owner, and creation timestamp;
2. dataset ID/version/schema version and label-set ID/version;
3. observation cutoff and all selection, inclusion, exclusion, and deduplication rules;
4. ordered subscriber-band set and whether gaps are permitted;
5. ordered threshold-candidate set, each candidate's numeric value and `>` or `>=` operator;
6. primary analysis population and every sensitivity population;
7. metric formulas, confidence level, boundary cases, and tie/display order;
8. methodology ID/version, implementation revision, runtime/dependency versions, and commands;
9. execution ID and explicit timezone-aware execution timestamp; and
10. all deviations from this protocol. A material deviation makes the study non-conforming unless
    an approved newer protocol version authorizes it.

Configuration order is authoritative. Implementations MUST NOT sort bands, candidates, criteria,
or recommendations unless an accepted contract explicitly requires canonical sorting.

## 4. Dataset methodology

### 4.1 Unit of analysis and minimum size

The unit of analysis is one unique channel snapshot at one timezone-aware evaluation timestamp,
represented by one valid `SubscriberRelativeBacktestObservation`. The primary labelled dataset
MUST contain at least **50 unique channels with final Positive or Negative labels**. This floor is
derived from the PRD R0 technical-spike exit gate of 50 manually reviewed channels; it is a study
completion floor, not a claim of statistical power or production readiness.

Only one snapshot per channel may enter the primary analysis. If the source contains several,
select the latest snapshot at or before the pre-registered cutoff; break an equal-timestamp tie by
ascending observation ID. Other snapshots may appear only in a separately registered temporal
sensitivity analysis and MUST NOT be treated as independent channels.

A band with no binary-labelled, threshold-eligible observation remains in all outputs with zero
support and unavailable derived rates. The protocol sets no unapproved per-band sufficiency
number. Product MUST be shown each band's exact support and warned that sparse bands cannot support
a defensible band-specific policy.

### 4.2 Required metadata

Each observation MUST satisfy Historical Dataset JSON schema version 2 and include its stable
observation ID, canonical channel ID, timezone-aware observation time, positive factual subscriber
count, and complete `SubscriberRelativeAnalysisResult`. The nested result MUST retain:

- qualification status, policy version, and ordered failure reasons;
- eligible standard-video count and median standard-video VSR availability/value;
- subscriber state and count consistency;
- evaluation timestamp; and
- channel-scoped uploads-playlist acquisition provenance, pagination state, discovered/enriched
  counts, omissions, and requested-ID resolution facts.

The study package MUST additionally bind immutable dataset custody metadata: source description,
collection method, collection window, cutoff, creator, creation timestamp, content digest and
digest algorithm, schema version, dataset version, selection query/rule version, and known
limitations. A valid import proves structural consistency, not factual custody.

### 4.3 Eligible and excluded channels

A channel is eligible for the primary threshold confusion matrix only when:

- it is the selected unique snapshot for that channel;
- its final label is Positive or Negative;
- its subscriber-relative analysis is qualified;
- median standard-video VSR is available and finite; and
- its positive subscriber count matches exactly one configured subscriber band.

All other valid observations remain in coverage and exclusion outputs. They MUST NOT be silently
dropped or coerced into negatives. Structural invalidity rejects the entire dataset; analytical
ineligibility produces a typed exclusion.

Excluded categories MUST distinguish at least: unqualified analysis by each existing qualification
failure, unavailable median, unmatched band, Borderline label, Unknown label, duplicate-snapshot
removal, and pre-registered sampling exclusion.

### 4.4 Sampling strategy

Use a deterministic stratified census of every observation available under the pre-registered
source, cutoff, and selection rules. If the eligible source exceeds a pre-registered study cap,
sample within each configured subscriber band by ascending SHA-256 of the UTF-8 string
`<dataset_id>:<dataset_version>:<channel_id>`, taking the first configured count. The cap and
per-band allocations MUST be frozen before labels or threshold results are inspected. Random,
convenience, cherry-picked, and post-result sampling are prohibited.

Discovery is query-bounded and MUST be reported as such. A study MUST NOT claim coverage of all
YouTube channels.

### 4.5 Historical and video window

The channel-snapshot collection interval and the single observation cutoff MUST be explicit. Each
observation uses Eligible Video Policy v1 at its recorded evaluation time: public, available,
classified standard videos with an inclusive age window of **24 elapsed hours through 90 elapsed
days**. Shorts and livestream replays are not mixed into the SIG-002 standard-video basis.

Views and current public subscribers MUST come from the same governed snapshot context described
by the observation. Historical subscriber counts MUST NOT be reconstructed from VSR. A study MUST
NOT recompute a serialized historical analysis unless a separately governed canonical-snapshot
contract is approved.

### 4.6 Subscriber bands

Subscriber bands are explicit, versioned, ordered, non-overlapping half-open ranges. Only the final
range may be unbounded. Gaps are invalid unless the configuration explicitly enables them, in
which case unmatched observations are reported as exclusions. This protocol deliberately sets no
band boundaries; choosing them is a pre-registered study configuration decision, not a hidden
default or production policy.

### 4.7 Deleted, private, incomplete, and missing data

- Resources omitted by enrichment are omissions, not inferred deletions and not fabricated
  placeholders.
- Private, deleted, unavailable, non-public, or unclassifiable videos are handled only through
  Eligible Video Policy v1 and recorded provenance; researchers MUST NOT repair the basis manually.
- Truncated uploads pagination, insufficient requested-ID resolution, hidden/missing/zero
  subscribers, and fewer than five eligible standard videos remain qualification failures.
- An unavailable median remains unavailable, never zero.
- A channel with missing required metadata makes import structurally invalid. A channel with valid
  but insufficient facts remains a typed analytical exclusion.
- No partial import is permitted.

## 5. Channel labelling methodology

### 5.1 Label target and evidence pack

Labels answer the PRD validation question: whether the channel shows unusually strong recent
audience demand relative to its current public subscriber scale. They are research annotations,
not SIG-002 outputs or Product policy.

Every reviewer receives the same immutable, versioned evidence pack and rubric. The pack MUST show
the channel snapshot timestamp, subscriber data-quality state, eligible-video basis and sample
size, eligible videos' factual public views and ages, median VSR, acquisition limitations, and
query-bounded provenance. It MUST hide candidate threshold IDs, candidate pass/fail states,
aggregate candidate metrics, and other reviewers' labels until independent review is complete.
Evidence-pack generation MUST be deterministic and its version/content digest recorded.

### 5.2 Closed labels

- **Positive:** the reviewer concludes that the labelled target is present from the permitted
  evidence, without relying on one exceptional video alone.
- **Negative:** the reviewer concludes that the target is absent from sufficient permitted
  evidence.
- **Borderline:** permitted evidence is sufficient to review, but reasonable interpretation is
  genuinely ambiguous or materially sensitive to rounding, exposure age, or mixed evidence.
- **Unknown:** permitted evidence is insufficient or unusable for a judgement, including a missing
  required evidence-pack fact or a material data-quality/provenance problem.

Reviewers MUST select exactly one label and a non-empty reason code from a pre-registered closed
rubric; optional notes may explain but cannot replace the code. Borderline and Unknown are never
merged with Negative.

### 5.3 Review and adjudication

At least two named qualified analysts independently label every selected channel. Reviewers MUST
not see candidate outcomes or one another's decisions. Matching labels become final. Disagreement
is resolved by a named adjudicator using the same evidence pack and rubric; the adjudicator records
one final label and rationale without altering the independent labels.

Label artifacts record label-set ID/version, channel and observation IDs, reviewer/adjudicator
identities, rubric and evidence-pack versions, timezone-aware timestamps, independent labels,
final label, reason codes, and provenance. Reviewer strings alone do not establish authentication.
The immutable engineering representations and strict canonical import boundaries are defined by
[Evidence Pack JSON Format](../engineering/EVIDENCE_PACK_FORMAT.md),
[Labelling Rubric JSON Format](../engineering/LABELLING_RUBRIC_FORMAT.md),
[Ground Truth Label JSON Format](../engineering/GROUND_TRUTH_LABEL_FORMAT.md), ADR-022, and
ADR-023. These contracts represent supplied artifacts only; they do not generate evidence, run a
labelling workflow, or choose labels.

### 5.4 Label changes and agreement

A final label changes only to correct a documented factual or rubric error, or under a newly
versioned rubric/evidence pack. The original artifact remains immutable; the replacement increments
the label-set version, identifies the superseded artifact, gives the reason, and requires the full
study to receive a new execution ID.

Report raw agreement as matching independent labels divided by all independently double-labelled
channels, both overall and by final label. Also report the complete reviewer-by-reviewer label
matrix. Agreement is a quality diagnostic, not a weighting or automatic validity decision.

## 6. Threshold evaluation methodology

### 6.1 Candidate generation and freezing

Candidates MUST be generated before viewing labels and stored as an ordered, versioned
`MedianVsrThresholdSet`. The study registration states one deterministic source:

1. **Domain grid:** an explicitly supplied finite ordered list justified without labels; or
2. **Observed-value grid:** the ascending unique finite median-VSR values from all structurally
   valid, qualified, median-available observations before labels are joined.

Each numeric value is paired with every pre-registered operator under study (`>` and/or `>=`).
Duplicate value/operator pairs are invalid. No candidate may be added, removed, or reordered after
labels are joined. Candidate support from the existing backtester remains factual and unlabelled;
the labelled evaluation is a separate governed analysis artifact and does not extend ADR-016's
current runtime contract.

### 6.2 Prediction and confusion matrix

For every primary-analysis observation and candidate, predicted Positive is the full-precision
comparison `M operator T`; otherwise predicted Negative. Do not round before comparison.

Using only final Positive and Negative labels, calculate integer counts:

```text
TP = labelled Positive and predicted Positive
FP = labelled Negative and predicted Positive
TN = labelled Negative and predicted Negative
FN = labelled Positive and predicted Negative
```

Counts MUST be reported overall and per subscriber band. Borderline, Unknown, unqualified,
median-unavailable, and unmatched-band observations are excluded from the confusion matrix and
reported separately.

Before any aggregation, ADR-025's immutable labelled-evaluation boundary records exactly one
prediction-versus-final-label fact for every governed observation in canonical order. Its True
Positive, True Negative, False Positive, and False Negative values are observation categories,
not totals; Borderline/Unknown truth and explicitly unavailable predictions remain Unknown or Not
Evaluated. Aggregation, metrics, intervals, and interpretation remain later protocol stages.

### 6.3 Required metrics

For every candidate, report:

```text
precision = TP / (TP + FP)
recall = TP / (TP + FN)
false_positive_rate = FP / (FP + TN)
false_negative_rate = FN / (FN + TP)
F1 = 2 * precision * recall / (precision + recall)
```

If any denominator is zero, the value is unavailable (`null`), never zero. F1 is unavailable if
precision or recall is unavailable or their sum is zero. Preserve integer counts as the primary
facts. Calculations use unrounded values; display may round to four decimal places using
round-half-even while machine-readable artifacts retain full values.

Also report qualification coverage, median availability, binary-label coverage, per-label counts,
threshold-eligible support, candidate hit/non-hit counts and rate, VSR distribution, exclusions,
and qualification-failure counts already governed by ADR-012 and ADR-016.

### 6.4 Confidence intervals

Report a two-sided **95% Wilson score interval** for every available binomial proportion:
precision, recall, false-positive rate, false-negative rate, and candidate hit rate. Use
`z = 1.959963984540054`, the metric denominator as `n`, and:

```text
center = (p + z^2 / (2n)) / (1 + z^2 / n)
half_width = z * sqrt((p(1-p) + z^2 / (4n)) / n) / (1 + z^2 / n)
interval = [max(0, center - half_width), min(1, center + half_width)]
```

An interval is unavailable when `n = 0`. No confidence interval is defined for F1 by this
protocol. Intervals describe sampling uncertainty under the study sample; they do not correct
discovery bias or prove population representativeness.

### 6.5 Candidate comparison, order, and ties

The canonical comparison table preserves configured subscriber-band order and configured candidate
order. It shows all counts, metrics, intervals, coverage, and exclusions side by side. **No scalar
score, weighted aggregate, winner, ordinal ranking, optimization objective, or automatic
recommendation is permitted.** This is the ranking methodology: candidates are not ranked because
Product and Analytics have approved no preference or loss function.

Consequently, ties are not broken analytically. Equal displayed metrics remain tied and candidate
configuration order is retained for stable presentation only. Product must explicitly weigh false
positives against false negatives in a later decision; researchers MUST NOT encode that preference.

### 6.6 Sensitivity analysis

Run the same frozen calculations without changing candidates for these pre-registered slices:

- each subscriber band and the combined primary population;
- `>` versus `>=` at each shared numeric threshold when both operators are registered;
- each eligible-sample-size group `5-9`, `10-19`, and `20+`;
- channels flagged as subscriber-count-rounded versus those not flagged, when the governed facts
  support that distinction; and
- one leave-one-channel-out influence diagnostic: for each candidate, report the minimum and
  maximum precision, recall, and F1 after removing each included channel once.

Unavailable slices remain present with counts and null metrics. No post-result slice may be added
to the primary study. Exploratory slices require a new explicitly labelled exploratory study and
cannot be presented as confirmatory evidence.

## 7. Boundary testing

Before accepting an implementation used for evidence, verify every candidate/operator against a
fixed conformance fixture. For threshold `T`, define `below = nextafter(T, -infinity)` and
`above = nextafter(T, +infinity)` in the implementation's binary64 representation.

Required cases are:

| Case | Required factual result |
|---|---|
| `M = below` | non-hit for `>` and `>=` |
| `M = T` | non-hit for `>`; hit for `>=` |
| `M = above` | hit for `>` and `>=` |
| `M = 0` | compare normally when structurally valid |
| largest finite non-negative `M` | compare normally without overflow |
| unavailable median | typed exclusion; no comparison |
| insufficient eligible sample | qualification exclusion; no comparison |
| every other qualification failure | typed exclusion preserving its failure reason |
| unmatched subscriber band when gaps are enabled | typed unmatched-band exclusion |
| non-finite or negative `M` or invalid `T` | structural rejection, not a non-hit |

Also test empty bands, all-Positive and all-Negative labelled slices, zero metric denominators,
duplicate candidate IDs/pairs, overlapping bands, dataset/configuration mismatch, label joins with
missing/duplicate channel identities, and stability under reversed input-observation order.

## 8. Required study artifacts

A complete study package is immutable and contains or content-addresses:

1. study definition and protocol snapshot;
2. original dataset plus manifest, custody metadata, digest, and successful import result;
3. original label artifacts, final label set, rubric, evidence-pack definition, and digests;
4. subscriber-band set, threshold set, study configuration, methodology, and sensitivity plan;
5. implementation source revision, environment/dependency snapshot, exact commands, and boundary
   conformance results;
6. execution request/result with study, execution, dataset, configuration, methodology, label-set,
   and protocol identities/versions plus timezone-aware execution timestamp;
7. complete factual backtest report and labelled evaluation output;
8. machine-readable tables and chart-source tables;
9. rendered tables and charts for coverage, label distribution/agreement, VSR distribution,
   confusion matrices, required metrics/intervals, sensitivity slices, and exclusions;
10. deviation, limitation, and invalidity logs; and
11. immutable study reviews and any methodology-bound human evaluation artifacts.

Every rendered number MUST be traceable to a machine-readable artifact. Charts MUST state sample
size, population/slice, dataset version, label-set version, candidate/operator, and axis units.
Charts are presentation only; machine-readable tables are authoritative.

## 9. Acceptance and rejection

### 9.1 Complete and valid

A study is complete only when:

- every registration field and required artifact exists and all identities/versions bind exactly;
- dataset import and structural validation succeed with no partial records;
- at least 50 unique channels have final binary labels;
- every selected channel has two independent labels and every disagreement is adjudicated;
- all configured candidates, bands, metrics, intervals, exclusions, sensitivity slices, and
  boundary cases are present, including zero-support/null results;
- a clean rerun from the recorded inputs and commands produces byte-identical canonical
  machine-readable outputs, excluding only explicitly non-canonical packaging metadata;
- no undocumented transformation, manual output edit, or protocol deviation exists; and
- required Analytics and governance reviews record their dispositions.

Completion means the study is eligible for human research review. It does not mean the evidence is
sufficient or that any candidate is suitable for production.

### 9.2 Invalid

A study is invalid and MUST NOT be supplied as threshold evidence if any required input is mutable,
missing, unversioned, or mismatched; custody cannot be established; import is partial; labels leak
candidate outcomes; the minimum binary-labelled size is not met; sampling or exclusions differ
from registration; calculations are manual or hidden; outputs cannot be reproduced; required
boundary tests fail; or a material protocol deviation is unapproved.

### 9.3 Rejected or insufficient

A structurally valid completed study may still be rejected or judged insufficient after review
because of material discovery bias, sparse band support, poor label agreement, excessive
Borderline/Unknown or qualification exclusions, wide intervals, instability, stale/inapplicable
data, unexplained anomalies, or evidence that the label target does not match Product intent.
These are recorded review judgements with rationale; they MUST NOT be converted into undocumented
numeric gates. Rejection preserves the artifact and has no production effect.

## 10. Product evidence flow

```text
Governed dataset + governed labels + frozen configuration
                         |
                         v
             Deterministic study execution
                         |
                         v
       Factual reports + labelled evaluation artifacts
                         |
                         v
              Analytics validity review
                         |
                         v
        Product review under PDR-001 (no auto-promotion)
                         |
                         v
     Separate Product decision and required reviews, if any
```

Product may receive only a complete valid immutable study package, Analytics review disposition,
candidate comparison tables in configured order, metrics and intervals, coverage/exclusions,
label agreement, sensitivity results, limitations, and human research recommendations permitted
by the bound methodology.

Product MUST NOT receive a cherry-picked subset, manually edited report, unsupported causal or
population claim, hidden calculation, unlabeled exploratory result presented as confirmatory,
automatic winner, or claim that study approval/eligibility authorizes production. Test fixtures
and synthetic boundary data prove implementation behavior only; they are not threshold evidence.

Architecture remains responsible for typed runtime evidence representation, qualified rule-input
boundaries, provenance composition, compatibility, production eligibility/approval boundaries,
and implementation readiness after Product approves observable behavior. This protocol does not
close any SIG-002 Product or Architecture gap.

## 11. Traceability

- [Decision Governance](../governance/DECISION_GOVERNANCE.md): ownership, review, lifecycle,
  blocking, and evidence authority.
- [PDR-001](../product/decisions/PDR-001-sig-002-product-policy.md): unresolved Product threshold,
  comparator, equality, and business-evidence decisions.
- [Signal Catalog](../product/SIGNAL_CATALOG.md): SIG-002 status, Eligible Video Policy v1,
  qualification, and threshold provenance.
- [SIG-002 specification](../signals/SIG-002.md): intended signal meaning, inputs, limitations,
  and pending decisions.
- [SIG-002 gap analysis](../signals/SIG-002_GAP_ANALYSIS.md): implementation blockers that research
  alone cannot close.
- [Historical Dataset JSON Format](../engineering/HISTORICAL_DATASET_FORMAT.md): strict schema
  version 2 custody, canonicalization, integrity, and import boundary.
- [Ground Truth Label JSON Format](../engineering/GROUND_TRUTH_LABEL_FORMAT.md): strict schema
  version 1 dataset/evidence binding, independent review, adjudication, history, and integrity.
- ADR-010 and ADR-011: qualification, provenance, analytics, and policy-free evidence facts.
- ADR-012: deterministic band/candidate backtesting, exclusions, statistics, and ordering.
- ADR-013: strict dataset import and factual-trust boundary.
- ADR-014: controlled deterministic execution and dataset/configuration binding.
- ADR-015: immutable study artifacts and research-only approval.
- ADR-016: current factual methodology contract and its deliberate metric boundary.
- ADR-017: immutable methodology-bound human evaluations.
- ADR-018 and ADR-019: historical production-promotion and eligibility contracts whose mandatory
  manual-approval portions are superseded by ADR-021.
- ADR-020: immutable dataset custody, provenance, canonical serialization, and digest integrity.
- ADR-021: development-time Product/release governance and autonomous post-release runtime
  evaluation; research labels and evaluations never authorize individual runtime outcomes.
- ADR-022: immutable ground-truth label artifacts, canonical import, and dataset/evidence binding.
- ADR-023: immutable evidence-pack and labelling-rubric definitions, concrete evidence snapshots,
  canonical integrity, and exact label-artifact binding.
- ADR-024 and ADR-025: governed non-analytical study execution followed by immutable
  observation-level prediction-versus-truth facts before aggregation.

## 12. Version history

| Version | Date | Change | Approval reference |
|---|---|---|---|
| 1 | 2026-07-24 | Initial canonical SIG-002 research protocol | Documentation milestone v0.9.1 |
| 2 | 2026-07-24 | Added governed execution and observation-level labelled evaluation boundaries | ADR-024 and ADR-025 |
