[![ci](https://github.com/autod3structeur/MCP-DecayBench/actions/workflows/ci.yml/badge.svg)](https://github.com/autod3structeur/MCP-DecayBench/actions/workflows/ci.yml)

# MCP-DecayBench

**A labeled benchmark for MCP security scanners - with hard negatives that measure whether a scanner cries wolf.**

Several open-source scanners now detect tool poisoning and prompt injection in
Model Context Protocol (MCP) servers. What's missing is a way to *compare* them:
nobody can currently answer "is scanner A better than scanner B?" with a number.

`MCP-DecayBench` is that corpus and the harness to score against it.

## What makes it different

The value isn't a big pile of obvious attacks - it's the **hard negatives**:
benign MCP servers deliberately crafted to *look* malicious, so a scanner's
real-world noise is measurable. The headline metric is **HN-FPR** - the
false-positive rate on those tricky-benign servers.

## Results

Measured against the v1 corpus: **10 samples** (2 attacks, 8 hard negatives).
`snyk-agent-scan` is cloud/token-gated; `cisco-mcp-scanner` (YARA) runs offline.

| scanner                     | mode  | prec  | rec   | F1    | HN-FPR |
|-----------------------------|-------|-------|-------|-------|--------|
| cisco-mcp-scanner (YARA)    | local | 0.500 | 1.000 | 0.667 | 0.250  |
| snyk-agent-scan (>=medium)  | cloud | 0.500 | 1.000 | 0.667 | 0.250  |
| snyk-agent-scan (>=low)     | cloud | 0.222 | 1.000 | 0.364 | 0.875  |

*HN-FPR = false-positive rate on hard negatives (lower is better).*

### The finding: same score, different blind spots

Both real scanners keep perfect recall (they catch every attack) and, at their
best settings, land at the same HN-FPR (0.25) - but they false-positive on
**different** legitimate servers:

- **Both** flag `b03` (a standard Git credential helper) that reads
  `~/.ssh/config` and `~/.git-credentials` - a shared blind spot.
- **Only Cisco** flags `b04`, a defensive hardening auditor, because its YARA
  path rules match `/etc/shadow` / `/etc/passwd` - the files it exists to protect.
- **Only snyk (>=medium)** flags `b06`, a backup tool whose description says
  "ignore all previous .gitignore patterns" - legitimate archiving semantics.

Run only one tool and you inherit its specific gaps. Untuned, snyk (`>=low`)
flags almost every legitimate server (HN-FPR 0.875).

## Quick start

    python -m pytest harness/test_benchmark.py -q
    python -m harness.run --scanner reference-keyword

Benchmark the real scanners:

    # Cisco YARA - offline, no token
    uv tool install --python 3.13 cisco-ai-mcp-scanner
    python -m harness.run --scanner "cisco-mcp-scanner[>=low]" --mode local

    # Snyk - cloud, needs a token from https://app.snyk.io/account
    export SNYK_TOKEN="your-token"
    python -m harness.run --scanner "snyk-agent-scan[>=medium]" --mode cloud

## How it works

- Each sample is a runnable stdio MCP server plus a `label.json` with ground
  truth, an attack-class tag, and a written rationale. Scanners enumerate tools
  the real way - not from inert JSON.
- Each scanner is wrapped in a thin adapter reducing its output to one boolean
  per server.
- Scanners with offline and cloud modes are reported separately (see
  `docs/METHODOLOGY.md`).

## Layout

    corpus/malicious/  poisoned servers (server.py + label.json)
    corpus/benign/     clean servers, incl. hard negatives
    fixtures/          shared MCP-server template
    harness/           adapters, scoring, runner, tests
    docs/              TAXONOMY.md, METHODOLOGY.md

## Documentation

- `docs/TAXONOMY.md` - attack classes, anchored to published sources.
- `docs/METHODOLOGY.md` - labeling philosophy, local-vs-cloud stance, limits.
- `CONTRIBUTING.md` - how to add a sample (especially a hard negative).

## Status

The corpus is hard enough to separate scanners rather than let everyone pass,
but still small. Contributing adversarial hard negatives is the highest-leverage
contribution.

## License

Apache-2.0.
