[![ci](https://github.com/autod3structeur/MCP-DecayBench/actions/workflows/ci.yml/badge.svg)](https://github.com/autod3structeur/MCP-DecayBench/actions/workflows/ci.yml)

# MCP-DecayBench

**A labeled benchmark for MCP security scanners — with hard negatives that measure whether a scanner cries wolf.**

Several open-source scanners now detect tool poisoning and prompt injection in
Model Context Protocol (MCP) servers. What's missing is a way to *compare* them:
nobody can currently answer "is scanner A better than scanner B?" with a number.
Field reports show these tools flag legitimate behavior as vulnerable, but there
is no standard corpus that quantifies it.

`MCP-DecayBench` is that corpus and the harness to score against it.

## What makes it different

The value isn't a big pile of obvious attacks — it's the **hard negatives**:
benign MCP servers deliberately crafted to *look* malicious, so a scanner's
real-world noise is measurable. The headline metric is **HN-FPR** — the
false-positive rate on those tricky-benign servers.

## Results

Measured against v1 of the corpus (4 samples: 2 attacks, 2 hard negatives).
`snyk-agent-scan` is the renamed successor to Invariant Labs' `mcp-scan`; it is
cloud-only and token-gated (see `docs/METHODOLOGY.md`). Severity thresholds are
reported separately because *what counts as a finding* is itself a scoring
decision.

| scanner                     | mode  | prec  | rec   | F1    | HN-FPR |
|-----------------------------|-------|-------|-------|-------|--------|
| snyk-agent-scan (>=medium)  | cloud | 1.000 | 1.000 | 1.000 | 0.000  |
| snyk-agent-scan (>=low)     | cloud | 0.500 | 1.000 | 0.667 | 1.000  |
| reference-keyword (bundled) | local | 0.500 | 0.500 | 0.500 | 0.500  |

*HN-FPR = false-positive rate on hard negatives (lower is better).*

### Two findings

**1. The severity threshold is everything.** At its `low` threshold,
snyk-agent-scan flags *every* hard negative (HN-FPR 1.0) — its capability and
keyword heuristics fire on legitimate high-capability servers (a backup tool
that needs file-read + network-egress; a caching tool whose description
legitimately says "IMPORTANT"). Filtering to `medium+` severity removes all of
that noise with **no loss of detection** (HN-FPR 0.0, recall 1.0). The scanner's
real-world usefulness depends entirely on where you set the bar — a single
"is it safe?" number is misleading.

**2. Capability-combination attacks resist static separation.** Our malicious
exfil-combo (`m02`) and our benign backup (`b01`) are functionally similar —
both pair file-read with network-egress. Static description analysis assigns
them nearly identical signals; the malicious intent lives in *how* the
capabilities are wired, not in any text a scanner can read. This is a
fundamental limit of description-level scanning, not a quirk of one tool.
Sharpening this boundary is a v2 roadmap item (see `CONTRIBUTING.md`).

The bundled `reference-keyword` scanner is a straw man included on purpose: it
catches obvious poison but false-positives on legitimate "IMPORTANT" phrasing
and misses capability-combination attacks that carry no suspicious keywords —
demonstrating why naive scanning fails and why the hard negatives matter.

## Quick start

```bash
python -m pytest harness/test_benchmark.py -q   # verify corpus + fixtures + scoring
python -m harness.run --scanner reference-keyword   # runs offline, no token
```

To benchmark snyk-agent-scan (needs a Snyk token; analysis is cloud-side):

```bash
pip install uv
export SNYK_TOKEN="your-token"    # from https://app.snyk.io/account
python -m harness.run --scanner "snyk-agent-scan[>=medium]" --mode cloud
python -m harness.run --scanner "snyk-agent-scan[>=low]" --mode cloud
```

Missing scanners degrade gracefully (they report per-sample errors; the run
still completes).

## How it works

- Each sample is a tiny, **runnable stdio MCP server** plus a `label.json` with
  ground truth, an attack-class tag, an OWASP-MCP mapping, and a written
  rationale. Scanners connect and enumerate tools the real way — not from inert
  JSON.
- Each scanner is wrapped in a thin **adapter** that reduces its native output
  to one boolean per server. Adding a scanner is one small class.
- Scanners with an offline and a vendor-API mode are run in **both, reported
  separately** (see `docs/METHODOLOGY.md`).

## Layout

```
corpus/malicious/  poisoned servers, one dir each (server.py + label.json)
corpus/benign/     clean servers, incl. hard negatives
fixtures/          shared MCP-server template + authoring helper
harness/           adapters, scoring, runner, tests
docs/              TAXONOMY.md, METHODOLOGY.md
```

## Documentation

- `docs/TAXONOMY.md` — attack classes, each anchored to a published source.
- `docs/METHODOLOGY.md` — labeling philosophy, local-vs-cloud stance, limitations.
- `corpus/SCHEMA.md` — the sample and scoring contract.
- `CONTRIBUTING.md` — how to add a sample (especially a good hard negative).

## Status

v1 is intentionally small and defensible. The benchmark already surfaced a real
limitation *in its own corpus* (finding 2 above) — which is the point.
Contributions that increase *discrimination* — new hard negatives, sharper
capability-combo separation, new attack classes — are the most valuable. See
`CONTRIBUTING.md`.

## License

Apache-2.0.
