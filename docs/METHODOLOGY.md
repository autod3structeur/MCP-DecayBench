# Methodology

This document is the load-bearing part of the benchmark. A benchmark's
authority comes from its labels being defensible, so the reasoning is written
down and every label is anchored to a source.

## What is measured

Each MCP server sample is run through a scanner, whose output is reduced to one
boolean — *did it raise a finding on this server?* — and compared to ground
truth. See `corpus/SCHEMA.md` for the exact contract.

Reported metrics:

- **Precision / Recall / F1** over the whole corpus.
- **Hard-negative false-positive rate (HN-FPR)** — the fraction of deliberately
  tricky *benign* servers a scanner wrongly flags. This is the headline number.
  Field reports of existing scanners describe them flagging intended behavior as
  vulnerable and producing findings that "reflect intended behavior, not
  vulnerabilities"; HN-FPR is designed to quantify exactly that failure.

## Why hard negatives are the core

A corpus of obviously-malicious vs obviously-clean servers measures almost
nothing — every scanner scores near 100%. Discrimination comes from **benign
servers that look malicious**: a backup tool that legitimately needs file-read
plus network-egress (resembles an exfiltration toxic-flow), a caching tool whose
description legitimately says "ignore cached copy / IMPORTANT" (resembles a
hidden-instruction payload), config that legitimately changes across versions
(resembles a rug pull). Each hard negative has a written rationale explaining
why it is genuinely safe. If a scanner author disputes a label, the rationale is
the thing to argue with — and that argument is the benchmark working as intended.

## Local vs cloud mode

Some scanners have two modes: a local/offline path and a cloud path that sends
tool metadata to a vendor API for classification. These differ in accuracy,
determinism, and privacy. We run and report **both, in separate columns**:

- **local** — deterministic, offline, reproducible. The headline reproducible
  number. Note this is often the *weaker* configuration of a given tool.
- **cloud** — reflects how the tool is used in practice, but is
  non-deterministic (the vendor model changes over time) and transmits corpus
  tool metadata to a third party. Cloud results are timestamped and should be
  treated as a snapshot, not a reproducible constant.

Neither mode is "the real" score; reporting both is the honest position.

## Scope of v1

v1 is intentionally small and defensible rather than large and noisy. Every
sample is hand-authored with a rationale and a source. Expansion happens by
adding samples that increase *discrimination* (new hard negatives, new attack
classes), not by inflating the count.

## Reproducing

```bash
pip install pytest
python -m pytest harness/test_benchmark.py -q     # integrity + fixtures + scoring
python -m harness.run                             # leaderboard, all installed scanners
python -m harness.run --scanner mcp-scan --mode local   # one tool, reproducible mode
```

External scanners are optional: if a tool is not installed, its rows report
per-sample errors and the run still completes. To benchmark a real scanner,
install it per its own instructions (e.g. `pip install mcp-scan`) and re-run.

## Limitations (stated plainly)

- Fixture servers declare attacks in metadata; they do not execute malicious
  behavior. This benchmarks *static description/definition* analysis, which is
  what these scanners target. Runtime-behavior scanners are out of scope for v1.
- The boolean reduction (flagged / not) discards severity and location. A future
  version may add per-finding localization scoring.
- Corpus size is small by design; treat absolute scores as indicative and the
  *ordering* and *HN-FPR* as the useful signals.
## Addendum: scanner realities discovered in practice

### snyk-agent-scan (formerly mcp-scan) is cloud-only and token-gated

The Invariant Labs `mcp-scan` package was renamed to `snyk-agent-scan`
(run via `uvx snyk-agent-scan@latest`). Two consequences for reproducibility:

- **No offline mode.** Analysis runs Snyk-side against an `analysis-machine`
  API endpoint and requires a `SNYK_TOKEN`. The old `--local-only` policy check
  no longer exists. This scanner therefore has only a **cloud** column here.
- **Corpus metadata leaves the machine.** Tool names/descriptions are sent to
  Snyk for analysis. Reproducing this scanner's rows requires a Snyk account.
- **Non-interactive runs** need `--dangerously-run-mcp-servers` (skip the
  per-server consent prompt) and `--suppress-mcpserver-io=true`.

### Severity thresholding is a scoring decision, not a detail

snyk-agent-scan emits both high-severity findings (e.g. `E001 Prompt injection
found`, severity `critical`) and low-severity keyword warnings (e.g. `W001
Dangerous Words Detection`, which fires on the literal word "important"). Whether
a server is "flagged" depends on the severity threshold applied:

- `>=low`  counts any issue, including keyword warnings.
- `>=medium` counts only substantive findings.

We report both. The gap between them is exactly the signal-vs-noise story: the
low threshold false-positives on legitimate descriptions that happen to contain
words like "important" (see hard negative `b02_imperative_desc`), while the
medium threshold suppresses that noise. A scanner's headline quality is not one
number but the shape of this tradeoff.
## Addendum: scanner realities and real results

### snyk-agent-scan (formerly mcp-scan) is cloud-only and token-gated
Invariant Labs' `mcp-scan` was renamed to `snyk-agent-scan` (run via
`uvx snyk-agent-scan@latest`). Analysis runs Snyk-side against an
`analysis-machine` API and requires `SNYK_TOKEN`; the old offline `--local-only`
policy check no longer exists. Consequences: this scanner has only a **cloud**
column here, corpus tool metadata leaves the machine, and reproducing its rows
requires a Snyk account. Non-interactive runs need `--dangerously-run-mcp-servers`
and `--suppress-mcpserver-io=true`.

### Severity is a scoring decision
snyk-agent-scan emits E-class findings (e.g. `E001 Prompt injection`, severity
in `extra_data`) and W-class warnings (e.g. `W001` dangerous words, `W018`
workspace data exposure, `W019/W020` destructive/local capabilities). Whether a
server is "flagged" depends on the severity threshold. We report both `>=low`
and `>=medium`; the gap between them is the signal-vs-noise story.

### Observed result (v1 corpus)
At `>=low`, snyk flags both hard negatives — but on capability heuristics
(W018/W020 on the legit backup; W001/W016/W018 on the legit cache), not only
keywords. At `>=medium` those drop and precision/recall/F1 all reach 1.0. The
malicious exfil-combo and benign backup produce near-identical low-severity
signals, which is why v2 sharpens the malicious exfil-combo to carry an explicit
hidden-instruction payload distinguishing it from legitimate high-capability
tools.
