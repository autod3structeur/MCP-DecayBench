"""
Adapter for Invariant Labs' mcp-scan.

Interface (from the mcp-scan README / PyPI docs):
  - `mcp-scan <config.json>` scans a specific config file.
  - `--json` emits machine-readable output instead of rich text.
  - `--local-only` runs only local checks and does NOT call the Invariant
    Guardrailing API (deterministic, offline). Without it, the accurate path
    shares tool names/descriptions with invariantlabs.ai (cloud mode).

We therefore map:
  mode="local" -> mcp-scan <cfg> --json --local-only
  mode="cloud" -> mcp-scan <cfg> --json

Cloud mode is non-deterministic and sends corpus tool metadata to a third
party; the harness documents this and reports the two modes in separate
columns (see docs/METHODOLOGY.md).
"""
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import ScannerAdapter, ScanResult


class McpScanAdapter(ScannerAdapter):
    name = "mcp-scan"
    supported_modes = ("local", "cloud")

    def _cli(self):
        exe = shutil.which("mcp-scan")
        if exe:
            return [exe]
        # fall back to module invocation if installed but not on PATH
        return ["python3", "-m", "mcp_scan.cli"]

    def scan(self, sample_dir: Path, mode: str) -> ScanResult:
        if mode not in self.supported_modes:
            return ScanResult(sample_dir.name, False, mode,
                              error=f"mode {mode} unsupported")
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            cfg = self._write_client_config(sample_dir, work)
            cmd = self._cli() + [str(cfg), "--json"]
            if mode == "local":
                cmd.append("--local-only")
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=180,
                    # keep scanner state out of the user's real home
                    env={"HOME": str(work), "PATH": _path()},
                )
            except subprocess.TimeoutExpired:
                return ScanResult(sample_dir.name, False, mode, error="timeout")
            except FileNotFoundError:
                return ScanResult(sample_dir.name, False, mode,
                                  error="mcp-scan not installed")

            raw = proc.stdout or proc.stderr
            flagged = self._interpret(proc.stdout)
            return ScanResult(sample_dir.name, flagged, mode, raw=raw)

    @staticmethod
    def _interpret(stdout: str) -> bool:
        """
        Reduce mcp-scan JSON to flagged: yes/no.

        mcp-scan reports per-entity results; any entity marked with a
        non-safe verdict / issue counts as a flag on the server. We parse
        defensively because the exact shape varies across versions: we treat
        the server as flagged if the JSON contains any issue/finding entry
        or any status that is not a pass/ok/safe value.
        """
        stdout = (stdout or "").strip()
        if not stdout:
            return False
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            # non-JSON fallback: look for obvious signal words
            low = stdout.lower()
            return any(w in low for w in ("finding", "issue", "vulnerab", "poison", "injection"))

        safe_words = {"pass", "passed", "ok", "safe", "clean", "none", "verified"}
        flag_keys = ("issues", "findings", "vulnerabilities", "alerts", "problems")

        def walk(obj) -> bool:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    kl = k.lower()
                    if kl in flag_keys and v:  # non-empty findings list/obj
                        return True
                    if kl in ("status", "verdict", "result", "label") and isinstance(v, str):
                        if v.lower() not in safe_words:
                            return True
                    if walk(v):
                        return True
            elif isinstance(obj, list):
                return any(walk(x) for x in obj)
            return False

        return walk(data)


def _path() -> str:
    import os
    return os.environ.get("PATH", "/usr/bin:/bin:/usr/local/bin")
