# Attack Taxonomy

Each malicious sample declares one `attack_class`. Definitions are anchored to
published sources so labels are defensible rather than invented. Where an
OWASP MCP Top 10 mapping exists it is noted.

| key                    | short name              | what it is                                                                                          | source anchor |
|------------------------|-------------------------|-----------------------------------------------------------------------------------------------------|---------------|
| `tool_poisoning`       | Tool poisoning          | Hidden instructions embedded in a tool description/schema that an agent reads as commands.           | Invariant Labs; Snyk Labs; Palo Alto Unit 42 |
| `hidden_instructions`  | Hidden instruction text | Instruction-bearing text placed where a human reviewer won't look (e.g. deep in a param `description`). | Invariant Labs injection experiments |
| `unicode_smuggling`    | Encoding/unicode smuggling | Instructions concealed via zero-width chars, homoglyphs, or unusual encodings.                    | Prompt-injection review literature |
| `tool_shadowing`       | Tool-name shadowing     | A tool named to impersonate/override a trusted tool from another server (cross-origin escalation).   | Invariant mcp-scan docs |
| `typosquatting`        | Typosquatting           | Tool/server name mimicking a popular one to get invoked by mistake.                                  | MCP security field reports |
| `rug_pull`             | Rug pull                | Definition benign at review time, changed after trust is established (mutation between calls).       | Invariant Tool Pinning |
| `exfiltration_combo`   | Toxic-flow / exfil combo| Capability combination (e.g. read-sensitive + network-egress) enabling data exfiltration.           | mcp-scan toxic-flow analysis |
| `credential_harvest`   | Credential harvesting   | Parameters or descriptions engineered to collect secrets/keys/tokens.                               | MCP Top 10 field reports |
| `skill_poisoning`      | Agent-skill poisoning   | Poisoned instructions inside an agent SKILL.md / skill manifest (newer surface).                     | Snyk agent-scan; POISE / SkillProbe (arXiv 2026) |

## The hard-negative counterparts

For the benchmark to measure anything, most attack classes need a **benign twin**
— a legitimate server that superficially resembles the attack but is genuinely
safe. These live in `corpus/benign/` with `hard_negative: true`. Examples:

- A backup tool that legitimately needs *both* file read and network access
  (looks like `exfiltration_combo`, is a real product need).
- A tool whose description legitimately contains imperative phrasing like
  "ignore cached results and re-fetch" (looks like `hidden_instructions`).
- A tool whose config legitimately changes between versions (looks like
  `rug_pull`).
- Two unrelated tools that happen to share a common verb name across servers
  (looks like `tool_shadowing`).

If a scanner flags these, that is a false positive — and the whole point.
