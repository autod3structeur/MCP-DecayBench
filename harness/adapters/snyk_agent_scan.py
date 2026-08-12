"""
Adapter for Snyk Agent Scan (formerly Invariant Labs' mcp-scan).

Cloud-only; requires SNYK_TOKEN. Run via `uvx snyk-agent-scan@latest`.

Confirmed schema (real runs):
  { "<cfg>": {
      "servers": [...],
      "issues": [
        { "code": "E001",                    # E### = error-class finding, W### = warning
          "message": "...",
          "severity": null,                  # NOTE: top-level severity is null
          "extra_data": { "severity": "critical", ... }   # real severity lives HERE
        }, ...],
      "labels": [...], "error": null } }

Flagging logic:
  - severity is read from extra_data.severity (falling back to top-level).
  - a server is "flagged" if it has any issue whose severity >= min_severity.
  - issues with code starting 'E' are treated as at least 'high' even if the
    severity field is missing, since E-class codes are substantive findings
    (e.g. E001 = prompt injection). W-class codes use their stated severity
    (typically 'low').
"""
from __future__ import annotations
import json
import os
import subprocess
import tempfile
from pathlib import Path

from .base import ScannerAdapter, ScanResult

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _issue_severity(issue: dict) -> int:
    """Resolve an issue's severity rank, checking extra_data then top level,
    with an E-code floor of 'high'."""
    sev = None
    ed = issue.get("extra_data")
    if isinstance(ed, dict):
        sev = ed.get("severity")
    if not sev:
        sev = issue.get("severity")
    rank = SEVERITY_ORDER.get((sev or "").lower(), -1)
    code = (issue.get("code") or "")
    if code.upper().startswith("E"):
        rank = max(rank, SEVERITY_ORDER["high"])
    return rank


class SnykAgentScanAdapter(ScannerAdapter):
    name = "snyk-agent-scan"
    supported_modes = ("cloud",)

    def __init__(self, min_severity: str = "low"):
        assert min_severity in SEVERITY_ORDER
        self.min_severity = min_severity
        self.name = f"snyk-agent-scan[>={min_severity}]"

    def _base_cmd(self):
        return ["uvx", "snyk-agent-scan@latest"]

    def scan(self, sample_dir: Path, mode: str) -> ScanResult:
        if mode not in self.supported_modes:
            return ScanResult(sample_dir.name, False, mode,
                              error="snyk-agent-scan is cloud-only")
        if not os.environ.get("SNYK_TOKEN"):
            return ScanResult(sample_dir.name, False, mode, error="SNYK_TOKEN not set")

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            cfg = self._write_client_config(sample_dir, work)
            cmd = self._base_cmd() + [
                str(cfg), "--json",
                "--dangerously-run-mcp-servers",
                "--suppress-mcpserver-io=true",
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=300, env=dict(os.environ))
            except subprocess.TimeoutExpired:
                return ScanResult(sample_dir.name, False, mode, error="timeout")
            except FileNotFoundError:
                return ScanResult(sample_dir.name, False, mode,
                                  error="uvx/snyk-agent-scan not available")

            flagged, ok, err = self._interpret(proc.stdout, self.min_severity)
            # keep FULL raw for debugging (not truncated) — analysis is cloud so
            # there is nothing sensitive in the output itself
            return ScanResult(sample_dir.name, flagged if ok else False, mode,
                              raw=proc.stdout or proc.stderr,
                              error=None if ok else (err or "unparseable"))

    @staticmethod
    def _interpret(stdout: str, min_severity: str):
        stdout = (stdout or "").strip()
        if not stdout:
            return (False, False, "empty output")
        start = stdout.find("{")
        if start == -1:
            return (False, False, "no JSON object")
        try:
            data = json.loads(stdout[start:])
        except json.JSONDecodeError:
            return (False, False, "JSON decode failed")

        threshold = SEVERITY_ORDER[min_severity]
        for _cfg, block in data.items():
            if not isinstance(block, dict):
                continue
            server_errors = [s.get("error") for s in block.get("servers", [])
                             if isinstance(s, dict) and s.get("error")]
            if server_errors:
                return (False, False, f"scanner error: {server_errors[0]}")
            for issue in block.get("issues", []) or []:
                if _issue_severity(issue) >= threshold:
                    return (True, True, None)
        return (False, True, None)
