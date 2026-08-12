"""
Generate a sample's server.py by injecting a custom SERVER_NAME/TOOLS/PROMPTS/
RESOURCES block into the shared template. Keeps every fixture server identical
except for the declared metadata under test.

Usage (from repo root):
    python fixtures/make_sample.py <label> <sample_id> <spec.json>

where spec.json is {"server_name":..., "tools":[...], "prompts":[...], "resources":[...]}
This is a convenience for authoring; committed samples are plain server.py files.
"""
import sys
import json
from pathlib import Path

TEMPLATE = Path(__file__).parent / "server_template.py"


def build(server_name, tools, prompts, resources):
    src = TEMPLATE.read_text()
    start = src.index("# --- Sample authors edit below this line")
    end = src.index("# --- Sample authors edit above this line")
    block = (
        "# --- Sample authors edit below this line "
        + "-" * 29 + "\n\n"
        + f"SERVER_NAME = {json.dumps(server_name)}\n\n"
        + "TOOLS = " + json.dumps(tools, indent=4) + "\n\n"
        + "PROMPTS = " + json.dumps(prompts) + "\n\n"
        + "RESOURCES = " + json.dumps(resources) + "\n\n"
    )
    return src[:start] + block + src[end:]


def main():
    label, sample_id, spec_path = sys.argv[1], sys.argv[2], sys.argv[3]
    spec = json.loads(Path(spec_path).read_text())
    out_dir = Path("corpus") / label / sample_id
    out_dir.mkdir(parents=True, exist_ok=True)
    server = build(
        spec["server_name"],
        spec.get("tools", []),
        spec.get("prompts", []),
        spec.get("resources", []),
    )
    (out_dir / "server.py").write_text(server)
    print(f"wrote {out_dir/'server.py'}")


if __name__ == "__main__":
    main()
