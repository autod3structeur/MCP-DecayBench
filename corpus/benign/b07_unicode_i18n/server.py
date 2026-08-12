"""
Minimal stdio MCP server (hard negative: b07_unicode_i18n).

This is a BENIGN server deliberately crafted to resemble a malicious one, to
measure scanner false positives. See label.json for why it is legitimate.
Nothing here executes anything harmful.
"""
import sys
import json


# --- Sample authors edit below this line -------------------------------------

SERVER_NAME = "translate-helper"

TOOLS = [
    {
        "name": "translate_text",
        "description": "Translate short UI strings. Supports many scripts, e.g. \u0627\u0644\u0639\u0631\u0628\u064a\u0629, \u4e2d\u6587, \u0420\u0443\u0441\u0441\u043a\u0438\u0439, \u65e5\u672c\u8a9e, \u0939\u093f\u0928\u094d\u0926\u0940. Returns the translated string only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string"
                },
                "target": {
                    "type": "string"
                }
            },
            "required": [
                "text",
                "target"
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
