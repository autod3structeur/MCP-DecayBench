"""
Benchmark runner.

Usage:
    python -m harness.run
    python -m harness.run --scanner reference-keyword
    python -m harness.run --mode cloud
    python -m harness.run --json results.json

snyk-agent-scan is cloud-only and needs SNYK_TOKEN in the environment. It is
registered at two severity thresholds so the leaderboard shows both a strict
"any finding" row and a "medium+ only" row; the gap between them is the
low-severity keyword noise the benchmark is built to expose.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from harness.scoring import score, render_table
from harness.adapters.reference_keyword import ReferenceKeywordAdapter
from harness.adapters.snyk_agent_scan import SnykAgentScanAdapter

CORPUS = Path(__file__).parent.parent / "corpus"

ADAPTERS = {}
for _a in [
    ReferenceKeywordAdapter(),
    SnykAgentScanAdapter(min_severity="low"),
    SnykAgentScanAdapter(min_severity="medium"),
]:
    ADAPTERS[_a.name] = _a


def load_corpus():
    samples = []
    for label_dir in ("malicious", "benign"):
        base = CORPUS / label_dir
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            lf = d / "label.json"
            if lf.exists():
                meta = json.loads(lf.read_text())
                meta["_dir"] = d
                samples.append(meta)
    return samples


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scanner", action="append")
    ap.add_argument("--mode", action="append", choices=["local", "cloud"])
    ap.add_argument("--json")
    args = ap.parse_args(argv)

    samples = load_corpus()
    if not samples:
        print("No samples found under corpus/.", file=sys.stderr)
        return 1

    chosen = args.scanner or list(ADAPTERS)
    modes = args.mode or ["local", "cloud"]

    results_by_scanner = {}
    raw_records = []
    for name in chosen:
        adapter = ADAPTERS.get(name)
        if adapter is None:
            print(f"unknown scanner: {name}", file=sys.stderr)
            continue
        for mode in modes:
            if mode not in adapter.supported_modes:
                continue
            recs = []
            for s in samples:
                res = adapter.scan(s["_dir"], mode)
                rec = {
                    "scanner": name, "mode": mode, "sample_id": s["id"],
                    "expect_flagged": s["expect_flagged"],
                    "flagged": res.flagged,
                    "hard_negative": s.get("hard_negative", False),
                    "error": res.error,
                }
                recs.append(rec)
                raw_records.append(rec)
            results_by_scanner[(name, mode)] = score(recs)

    print(render_table(results_by_scanner))
    if args.json:
        Path(args.json).write_text(json.dumps(raw_records, indent=2))
        print(f"\nraw records -> {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
