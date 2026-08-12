"""
Tests that (a) the corpus is well-formed, (b) every fixture server actually
runs and speaks MCP, and (c) the scoring math is correct. These run in CI with
no external scanner required.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
CORPUS = ROOT / "corpus"

sys.path.insert(0, str(ROOT))
from harness.scoring import score, Counts  # noqa: E402


def _all_samples():
    for label_dir in ("malicious", "benign"):
        for d in sorted((CORPUS / label_dir).iterdir()):
            if (d / "label.json").exists():
                yield d


def test_corpus_nonempty():
    assert list(_all_samples()), "corpus is empty"


@pytest.mark.parametrize("sample_dir", list(_all_samples()), ids=lambda d: d.name)
def test_label_wellformed(sample_dir):
    meta = json.loads((sample_dir / "label.json").read_text())
    assert meta["id"] == sample_dir.name
    assert meta["label"] in ("malicious", "benign")
    assert meta["expect_flagged"] == (meta["label"] == "malicious")
    assert meta["rationale"].strip(), "every sample needs a rationale"
    if meta["label"] == "malicious":
        assert meta["attack_class"], "malicious samples need an attack_class"
        assert meta["hard_negative"] is False
    if meta.get("hard_negative"):
        assert meta["label"] == "benign"


@pytest.mark.parametrize("sample_dir", list(_all_samples()), ids=lambda d: d.name)
def test_server_speaks_mcp(sample_dir):
    """Launch the fixture server, do the handshake, and get a tools list back."""
    server = sample_dir / "server.py"
    proc = subprocess.Popen(
        [sys.executable, str(server)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    reqs = (
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n"
        + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}) + "\n"
    )
    out, _ = proc.communicate(reqs, timeout=10)
    lines = [json.loads(l) for l in out.splitlines() if l.strip()]
    assert any(r.get("id") == 1 for r in lines), "no initialize response"
    tl = next(r for r in lines if r.get("id") == 2)
    assert "tools" in tl["result"]


def test_hard_negatives_exist():
    hn = [d for d in _all_samples()
          if json.loads((d / "label.json").read_text()).get("hard_negative")]
    assert hn, "benchmark has no hard negatives; it measures nothing"


def test_scoring_math():
    recs = [
        {"expect_flagged": True,  "flagged": True,  "hard_negative": False, "error": None},  # tp
        {"expect_flagged": True,  "flagged": False, "hard_negative": False, "error": None},  # fn
        {"expect_flagged": False, "flagged": True,  "hard_negative": True,  "error": None},  # fp + HN
        {"expect_flagged": False, "flagged": False, "hard_negative": True,  "error": None},  # tn
    ]
    c = score(recs)
    assert (c.tp, c.fp, c.tn, c.fn) == (1, 1, 1, 1)
    assert c.precision() == 0.5
    assert c.recall() == 0.5
    assert c.hard_neg_fpr() == 0.5
