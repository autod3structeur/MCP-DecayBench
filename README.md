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

Measured against the v1 corpus: **10 samples** (2 attacks, 8 hard negatives).
Two real scanners are wrapped, each in the mode it actually supports.
`snyk-agent-scan` is cloud/token-gated; `cisco-mcp-scanner` (YARA) runs offline.

| scanner                     | mode  | prec  | rec   | F1    | HN-FPR |
|-----------------------------|-------|-------|-------|-------|--------|
| cisco-mcp-scanner (YARA)    | local | 0.500 | 1.000 | 0.667 | 0.250  |
| snyk-agent-scan (>=medium)  | cloud | 0.500 | 1.000 | 0.667 | 0.250  |
| snyk-agent-scan (>=low)     | cloud | 0.222 | 1.000 | 0.364 | 0.875  |

*HN-FPR = false-positive rate on hard negatives (lower is better).*

### The finding: same score, different blind spots

Both real scanners keep perfect recall (they catch every attack) and, at their
best settings, land at the same HN-FPR (0.25). But they false-positive on
**different** legitimate servers, so the aggregate number hides the real story:

- **Both** flag `b03` (a standard Git credential helper). Neither tool
  distinguishes a legitimate helper that reads `~/.ssh/config` and
  `~/.git-credentials` from credential harvesting — a shared blind spot.
- **Only Cisco** flags `b04`, a defensive hardening auditor, because its YARA
  path rules match `/etc/shadow` / `/etc/passwd` — the very files the tool
  exists to protect.
- **Only snyk (>=medium)** flags `b06`, a backup tool whose description says
  "ignore all previous .gitignore patterns" — legitimate archiving semantics
  that trip its injection heuristics.

A defender running only one of these tools inherits that tool's specific gaps.
Running snyk untuned (`>=low`) is worse: HN-FPR 0.875 — it flags almost every
legitimate server, including credential helpers, backups, i18n tools, and a
security-awareness prompt library.

### What held up

`b05` (a base64 decoder with encoded example data) fooled neither scanner. And
recall stayed 1.0 throughout: harder hard negatives raised false positives
without causing either tool to miss a real attack.

## Quick start

```bash
python -m pytest harness/test_benchmark.py -q       # verify corpus + fixtures + scoring
python -m harness.run --scanner reference-keyword   # offline straw-man, no token
```

Benchmark the real scanners:

```bash
# Cisco YARA — offline, no token
pip install uv
uv tool install --python 3.13 cisco-ai-mcp-scanner
python -m harness.run --scanner "cisco-mcp-scanner[>=low]" --mode local

# Snyk agent-scan — cloud, needs a token from https://app.snyk.io/account
export SNYK_TOKEN="your-token"
python -m harness.run --scanner "snyk-agent-scan[>=medium]" --mode cloud
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
corpus/malicious/ poisoned servers, one dir each (server.py + label.json)
corpus/benign/ clean servers, incl. hard negatives
fixtures/ shared MCP-server template + authoring helper
harness/ adapters, scoring, runner, tests
docs/ TAXONOMY.md, METHODOLOGY.md
## Documentation

- `docs/TAXONOMY.md` — attack classes, each anchored to a published source.
- `docs/METHODOLOGY.md` — labeling philosophy, local-vs-cloud stance, limitations.
- `corpus/SCHEMA.md` — the sample and scoring contract.
- `CONTRIBUTING.md` — how to add a sample (especially a good hard negative).

## Status

The corpus is hard enough to *separate* scanners rather than let everyone pass,
but still small (10 samples, one cloud snapshot). Contributing adversarial hard
negatives that split the tools further is the highest-leverage contribution.
See `CONTRIBUTING.md`.

## License

Apache-2.0.
