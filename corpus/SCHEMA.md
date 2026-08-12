# Corpus Sample Schema

Every sample in this benchmark is a directory under `corpus/malicious/` or
`corpus/benign/` containing exactly two files:

```
corpus/<label>/<sample_id>/
├── label.json      # ground truth + rationale (machine + human readable)
└── server.py       # a minimal, runnable stdio MCP server the scanner connects to
```

The scanner under test is pointed at a generated config that launches
`server.py`, connects over stdio, and retrieves the tool/prompt/resource
definitions - i.e. the tools are tested the *real* way, not as inert JSON.

## `label.json` fields

| field            | type      | meaning                                                                 |
|------------------|-----------|-------------------------------------------------------------------------|
| `id`             | string    | Unique sample id, matches the directory name.                           |
| `label`          | string    | `"malicious"` or `"benign"`. The ground truth.                          |
| `attack_class`   | string\|null | For malicious samples, one of the taxonomy keys in `docs/TAXONOMY.md`. `null` for benign. |
| `hard_negative`  | bool      | `true` if this benign sample is deliberately crafted to *look* suspicious (the moat). Always `false` for malicious. |
| `owasp_mcp`      | string\|null | Mapped OWASP MCP Top 10 id (e.g. `"MCP01"`) where applicable.         |
| `rationale`      | string    | Human-readable justification for the label. **Required for every sample; load-bearing for hard negatives.** |
| `source`         | string\|null | Citation/URL anchoring the attack class or the "this is legitimate" claim. |
| `expect_flagged` | bool      | What a *correct* scanner should do: `true` = should raise a finding, `false` = should stay silent. Equals `(label == "malicious")`. Kept explicit so scoring never re-derives it. |

## Scoring contract

A scanner's output is reduced to one boolean per sample: **did it flag this
server or not.** That boolean is compared against `expect_flagged`:

- malicious + flagged   → true positive
- malicious + not flagged → false negative (missed attack)
- benign + flagged      → false positive (crying wolf)
- benign + not flagged  → true negative

Precision, recall, F1 are computed over the whole corpus; a separate
**false-positive rate on hard negatives** is reported, because that is the
number this benchmark exists to expose.
