# Research Architecture Stabilization and Integrity Audit

## 1. Scope

This audit verifies the implemented governed research pipeline through v0.9.8. It covers research
models, importers, validators, services, canonicalizers, exceptions, tests, exports, architecture,
format documents, the SIG-002 Research Protocol, ADR-012 through ADR-027, navigation, and runtime
composition. It introduces no new research capability.

## 2. Audited pipeline

```text
Historical Dataset
    -> Evidence Packs + Labelling Rubric
    -> Ground Truth Labels
    -> Governed Study Execution
    -> Supplied Predictions + Observation-Level Labelled Evaluation
    -> Counts-Only Evaluation Aggregation
    -> Governed Statistical Evaluation
```

A synthetic six-observation integration test exercises the entire chain. It produces one True
Positive, True Negative, False Positive, False Negative, Unknown, and Not Evaluated outcome, then
verifies counts, defined statistics, identity/version/schema continuity, digest continuity,
deterministic reruns, and byte-identical final serialization.

## 3. Boundary-responsibility matrix

| Boundary | Sole responsibility | Explicit exclusions |
|---|---|---|
| Historical Dataset importer/canonicalizer | Strictly import, order, and content-address supplied historical observations | Acquisition, analytics execution, labels, policy |
| Evidence Pack importer/canonicalizer | Strictly import typed reviewer evidence and verify definition/pack integrity | Evidence generation, predictions, review workflow |
| Rubric importer/canonicalizer | Strictly import non-executable reviewer guidance | Automated labelling or scoring |
| Ground Truth importer/canonicalizer/binding validator | Import labels and verify exact evidence/rubric bindings | Choosing, changing, or aggregating labels |
| Study execution validator/service/canonicalizer | Validate complete governed inputs and package one immutable execution | Prediction generation, analytics, persistence |
| Labelled evaluation validator/service/canonicalizer | Compare one supplied prediction with final truth per observation | Aggregation, metrics, interpretation |
| Aggregation validator/service/canonicalizer | Count six closed observation outcomes exactly once | Division, rates, statistics, ranking |
| Statistical validator/service/canonicalizer | Calculate the approved mathematical metric and interval set | Candidate comparison, interpretation, recommendation, policy |

Importers do not execute research; canonicalizers serialize and hash without interpretation;
validators establish preconditions without producing analytical outputs. Application startup
imports no research execution service.

## 4. Contract-consistency findings

All current governed artifact contracts are frozen, reject unknown fields, use typed identifiers,
positive versions, immutable tuples, closed enums/literals, caller-supplied timezone-aware times,
and explicit definition/configuration/source bindings. Result manifests carry exact upstream
digests and their own SHA-256 digest.

One legacy inconsistency was corrected: the immutable threshold-backtesting models reused by the
Historical Dataset boundary were frozen but did not set `extra="forbid"` for direct typed
construction. They now match the strict governed contract surface. Stable field names were not
changed. `HistoricalDatasetDigest` and `LabelContentDigest` remain distinct bounded-context types
with identical SHA-256 value constraints; consolidating them would be unnecessary public churn.

Aggregation counts, configured expected cohort size, and Wilson sample size now require strict
integers, preventing Boolean-to-integer coercion. Existing external importers continue to use
strict JSON validation.

## 5. Validation traceability matrix

| Boundary | Identity/version/schema | Order/duplicates/completeness | Digest | Time/domain | Public failure |
|---|---|---|---|---|---|
| Historical Dataset import | Manifest/dataset and schema 2 | Observation ordering; duplicate observation and channel/time rejection | Dataset digest | Provenance/custody chronology; observation cutoff | Typed read, syntax, schema, validation, duplicate, digest errors |
| Evidence Pack import | Definition/pack IDs and versions; schema 1 | Definition order; item/fact uniqueness and required coverage | Definition and pack digests | Aware observation/creation times; exact fact types | Typed read, syntax, schema, validation, digest errors |
| Rubric import | Evidence definition binding; schema 1 | Criterion/reason/rule uniqueness and closed state order | Rubric digest | Aware creation time | Typed read, syntax, schema, validation, digest errors |
| Ground Truth import/binding | Label-set/dataset/evidence/rubric IDs and versions; schema 1 | Canonical artifacts/reviews; duplicate and adjudication rules | Label-set plus referenced evidence/rubric digests | Review/adjudication/set chronology | Typed read, syntax, schema, validation, duplicate, digest, binding errors |
| Study execution | Definition/configuration and every governed artifact schema/binding | Exact cohort coverage; unique/canonical evidence packs | Every source digest and result digest | Request/start/completion chronology | `StudyExecutionValidationError` or digest subtype |
| Labelled evaluation | Configuration/execution/dataset/label bindings | Exact canonical prediction/label cohort; duplicate IDs and channel mismatch | Dataset, labels, execution, predictions, result | Evaluation chronology; closed prediction/outcome vocabularies | `EvaluationValidationError` or digest subtype |
| Aggregation | Definition/configuration/evaluation/schema bindings | Expected count; unique canonical observations | Evaluation and result digests | Strict non-negative counts and total identities | `EvaluationAggregationValidationError` or digest subtype |
| Statistical evaluation | Definition/configuration/aggregation/schema bindings | Duplicate statistical identity rejection | Aggregation and result digests | Strict counts; all denominators/MCC factors defined; aware chronology | `StatisticalEvaluationValidationError` or digest subtype |

Tests cover valid deterministic execution and meaningful negative states including identity,
version/schema, ordering, duplicate, completeness, channel, vocabulary, Boolean/negative count,
total, undefined-domain, naive-time, unknown-field, and digest mutation failures. Low-level
`model_copy(update=...)` is deliberately used in adversarial tests to prove validators reject
forged in-memory content where the normal typed constructor is bypassed.

## 6. Canonicalization and digest findings

Every canonicalizer uses UTF-8 JSON, sorted object keys, compact separators, retained Unicode,
`allow_nan=False`, SHA-256, and lowercase hexadecimal output. Ordered tuples are either governed
input order or explicitly canonicalized before hashing. Result digests exclude only their own
`result_digest` field. Source identity, versions, timestamps, metadata, content summaries, and
upstream artifact digests remain covered.

Every serialization method validates integrity before returning bytes. Mutation tests cover source
and final results. Equivalent inputs produce byte-identical output, including the complete
integration fixture. The small `_json_bytes` implementations are intentionally duplicated within
bounded canonicalizers: they are currently identical, and a shared generic framework would add
coupling without correcting a defect.

## 7. Mathematical verification findings

Independent fixtures verify accuracy, precision, recall/sensitivity, specificity, negative
predictive value, false-positive rate, false-negative rate, balanced accuracy, F1, MCC, and all
five Wilson intervals. Recall equals sensitivity; FPR equals `1 - specificity`; FNR equals
`1 - recall`. Probability metrics and interval bounds remain within `[0,1]`, MCC remains within
`[-1,1]`, and every interval contains its estimate.

The implementation uses Decimal precision 50 before final float conversion. Denominator validation
covers the binary cohort, predicted/actual positive and negative support, F1, and every MCC factor.
Undefined required mathematics rejects the complete statistical artifact.

Balanced accuracy retains the v0.9.8 governed plug-in Wilson convention using binary cohort size.
The field name, format document, ADR-027, and Research Protocol distinguish it from Wilson
intervals over direct binomial proportions and explicitly prohibit inferential interpretation.
Changing this convention requires a new version.

## 8. Documentation reconciliation findings

Every implemented boundary has an authoritative format document, relevant accepted ADR,
architecture placement, engineering/root/research navigation, changelog coverage, and explicit
exclusions. Formulas, schema versions, outcome vocabularies, source digests, chronological rules,
and release boundaries match code. Repository Markdown navigation contains no broken local `.md`
links found by the audit.

The changelog now records v0.9.8 as released and reserves Unreleased for v0.9.8.1 stabilization.
No document claims that real research ran or that Product approved a threshold. Historical ADRs
remain historical; ADR-021 already records its partial supersession of ADR-018 and ADR-019. This
audit adds no decision requiring ADR-028.

## 9. Dependency-direction findings

The implemented dependency direction is downstream:

```text
Dataset/Evidence/Labels
    -> Study Execution
    -> Labelled Evaluation
    -> Evaluation Aggregation
    -> Statistical Evaluation
```

An automated source-boundary test rejects downstream imports from upstream pipeline modules and
confirms application startup imports no backtesting service. Statistical evaluation only reads its
immutable aggregation; aggregation has no statistical dependency; labelled evaluation has no
aggregation dependency; study execution has no prediction or metric dependency. No circular
research dependency or runtime registration was found.

## 10. Defects corrected

1. Four downstream validators broadly caught `Exception`, risking concealment of programming
   defects and erasing typed integrity distinctions. Catches now name exact upstream digest or
   binding errors and translate integrity failures to each downstream digest subtype.
2. Aggregation count fields accepted Booleans through integer coercion. Counts, expected cohort
   size, and Wilson sample size now use strict integer validation.
3. Legacy immutable threshold-backtesting models silently ignored unknown direct-construction
   fields. They now consistently use `extra="forbid"`.
4. End-to-end, export-integrity, dependency-direction, complement-identity, interval-containment,
   Boolean-count, and direct unknown-field coverage was absent. Focused tests now protect it.

## 11. Risks accepted

- Balanced-accuracy interval is a governed plug-in convention, not a standard binomial interval.
  Its limitation and sample-size convention are explicit.
- Digest types remain bounded-context-specific rather than unified.
- Public contract naming reflects historical milestones and is not cosmetically normalized.
- Canonical JSON byte helpers remain locally duplicated to avoid coupling bounded contexts.
- Global identity uniqueness across separately submitted stateless requests requires a future
  registry and remains outside the approved architecture.

## 12. Deferred improvements

No cohort slicing, sensitivity/influence analysis, candidate comparison, interpretation, review
workflow, persistence, registry, external artifact import, API, scheduling, UI, AI, or runtime
signal work belongs to this stabilization patch. Those require separately approved milestones and,
where architectural, new decisions.

## 13. Final architecture status

The implemented research pipeline is internally consistent, strictly separated, deterministic,
immutable, synchronous, offline, stateless, fail-fast, side-effect free, and content-addressed at
artifact boundaries. Automated integration proves identity, version, schema, ordering, digest,
count, statistical, and canonical-byte continuity across the complete implemented chain.

## 14. No real research executed

This audit uses synthetic test fixtures only. It creates no persisted research artifact, evaluates
no real channel or dataset, compares/selects/recommends no threshold, creates no Product decision,
and changes no runtime behavior.

