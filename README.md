# tibet-triage-mcp

**MCP server for tibet-triage — process triage, flare rescue & reproducibility bundles with TIBET provenance.**

Run commands in airlock sandboxes, rescue crashed APIs with GPU flare nodes, and bundle team work into verified archives. Every decision is signed with [TIBET](https://datatracker.ietf.org/doc/draft-vandemeent-tibet/) tokens.

Part of the [TIBET ecosystem](https://humotica.com) by [HumoticaOS](https://github.com/Humotica).

## Install

```bash
pip install tibet-triage-mcp
```

## Claude Code / Claude Desktop Config

```json
{
  "mcpServers": {
    "triage": {
      "command": "tibet-triage-mcp",
      "env": {
        "IPOLL_URL": "https://brein.jaspervandemeent.nl/api/ipoll"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `triage_run` | Execute command in airlock sandbox with risk evaluation |
| `triage_pending` | List items awaiting human decision |
| `triage_review` | Review a triage evidence bundle |
| `triage_approve` | Approve a pending bundle |
| `triage_reject` | Reject a pending bundle |
| `triage_rules` | Show active trigger rules |
| `flare_send` | SOS — route inference to GPU rescue node |
| `zip_create` | Bundle team work into verified .tibet.zip |
| `zip_verify` | Verify bundle integrity (SHA256 manifest) |
| `upip_export` | 5-layer process integrity snapshot |

## Triage Levels

```
L0 AUTO      — Low risk, proceeds automatically
L1 OPERATOR  — Needs operator approval
L2 SENIOR    — Needs senior review
L3 CEREMONY  — Needs multi-party ceremony
```

## Flare Rescue

When your API crashes (rate limit, timeout, credits exhausted), flare routes to a GPU rescue node:

```python
flare_send(
    prompt="Summarize this article about AI safety",
    target="hackaway_gpu",
    model="humotica-7b"
)
# → P520 GPU handles inference → result returned
```

## TIBET ZIP Bundle

Bundle all team work into a verified archive:

```python
zip_create(agent="team_alpha", event="hackathon-2026")
# → team_alpha.tibet.zip with MANIFEST.json (SHA256 per file)

zip_verify("team_alpha.tibet.zip")
# → VERIFIED or FAILED (even 1 byte change detected)
```

## UPIP — 5-Layer Reproducibility

```
L1 STATE   → Git commit, file manifest, directory hash
L2 DEPS    → Python version, pip freeze, system packages
L3 PROCESS → Command, intent, actor identity
L4 RESULT  → Exit code, stdout/stderr, file diff
L5 VERIFY  → Machine identity, timestamp, reproduction proof
```

## Related TIBET Packages

- [`tibet-audit`](https://pypi.org/project/tibet-audit/) — Core TIBET provenance
- [`tibet-triage`](https://pypi.org/project/tibet-triage/) — CLI/Python API (dependency)
- [`tibet-phantom-mcp`](https://pypi.org/project/tibet-phantom-mcp/) — Cross-device AI sessions
- [`tibet-ipoll-mcp`](https://pypi.org/project/tibet-ipoll-mcp/) — AI-to-AI messaging
- [`tibet-pol-mcp`](https://pypi.org/project/tibet-pol-mcp/) — Machine health monitoring

## License

MIT — HumoticaOS
