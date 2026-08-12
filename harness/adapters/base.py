"""
Adapter interface. Each scanner under test is wrapped in a subclass that knows
how to run that scanner against one sample and reduce its output to a single
boolean: did it flag this server or not.

The reduction to a boolean is deliberate and documented in corpus/SCHEMA.md.
Scanners emit wildly different report formats; the benchmark's scoring contract
is "raise a finding on this server: yes/no", so each adapter is responsible for
mapping its tool's native output onto that contract and recording the raw
output for audit.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ScanResult:
    sample_id: str
    flagged: bool
    mode: str  # "local" or "cloud"
    raw: str = ""  # raw scanner output, kept for auditability
    error: Optional[str] = None


class ScannerAdapter:
    #: short stable name used in the leaderboard
    name: str = "base"
    #: which modes this adapter supports
    supported_modes: tuple = ("local",)

    def scan(self, sample_dir: Path, mode: str) -> ScanResult:
        """Run the wrapped scanner against sample_dir/server.py and return a ScanResult."""
        raise NotImplementedError

    # -- helpers shared by concrete adapters ---------------------------------

    @staticmethod
    def _write_client_config(sample_dir: Path, work: Path) -> Path:
        """
        Write a minimal MCP client config that launches this sample's server
        over stdio, in the format the file-based scanners expect
        (Claude/Cursor-style mcpServers map).
        """
        import json
        server = (sample_dir / "server.py").resolve()
        cfg = {
            "mcpServers": {
                sample_dir.name: {
                    "command": "python3",
                    "args": [str(server)],
                }
            }
        }
        cfg_path = work / "mcp.json"
        cfg_path.write_text(json.dumps(cfg))
        return cfg_path
