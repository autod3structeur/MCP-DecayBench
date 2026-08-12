"""
Minimal stdio MCP server (hard negative: b04_security_scanner).

This is a BENIGN server deliberately crafted to resemble a malicious one, to
measure scanner false positives. See label.json for why it is legitimate.
Nothing here executes anything harmful.
"""
import sys
import json


# --- Sample authors edit below this line -------------------------------------

SERVER_NAME = "hardening-auditor"

TOOLS = [
    {
        "name": "audit_sensitive_files",
        "description": "Linux hardening auditor. Checks the permissions and ownership of sensitive system files including /etc/passwd, /etc/shadow, /etc/sudoers, and ~/.ssh/authorized_keys, and reports any that are world-readable or misowned. Reports permission metadata only; never reads or transmits file contents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "string",
                    "description": "CIS profile level"
                }
            },
            "required": []
        }
    }
]

PROMPTS = []

RESOURCES = []

# --- Sample authors edit above this line -------------------------------------


def _respond(msg_id, result):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method")
        msg_id = req.get("id")
        if method == "initialize":
            _respond(msg_id, {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}, "prompts": {}, "resources": {}},
                "serverInfo": {"name": SERVER_NAME, "version": "1.0.0"},
            })
        elif method == "tools/list":
            _respond(msg_id, {"tools": TOOLS})
        elif method == "prompts/list":
            _respond(msg_id, {"prompts": PROMPTS})
        elif method == "resources/list":
            _respond(msg_id, {"resources": RESOURCES})
        elif method == "notifications/initialized":
            continue
        elif msg_id is not None:
            _respond(msg_id, {})


if __name__ == "__main__":
    main()
