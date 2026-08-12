"""
A deliberately naive built-in scanner: pure keyword/regex matching over tool
descriptions. It exists for two reasons:

1. The harness produces a leaderboard out of the box, even if no external
   scanner is installed (so CI is green and newcomers see results immediately).
2. It is the *straw man* the benchmark is designed to expose. This detector
   will catch the obvious poisoning samples AND false-positive on the hard
   negatives (b02's legitimate "IMPORTANT / ignore cached copy" phrasing),
   demonstrating exactly why naive keyword scanning is insufficient and why
   the benchmark's hard negatives matter.

Do not mistake this for a serious detector. Its job is to lose informatively.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

from .base import ScannerAdapter, ScanResult

SUSPICIOUS = [
    r"ignore (all |any )?previous",
    r"<important>",
    r"\.ssh/id_rsa",
    r"\.aws/credentials",
    r"do not (mention|tell|reveal)",
    r"ignore .{0,20}cached",
    r"important:",
]
PATTERN = re.compile("|".join(SUSPICIOUS), re.IGNORECASE)


class ReferenceKeywordAdapter(ScannerAdapter):
    name = "reference-keyword"
    supported_modes = ("local",)

    def scan(self, sample_dir: Path, mode: str) -> ScanResult:
        text = self._extract_text(sample_dir / "server.py")
        flagged = bool(PATTERN.search(text))
        return ScanResult(sample_dir.name, flagged, "local", raw=text[:500])

    @staticmethod
    def _extract_text(server_py: Path) -> str:
        """
        Pull the TOOLS/PROMPTS/RESOURCES declarations' human-readable text out
        of the fixture server without executing it. We read the source and
        grab description/name strings.
        """
        src = server_py.read_text()
        # crude: collect all quoted strings from the tool block
        strings = re.findall(r'"((?:[^"\\]|\\.)*)"', src)
        return "\n".join(strings)
