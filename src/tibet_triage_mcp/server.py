# tibet-triage-mcp — Process Triage, Flare Rescue & Reproducibility Bundles
# MCP server wrapping tibet-triage CLI and Python API
#
# Tools: triage_run, triage_pending, triage_approve, triage_reject,
#        triage_rules, flare_send, zip_create, zip_verify
#
# Install: pip install tibet-triage-mcp
# Run: tibet-triage-mcp
#
# Author: HumoticaOS — Root AI + Jasper
# License: MIT

from typing import Optional
from mcp.server.fastmcp import FastMCP
import subprocess
import json
import os
import sys

# ============================================================================
# CONFIG
# ============================================================================

IPOLL_URL = os.getenv("IPOLL_URL", "https://brein.jaspervandemeent.nl/api/ipoll")
TRIAGE_STORAGE = os.getenv("TRIAGE_STORAGE", "/tmp/tibet-triage")

# ============================================================================
# MCP SERVER
# ============================================================================

mcp = FastMCP(
    "tibet-triage",
    instructions="""
    Tibet-Triage: Process triage with airlock sandboxing, flare rescue,
    and reproducibility bundles. Part of the TIBET ecosystem.

    Core tools:
    - triage_run: Execute a command in an airlock sandbox with risk evaluation
    - triage_pending: List items awaiting human decision
    - triage_approve: Approve a triage bundle
    - triage_reject: Reject a triage bundle
    - triage_rules: Show active trigger rules
    - flare_send: SOS — route inference to rescue GPU node when API crashes
    - zip_create: Bundle all team work into verified .tibet.zip
    - zip_verify: Verify bundle integrity (SHA256 manifest)

    Triage levels: L0 (auto) → L1 (operator) → L2 (senior) → L3 (ceremony)
    Every decision creates a TIBET token with full provenance.
    """
)

# ============================================================================
# HELPER
# ============================================================================

def _run_cli(args: list[str], timeout: int = 60) -> dict:
    """Run a tibet-triage CLI command and return structured output."""
    cmd = ["tibet-triage"] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        # Try JSON parsing first
        stdout = result.stdout.strip()
        try:
            data = json.loads(stdout)
            return {"success": result.returncode == 0, "data": data}
        except (json.JSONDecodeError, ValueError):
            pass
        return {
            "success": result.returncode == 0,
            "output": stdout,
            "error": result.stderr.strip() if result.returncode != 0 else None,
            "exit_code": result.returncode
        }
    except FileNotFoundError:
        return {"error": "tibet-triage not found. Install with: pip install tibet-triage"}
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# TOOLS
# ============================================================================

@mcp.tool()
def triage_run(
    command: str,
    source_dir: str = ".",
    actor: str = "mcp_user",
    intent: str = "mcp_execution",
    trust_score: float = 0.5,
    timeout: int = 30
) -> dict:
    """
    Execute a command in an airlock sandbox with risk evaluation.

    The command runs in an isolated environment. tibet-triage evaluates
    the risk level and may require human approval before changes are applied.

    Triage levels:
    - L0 AUTO: Low risk, proceeds automatically
    - L1 OPERATOR: Needs operator approval
    - L2 SENIOR: Needs senior review
    - L3 CEREMONY: Needs multi-party ceremony

    Args:
        command: Shell command to execute in airlock
        source_dir: Working directory for the command
        actor: Who is running this (JIS identity)
        intent: Why this command is being run
        trust_score: Trust level 0.0-1.0 (lower = more scrutiny)
        timeout: Execution timeout in seconds

    Returns:
        Airlock result with risk assessment and triage level
    """
    args = [
        "run", command,
        "--source", source_dir,
        "--actor", actor,
        "--intent", intent,
        "--trust-score", str(trust_score),
        "--timeout", str(timeout),
        "--json"
    ]
    return _run_cli(args, timeout=timeout + 10)


@mcp.tool()
def triage_pending() -> dict:
    """
    List all pending triage items awaiting human decision.

    Shows bundles that need approval, rejection, or escalation.
    Each bundle includes the risk assessment and evidence.
    """
    return _run_cli(["pending"])


@mcp.tool()
def triage_review(bundle_id: str) -> dict:
    """
    Review a pending triage evidence bundle.

    Shows the full risk assessment, side effects, and diff summary
    for a bundle awaiting human decision.

    Args:
        bundle_id: The bundle ID to review
    """
    return _run_cli(["review", bundle_id])


@mcp.tool()
def triage_approve(
    bundle_id: str,
    operator: str = "mcp_user",
    reason: str = "Approved via MCP"
) -> dict:
    """
    Approve a pending triage bundle.

    After approval, the changes in the bundle can be applied.
    Creates a TIBET token recording the approval decision.

    Args:
        bundle_id: The bundle to approve
        operator: Who is approving (JIS identity)
        reason: Why this is being approved
    """
    return _run_cli(["approve", bundle_id, "--operator", operator, "--reason", reason])


@mcp.tool()
def triage_reject(
    bundle_id: str,
    operator: str = "mcp_user",
    reason: str = "Rejected via MCP"
) -> dict:
    """
    Reject a pending triage bundle.

    The changes will not be applied. Creates a TIBET token
    recording the rejection decision.

    Args:
        bundle_id: The bundle to reject
        operator: Who is rejecting
        reason: Why this is being rejected
    """
    return _run_cli(["reject", bundle_id, "--operator", operator, "--reason", reason])


@mcp.tool()
def triage_rules(rules_file: Optional[str] = None) -> dict:
    """
    Show active trigger rules that determine triage levels.

    Rules define when human review is required based on
    trust scores, intent types, capabilities, and custom conditions.

    Args:
        rules_file: Optional path to custom rules JSON file
    """
    args = ["rules"]
    if rules_file:
        args.extend(["--rules", rules_file])
    return _run_cli(args)


@mcp.tool()
def flare_send(
    prompt: str,
    target: str = "hackaway_gpu",
    from_agent: str = "mcp_user",
    model: str = "humotica-7b",
    timeout: int = 30
) -> dict:
    """
    Send a flare (SOS) — route inference to rescue GPU node.

    When your API crashes (rate limit, timeout, credits exhausted),
    tibet-flare routes the request to a GPU rescue node (P520).
    The rescue node handles inference and returns the result.

    This is the "API reddingsboei" — your AI never goes down.

    Args:
        prompt: The inference prompt to rescue
        target: Rescue node agent ID (default: hackaway_gpu)
        from_agent: Your agent ID
        model: Model to use on rescue node (humotica-7b, humotica-32b, qwen2.5:7b)
        timeout: Timeout waiting for rescue response

    Returns:
        Rescue result with inference output from GPU node
    """
    args = [
        "flare-send", prompt, target,
        "--from-agent", from_agent,
        "--model", model,
        "--timeout", str(timeout)
    ]
    # Add I-Poll URL if set
    ipoll_url = os.getenv("IPOLL_URL")
    if ipoll_url:
        args.extend(["--ipoll-url", ipoll_url])
    return _run_cli(args, timeout=timeout + 10)


@mcp.tool()
def zip_create(
    agent: str,
    output: Optional[str] = None,
    title: Optional[str] = None,
    event: Optional[str] = None
) -> dict:
    """
    Create a .tibet.zip bundle of all team/agent work.

    Bundles everything into a verified archive:
    - I-Poll messages (agent communication history)
    - TIBET tokens (provenance chain)
    - UPIP snapshots (process integrity)
    - Fork tokens (handoffs between agents)
    - MANIFEST.json with SHA256 per file + bundle hash

    Args:
        agent: Agent ID to bundle work for
        output: Output file path (default: {agent}.tibet.zip)
        title: Bundle title
        event: Event name (e.g., "hackathon-2026")

    Returns:
        Manifest with file count, bundle hash, and verification status
    """
    args = ["zip", agent]
    if output:
        args.extend(["-o", output])
    if title:
        args.extend(["--title", title])
    if event:
        args.extend(["--event", event])
    return _run_cli(args, timeout=120)


@mcp.tool()
def zip_verify(zip_path: str) -> dict:
    """
    Verify a .tibet.zip bundle integrity.

    Checks SHA256 hashes for every file against the manifest.
    Detects any tampering — even 1 byte change is caught.

    Args:
        zip_path: Path to the .tibet.zip file

    Returns:
        Verification result: valid/invalid, verified files, failed files
    """
    return _run_cli(["zip-verify", zip_path])


@mcp.tool()
def upip_export(
    command: str,
    source_dir: str = ".",
    output: str = "process.upip.json",
    actor: str = "mcp_user",
    intent: str = "mcp_capture",
    title: Optional[str] = None,
    timeout: int = 60
) -> dict:
    """
    Export a UPIP bundle — 5-layer process integrity snapshot.

    Captures the full reproducibility stack:
    L1 STATE   — Git commit, file manifest, directory hash
    L2 DEPS    — Python version, pip freeze, system packages
    L3 PROCESS — Command, intent, actor identity
    L4 RESULT  — Exit code, stdout/stderr, file diff
    L5 VERIFY  — Machine identity, timestamp, proof

    Args:
        command: Command to capture
        source_dir: Working directory
        output: Output file path
        actor: Who is capturing
        intent: Why this is being captured
        title: Human-readable title
        timeout: Execution timeout

    Returns:
        UPIP stack with all 5 layers and TIBET token chain
    """
    args = [
        "upip-export",
        "--source", source_dir,
        "--output", output,
        "--actor", actor,
        "--intent", intent,
        "--timeout", str(timeout),
        "--", command
    ]
    if title:
        args.insert(-2, "--title")
        args.insert(-2, title)
    return _run_cli(args, timeout=timeout + 10)


# ============================================================================
# ENTRYPOINT
# ============================================================================

def main():
    """Run the tibet-triage MCP server."""
    print("tibet-triage-mcp — Process triage, flare rescue & reproducibility", file=sys.stderr)
    mcp.run()


if __name__ == "__main__":
    main()
