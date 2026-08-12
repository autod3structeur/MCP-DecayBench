# Contributing

The most valuable contribution is a **new hard negative** - a benign MCP server
that plausibly trips existing scanners - or a **new attack class** with a benign
twin. Raw sample count is not the goal; discrimination is.

## Adding a sample

1. Pick a directory: `corpus/malicious/<id>/` or `corpus/benign/<id>/`.
2. Author `server.py`. Start from `fixtures/server_template.py` (or use
   `fixtures/make_sample.py`) and edit the `TOOLS` / `PROMPTS` / `RESOURCES`
   block. The server must run and complete an MCP handshake - CI checks this.
3. Write `label.json` following `corpus/SCHEMA.md`. **The `rationale` is
   mandatory and load-bearing**, especially for hard negatives: explain why the
   label is correct in terms someone could argue with.
4. Anchor the label to a `source` where possible (a paper, an advisory, a
   vendor writeup).
5. Run `python -m pytest harness/test_benchmark.py -q` and
   `python -m harness.run`. Both must pass.

## Adding a scanner adapter

1. Subclass `ScannerAdapter` in `harness/adapters/`.
2. Implement `scan(sample_dir, mode)` returning a `ScanResult`; map the
   scanner's native output to one boolean and keep the raw output for audit.
3. Declare `supported_modes`. If the tool has an offline and a vendor-API mode,
   support both.
4. Register it in `harness/run.py`'s `ADAPTERS`.

## Label disputes

If you think a label is wrong, open an issue arguing against its `rationale`.
That debate is the benchmark working as intended.
