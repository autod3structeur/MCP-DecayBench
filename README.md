# mcp-poison-bench

**A labeled benchmark for MCP security scanners — with hard negatives that measure whether a scanner cries wolf.**

Several open-source scanners now detect tool poisoning and prompt injection in
Model Context Protocol (MCP) servers. What's missing is a way to *compare* them:
nobody can currently answer "is scanner A better than scanner B?" with a number.
Field reports show these tools flag legitimate behavior as vulnerable, but there
is no standard corpus that quantifies it.

`mcp-poison-bench` is that corpus and the harness to score against it.

## What makes it different

The value isn't a big pile of obvious attacks — it's the **hard negatives**:
benign MCP servers deliberately crafted to *look* malicious, so a scanner's
real-world noise is measurable. The headline metric is **HN-FPR** — the
false-positive rate on those tricky-benign servers.

```
scanner              mode     prec    rec     F1  HN-FPR  err
-------------------------------------------------------------
reference-keyword    local  0.500 0.500 0.500 0.500    0
mcp-scan             local    ...   ...   ...   ...    0
mcp-scan             cloud    ...   ...   ...   ...    0

HN-FPR = false-positive rate on hard negatives (lower is better).
```

The bundled `reference-keyword` scanner is a straw man included on purpose: it
catches obvious poison but false-positives on legitimate "IMPORTANT / ignore
cached copy" phrasing and misses capability-combination attacks that carry no
suspicious keywords — demonstrating exactly why naive scanning fails and why the
hard negatives matter.

## Quick start

```bash
pip install pytest
python -m pytest harness/test_benchmark.py -q   # verify corpus + fixtures + scoring
python -m harness.run                           # run the leaderboard
```

To benchmark a real scanner, install it and re-run:

```bash
pip install mcp-scan
python -m harness.run --scanner mcp-scan
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

v1 is intentionally small and defensible. Contributions that increase
*discrimination* — new hard negatives and new attack classes — are the most
valuable. See `CONTRIBUTING.md`.

## License

Apache-2.0.
