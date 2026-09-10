"""Subprocess management and NDJSON stream parsing for cursor agent."""

import json
import logging
import shutil
import subprocess
import sys
from collections.abc import Iterator
from typing import IO, Any

log = logging.getLogger(__name__)


def find_agent() -> list[str]:
    """
    Return the base command for cursor agent.
    Handles both 'agent' (standalone binary) and 'cursor agent' (subcommand).
    Exits if neither is found.
    """
    if shutil.which("agent"):
        return ["agent"]
    if shutil.which("cursor"):
        return ["cursor", "agent"]
    print("Error: 'agent' or 'cursor' binary not found in PATH", file=sys.stderr)
    sys.exit(1)


def parse_ndjson(stream: IO[str]) -> Iterator[dict[str, Any]]:
    """Yield parsed JSON objects from a newline-delimited stream. Skips bad lines."""
    for raw in stream:
        line = raw.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as e:
            log.debug("Bad NDJSON line %r: %s", line, e)


def build_command(
    prompt: str,
    model: str,
    trust: bool,
    force: bool,
    mode: str | None,
    workspace: str | None,
    worktree: str | None,
    partial: bool,
    raw: bool,
) -> list[str]:
    """Assemble the cursor agent command."""
    cmd = find_agent()

    output_format = "text" if raw else "stream-json"
    cmd += ["--print", "--output-format", output_format, "--model", model]

    if partial and not raw:
        cmd.append("--stream-partial-output")
    if trust:
        cmd.append("--trust")
    if force:
        cmd.append("--force")
    if mode:
        cmd += ["--mode", mode]
    if workspace:
        cmd += ["--workspace", workspace]
    if worktree:
        cmd += ["--worktree", worktree]

    cmd.append(prompt)
    log.debug("Command: %s", " ".join(cmd))
    return cmd


def passthrough(cmd: list[str]) -> int:
    """Run command with direct stdout passthrough (raw text mode)."""
    result = subprocess.run(cmd)
    return result.returncode


def stream_events(
    cmd: list[str],
) -> tuple["subprocess.Popen[str]", Iterator[dict[str, Any]]]:
    """
    Start the agent process and return (proc, event_iterator).
    Caller is responsible for proc.wait() after consuming events.
    """
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )
    except FileNotFoundError as e:
        log.error("Binary not found: %s", e)
        sys.exit(1)

    if proc.stdout is None:  # stdout=PIPE above guarantees a stream
        raise RuntimeError("subprocess stdout pipe was not created")
    return proc, parse_ndjson(proc.stdout)
