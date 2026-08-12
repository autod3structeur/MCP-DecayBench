"""
Scoring: turn per-sample (flagged vs expected) into the benchmark metrics.

Headline metrics: precision, recall, F1 over the whole corpus.
The metric this benchmark exists for: false-positive rate on HARD NEGATIVES,
reported separately, because obvious-benign samples inflate a scanner's apparent
precision while hiding whether it actually cries wolf on realistic edge cases.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0
    hard_neg_total: int = 0
    hard_neg_fp: int = 0
    errors: int = 0

    def precision(self) -> Optional[float]:
        d = self.tp + self.fp
        return self.tp / d if d else None

    def recall(self) -> Optional[float]:
        d = self.tp + self.fn
        return self.tp / d if d else None

    def f1(self) -> Optional[float]:
        p, r = self.precision(), self.recall()
        if not p or not r:
            return None
        return 2 * p * r / (p + r)

    def hard_neg_fpr(self) -> Optional[float]:
        return self.hard_neg_fp / self.hard_neg_total if self.hard_neg_total else None


def score(records) -> Counts:
    """
    records: iterable of dicts with keys:
        expect_flagged (bool), flagged (bool), hard_negative (bool), error (str|None)
    """
    c = Counts()
    for r in records:
        if r.get("error"):
            c.errors += 1
            continue
        expected = r["expect_flagged"]
        got = r["flagged"]
        if r.get("hard_negative"):
            c.hard_neg_total += 1
            if got:  # flagged a hard negative
                c.hard_neg_fp += 1
        if expected and got:
            c.tp += 1
        elif expected and not got:
            c.fn += 1
        elif not expected and got:
            c.fp += 1
        else:
            c.tn += 1
    return c


def _fmt(x):
    return "  n/a" if x is None else f"{x:5.3f}"


def render_table(results_by_scanner: dict) -> str:
    """
    results_by_scanner: {(scanner_name, mode): Counts}
    Returns a plain-text leaderboard.
    """
    header = f"{'scanner':<20} {'mode':<6} {'prec':>6} {'rec':>6} {'F1':>6} {'HN-FPR':>7} {'err':>4}"
    lines = [header, "-" * len(header)]
    for (name, mode), c in sorted(results_by_scanner.items(),
                                  key=lambda kv: (-(kv[1].f1() or 0), kv[0])):
        lines.append(
            f"{name:<20} {mode:<6} {_fmt(c.precision())} {_fmt(c.recall())} "
            f"{_fmt(c.f1())} {_fmt(c.hard_neg_fpr())} {c.errors:>4}"
        )
    lines.append("")
    lines.append("HN-FPR = false-positive rate on hard negatives (lower is better).")
    return "\n".join(lines)
