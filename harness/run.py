"""
Benchmark runner.

Usage:
    python -m harness.run                      # run all installed scanners, all modes
    python -m harness.run --scanner reference-keyword
    python -m harness.run --mode local
    python -m harness.run --json results.json  # also dump raw per-sample records

Loads every sample under corpus/, runs each selected adapter in each selected
mode, scores the results, and prints the leaderboard. Adapters whose tool is
not installed report an error per sample and are still shown (with err count),
so a missing external scanner never breaks the run.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from harness.scoring import score, render_table
from harness.adapters.mcp_scan import McpScanAdapter
from harness.adapters.reference_keyword import ReferenceKeywordAdapter

CORPUS = Path(__file__).parent.parent / "corpus"

ADAPTERS = {
    a.name: a for a in [
        ReferenceKeywordAdapter(),
        McpScanAdapter(),
        # add CiscoScannerAdapter(), ESentireAdapter() here as they are wrapped
    ]
}


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
    ap.add_argument("--scanner", action="append", help="limit to named scanner(s)")
    ap.add_argument("--mode", action="append", choices=["local", "cloud"],
                    help="limit to mode(s); default both where supported")
    ap.add_argument("--json", help="dump raw per-sample records to this path")
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
                    "scanner": name,
                    "mode": mode,
                    "sample_id": s["id"],
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
