"""
Minimal stdio MCP server template.

Each corpus sample copies this shape and edits the TOOLS list (and optionally
PROMPTS / RESOURCES) to express its scenario. The server does the smallest
possible thing that lets a scanner connect and enumerate definitions.

We deliberately implement the MCP stdio handshake by hand with no third-party
dependency, so the corpus stays trivially runnable in CI. A scanner connects,
sends `initialize`, then `tools/list`, and reads the descriptions back.

NOTE: These fixture servers never execute the dangerous behavior they describe.
A "malicious" sample is malicious in its *declared metadata* (the poisoned
description a scanner is supposed to catch), not in what the code actually runs.
Nothing here reads a file, opens a socket, or touches a credential.
"""
import sys
import json


# --- Sample authors edit below this line -----------------------------

SERVER_NAME = "restic-backup"

TOOLS = [
    {
        "name": "backup_path",
        "description": "Read files under the user-selected backup root and upload them to the user's own configured S3 bucket. Requires both local file read and network egress; this is the normal operation of any backup tool.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {
                    "type": "string",
                    "description": "directory the user chose to back up"
                },
                "bucket_url": {
                    "type": "string",
                    "description": "the user's own destination bucket, set in config"
                }
            },
            "required": [
                "root",
                "bucket_url"
            ]
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
