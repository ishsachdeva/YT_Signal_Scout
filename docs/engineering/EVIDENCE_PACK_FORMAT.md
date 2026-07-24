# Reviewer Evidence Pack JSON Format

Reviewer evidence uses strict JSON schema version 1 and enters only through
`EvidencePackImporter`. One document contains a complete evidence-pack definition and one concrete
pack. No repository evidence instance is created by this specification.

## Top-level shape

```json
{
  "schema_version": 1,
  "definition": {},
  "pack": {}
}
```

## Definition

`EvidencePackDefinition` records stable identity/version, name, purpose, timezone-aware creation
time, ordered evidence item definitions, and a SHA-256 digest. Every item definition has a stable
ID, title, description, required state, and ordered typed fact definitions.

Fact definitions declare:

- stable fact name;
- Boolean, integer, float, text, or timestamp type;
- required and repeatable states;
- optional semantic unit; and
- human-readable description.

Definition order is authoritative. IDs are unique and no default items are inserted.

## Concrete evidence pack

`EvidencePack` records stable identity/version, exact definition identity/version/digest,
timezone-aware creation time, one snapshot, ordered items, and its own SHA-256 digest.

`EvidenceSnapshot` binds the pack to one exact dataset ID/version, observation ID, channel ID,
snapshot ID/version, and timezone-aware observation time. Pack creation cannot precede the
observation.

Every evidence item must match the definition's identity and order. Facts must use defined names,
exact types, and exact semantic units. Required facts cannot be omitted. A repeatable fact requires
a subject ID, such as a video identity; a non-repeatable fact prohibits one. Fact name/subject pairs
are unique and canonically ordered.

Evidence packs contain typed facts only. They contain no candidate threshold, predicted label,
other reviewer decision, score, ranking, generated narrative, image, thumbnail, screenshot, OCR,
or executable calculation.

## Canonicalization and integrity

The definition digest covers its complete canonical content except `digest`. The pack digest does
the same for the concrete definition-bound pack. Canonical JSON uses UTF-8, sorted object keys,
explicit array order, retained Unicode, no insignificant whitespace, and no non-finite numbers.

`EvidencePackCanonicalizer` calculates/verifies both digests and serializes a validated import to
stable bytes.

## Strict validation

Import rejects unsupported schemas, missing or unknown fields, coercive primitives, naive times,
duplicate identities, non-finite floats, definition/pack mismatch, missing or unknown facts,
type/unit/repeatability mismatch, order mismatch, and digest mismatch. No partial result is
returned. Typed failures distinguish reads, syntax, schema, structure, and integrity.

Import performs no evidence generation, acquisition, labelling, study execution, Product decision,
or runtime behavior. See ADR-023.
