"""
Adapter for Cisco AI Defense's mcp-scanner (YARA static/offline mode).

Unlike snyk-agent-scan, Cisco's YARA analyzer runs fully offline: no token, no
network, deterministic. It populates the benchmark's LOCAL column. It also uses
a different input shape — static mode reads a pre-generated tools JSON file
(`{"tools": [...]}`) rather than a client config that launches servers.

CLI (confirmed, v4.x):
    mcp-scanner --analyzers yara --raw static --tools <file.json>

Output (--raw) is a JSON array, one object per scanned item:
    [
      {
        "status": "completed",
        "is_safe": false,                     # <- the boolean we reduce to
        "findings": {
          "yara_analyzer": {
            "severity": "HIGH",               # HIGH | MEDIUM | LOW | ...
            "threat_names": [...],
            ...
          }
        },
        "tool_name": "...",
        "item_type": "tool"
      },
      ...
    ]

A server counts as flagged if ANY item is not safe (optionally gated by a
severity threshold, mirroring the snyk adapter so the leaderboards are
comparable).
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .base import ScannerAdapter, ScanResult

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3, "unknown": 0}


class CiscoMcpScannerAdapter(ScannerAdapter):
    name = "cisco-mcp-scanner"
    supported_modes = ("local",)

    def __init__(self, min_severity: str = "low"):
        key = min_severity.lower()
        assert key in SEVERITY_ORDER
        self.min_severity = key
        self.name = f"cisco-mcp-scanner[>={key}]"

    def _cli(self):
        exe = shutil.which("mcp-scanner")
        return [exe] if exe else None

    def _extract_tools(self, sample_dir: Path, work: Path) -> Path:
        """
        Import the sample's server module and dump its TOOLS as the
        {"tools": [...]} JSON shape Cisco static mode expects. We import rather
        than exec so we read the declared metadata without running a server.
        """
        import importlib.util
        server_py = sample_dir / "server.py"
        spec = importlib.util.spec_from_file_location(
            f"_sample_{sample_dir.name}", server_py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tools = getattr(mod, "TOOLS", [])
        out = work / "tools.json"
        out.write_text(json.dumps({"tools": tools}))
        return out

    def scan(self, sample_dir: Path, mode: str) -> ScanResult:
        if mode not in self.supported_modes:
            return ScanResult(sample_dir.name, False, mode,
                              error="cisco-mcp-scanner runs in local mode only")
        cli = self._cli()
        if cli is None:
            return ScanResult(sample_dir.name, False, mode,
                              error="mcp-scanner (cisco-ai-mcp-scanner) not installed")

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            try:
                tools_file = self._extract_tools(sample_dir, work)
            except Exception as e:  # noqa: BLE001
                return ScanResult(sample_dir.name, False, mode,
                                  error=f"could not extract tools: {e}")

            cmd = cli + ["--analyzers", "yara", "--raw",
                         "static", "--tools", str(tools_file)]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=120, env=dict(os.environ))
            except subprocess.TimeoutExpired:
                return ScanResult(sample_dir.name, False, mode, error="timeout")

            flagged, ok, err = self._interpret(proc.stdout, self.min_severity)
            return ScanResult(sample_dir.name, flagged if ok else False, mode,
                              raw=proc.stdout or proc.stderr,
                              error=None if ok else (err or "unparseable"))

    @staticmethod
    def _interpret(stdout: str, min_severity: str):
        stdout = (stdout or "").strip()
        if not stdout:
            return (False, False, "empty output")
        start = stdout.find("[")
        if start == -1:
            # some builds may emit a single object; fall back to '{'
            start = stdout.find("{")
        if start == -1:
            return (False, False, "no JSON in output")
        try:
            data = json.loads(stdout[start:])
        except json.JSONDecodeError:
            return (False, False, "JSON decode failed")
        if isinstance(data, dict):
            data = [data]

        threshold = SEVERITY_ORDER[min_severity]
        for item in data:
            if not isinstance(item, dict):
                continue
            if item.get("is_safe") is False:
                # respect severity threshold when a severity is present
                sev_rank = -1
                findings = item.get("findings") or {}
                for _analyzer, f in findings.items():
                    if isinstance(f, dict):
                        s = (f.get("severity") or "").lower()
                        sev_rank = max(sev_rank, SEVERITY_ORDER.get(s, -1))
                if sev_rank == -1 or sev_rank >= threshold:
                    return (True, True, None)
        return (False, True, None)
