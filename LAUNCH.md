# Launch Materials — MCP-DecayBench

## GitHub "About" description (short, goes in repo settings)

> A labeled benchmark for MCP security scanners — with hard negatives that
> measure whether a scanner cries wolf. Quantifies detection vs. false-positive
> noise on tool-poisoning and prompt-injection.

Topics/tags to add in repo settings (GitHub "topics"):
`mcp` `model-context-protocol` `ai-security` `llm-security` `prompt-injection`
`tool-poisoning` `benchmark` `security-tools` `agent-security` `mcp-security`

---

## One-line pitch (for HN title, LinkedIn headline)

> MCP-DecayBench: I benchmarked MCP security scanners on how noisy they are —
> not just what they catch.

---

## Hacker News / Reddit r/netsec post

**Title:** MCP-DecayBench – a benchmark that measures whether MCP security scanners cry wolf

**Body:**

MCP security scanners (Snyk's agent-scan, Cisco's mcp-scanner, and others) are
getting adopted fast, but there's no standard way to compare them. Everyone's
noticed they produce false positives; nobody had quantified it.

So I built a small labeled benchmark. The idea isn't a big pile of obvious
attacks — it's the **hard negatives**: benign MCP servers deliberately built to
*look* malicious (a backup tool that legitimately needs file-read + network
egress; a caching tool whose description legitimately says "IMPORTANT"). The
headline metric is HN-FPR: the false-positive rate on those tricky-benign
servers.

Two things fell out of the first run against snyk-agent-scan:

1. The severity threshold is everything. At its low threshold it flags *every*
   hard negative (HN-FPR 1.0). Filtering to medium+ severity removes all that
   noise with zero loss of detection. A single "is it safe" number is
   misleading — the whole story is in the threshold.

2. Capability-combination attacks resist static detection. My malicious
   exfil-combo and my benign backup are functionally similar (both pair read +
   egress), and description-level analysis gives them near-identical signals.
   The malicious intent is in how the capabilities are wired, not in any text a
   scanner can read.

Each sample is a real runnable stdio MCP server, not inert JSON, so scanners are
tested the way they actually run. Adapters wrap real tools; results are
reproducible (offline scanners) or reported as cloud snapshots (token-gated
ones). Contributions of new hard negatives especially welcome.

Repo: https://github.com/autod3structeur/MCP-DecayBench

---

## LinkedIn post

I kept reading that MCP security scanners are noisy — lots of false positives on
legitimate servers. But "noisy" wasn't a number anyone could point to. So I
built a benchmark to make it one.

MCP-DecayBench measures MCP security scanners on a labeled corpus whose core is
its **hard negatives**: benign servers deliberately crafted to look suspicious.
The headline metric is the false-positive rate on those — because catching
obvious attacks is easy; *not* crying wolf on legitimate tools is the hard part.

First result against snyk-agent-scan was clean and honest:
→ At a low severity threshold it flags every tricky-benign server (100% false
positives).
→ Filtered to medium+ severity: zero false positives, full detection.
→ And it surfaced a real blind spot — capability-combination attacks look almost
identical to legitimate high-capability tools under static analysis.

The benchmark found a limitation in its *own* corpus on the first run, which is
exactly what a good benchmark should do.

Built in Python, fully reproducible, contributions welcome — especially new hard
negatives. Link in comments.

#AISecurity #LLMSecurity #MCP #PromptInjection #CyberSecurity #OpenSource
#ThreatDetection #AppSec #AIagents #SecurityResearch

---

## X / Twitter thread (optional)

1/ MCP security scanners are getting adopted fast. They're also noisy. Nobody
had measured *how* noisy. So I built MCP-DecayBench — a benchmark that scores
scanners on false positives, not just detection. 🧵

2/ The trick isn't obvious attacks — it's hard negatives: benign MCP servers
built to LOOK malicious. A backup tool that needs read+egress. A cache whose
description says "IMPORTANT." If a scanner flags those, that's the noise we
measure.

3/ First run vs snyk-agent-scan:
• low severity threshold → flags 100% of hard negatives
• medium+ threshold → 0% false positives, full detection
The threshold IS the story. One "safe/unsafe" number hides all of it.

4/ It also surfaced a blind spot: capability-combination attacks (read + exfil)
look nearly identical to legitimate high-capability tools under static analysis.
The intent is in the wiring, not the text.

5/ Every sample is a real runnable MCP server, tested the way scanners actually
run. Python, reproducible, Apache-2.0. New hard negatives especially welcome:
https://github.com/autod3structeur/MCP-DecayBench

#AISecurity #MCP #LLMSecurity #PromptInjection

---

## Hashtag sets (pick per platform)

**Core (always):** #AISecurity #LLMSecurity #MCP #PromptInjection

**LinkedIn (broader reach):** add #CyberSecurity #OpenSource #ThreatDetection
#AppSec #AIagents #SecurityResearch #InfoSec

**X (tighter):** #AISecurity #MCP #LLMSecurity #PromptInjection #infosec

**GitHub topics (not hashtags):** mcp, model-context-protocol, ai-security,
llm-security, prompt-injection, tool-poisoning, benchmark, security-tools,
agent-security, mcp-security
