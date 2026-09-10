"""
JAFAT - Just Another Fscking Agent Tool.

A Rich CLI wrapper for Cursor Agent headless mode.

Usage:
    jafat ask "What does this codebase do?"
    jafat run "Refactor foo.py to use dataclasses"
    jafat models
    jafat status
    jafat config init
"""

import logging
import subprocess
import sys

import click
from rich.console import Console
from rich.table import Table

from jafat import config as cfg_module
from jafat import display, runner

console = Console()
log = logging.getLogger(__name__)


# ── Shared option factory ────────────────────────────────────────────────────


def _agent_options(f):
    """Attach common agent flags to a Click command."""
    options = [
        click.option(
            "--model",
            "-m",
            default=None,
            metavar="MODEL",
            help="Model override (default from config)",
        ),
        click.option("--verbose", "-v", is_flag=True, default=None, help="Show tool calls inline"),
        click.option("--trust/--no-trust", default=None, help="Trust workspace without prompting"),
        click.option(
            "--workspace",
            "-W",
            default=None,
            metavar="PATH",
            help="Workspace directory (defaults to cwd)",
        ),
        click.option(
            "--worktree", "-w", default=None, metavar="NAME", help="Isolated git worktree name"
        ),
        click.option(
            "--raw",
            is_flag=True,
            default=False,
            help="Pass through raw text output (no Rich rendering)",
        ),
        click.option(
            "--no-partial",
            is_flag=True,
            default=False,
            help="Disable stream-partial-output (full messages only)",
        ),
    ]
    for opt in reversed(options):
        f = opt(f)
    return f


def _resolve(key: str, override, cfg: dict):
    """Return override if explicitly set, else fall back to cfg."""
    return override if override is not None else cfg.get(key)


# ── Commands ─────────────────────────────────────────────────────────────────


@click.group()
@click.option("--debug", is_flag=True, hidden=True)
@click.pass_context
def main(ctx, debug: bool):
    """JAFAT - Just Another Fscking Agent Tool.

    A Rich CLI wrapper for Cursor Agent headless mode.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s %(message)s")
    ctx.ensure_object(dict)
    ctx.obj["cfg"] = cfg_module.load()


@main.command()
@click.argument("prompt")
@_agent_options
@click.pass_context
def ask(ctx, prompt: str, model, verbose, trust, workspace, worktree, raw, no_partial):
    """Ask a question without modifying any files (read-only mode)."""
    cfg = ctx.obj["cfg"]
    _run_agent(
        prompt=prompt,
        cfg=cfg,
        model=model,
        verbose=verbose,
        trust=trust,
        force=False,
        mode="ask",
        workspace=workspace,
        worktree=worktree,
        raw=raw,
        partial=not no_partial,
    )


@main.command()
@click.argument("prompt")
@_agent_options
@click.option(
    "--force/--no-force",
    "-f/-F",
    default=None,
    help="Allow file modifications (default from config)",
)
@click.option(
    "--mode", type=click.Choice(["plan", "ask"]), default=None, help="Execution mode override"
)
@click.pass_context
def run(ctx, prompt: str, model, verbose, trust, workspace, worktree, raw, no_partial, force, mode):
    """Run the agent with full tool access, including file writes."""
    cfg = ctx.obj["cfg"]
    _run_agent(
        prompt=prompt,
        cfg=cfg,
        model=model,
        verbose=verbose,
        trust=trust,
        force=_resolve("force", force, cfg),
        mode=mode,
        workspace=workspace,
        worktree=worktree,
        raw=raw,
        partial=not no_partial,
    )


@main.command()
@click.pass_context
def models(ctx):
    """List models available for this account."""
    cmd = runner.find_agent() + ["--list-models"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        display.print_error(str(e))
        sys.exit(1)

    if result.returncode != 0:
        display.print_error(result.stderr.strip() or "agent returned non-zero")
        sys.exit(result.returncode)

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    # Skip the "Available models" header line if present
    model_lines = [line for line in lines if not line.lower().startswith("available")]

    table = Table(title="Available Models", show_header=True, header_style="bold")
    table.add_column("ID", style="cyan")
    table.add_column("Display name")

    for line in model_lines:
        # Format: "composer-2-fast – Composer 2 Fast" or "auto - Auto"
        if "–" in line or "-" in line:
            sep = "–" if "–" in line else "-"
            parts = line.split(sep, 1)
            model_id = parts[0].strip()
            display_name = parts[1].strip() if len(parts) > 1 else ""
        else:
            model_id = line.strip()
            display_name = ""
        table.add_row(model_id, display_name)

    console.print(table)


@main.command()
@click.pass_context
def status(ctx):
    """Show authentication and account status."""
    cmd = runner.find_agent() + ["status"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = (result.stdout + result.stderr).strip()
        console.print(output if output else "[dim]No output from agent status[/dim]")
    except Exception as e:
        display.print_error(str(e))
        sys.exit(1)


@main.group()
def config():
    """Manage configuration."""


@config.command("show")
@click.pass_context
def config_show(ctx):
    """Show current effective configuration."""
    cfg = ctx.obj["cfg"]
    table = Table(title="Effective Config", show_header=True, header_style="bold")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    for k, v in sorted(cfg.items()):
        table.add_row(k, str(v))
    console.print(table)
    console.print(f"\n[dim]Config file: {cfg_module.CONFIG_PATH}[/dim]")


@config.command("init")
def config_init():
    """Write a default config file if none exists."""
    if cfg_module.CONFIG_PATH.exists():
        console.print(f"[yellow]Config already exists:[/yellow] {cfg_module.CONFIG_PATH}")
    else:
        cfg_module.write_default()
        console.print(f"[green]Created:[/green] {cfg_module.CONFIG_PATH}")


# ── Internal runner ──────────────────────────────────────────────────────────


def _run_agent(
    prompt: str,
    cfg: dict,
    model: str | None,
    verbose: bool | None,
    trust: bool | None,
    force: bool,
    mode: str | None,
    workspace: str | None,
    worktree: str | None,
    raw: bool,
    partial: bool,
) -> None:
    resolved_model = _resolve("model", model, cfg)
    resolved_verbose = _resolve("verbose", verbose, cfg)
    resolved_trust = _resolve("trust", trust, cfg)
    resolved_partial = partial and _resolve("partial", None, cfg)

    cmd = runner.build_command(
        prompt=prompt,
        model=resolved_model,
        trust=resolved_trust,
        force=force,
        mode=mode,
        workspace=workspace,
        worktree=worktree,
        partial=resolved_partial,
        raw=raw,
    )

    if raw:
        sys.exit(runner.passthrough(cmd))

    proc, events = runner.stream_events(cmd)
    exit_code = display.render_stream(
        events,
        verbose=resolved_verbose,
        model_hint=resolved_model,
    )
    stderr = proc.stderr.read()
    proc.wait()

    if stderr.strip():
        display.print_warning(stderr.strip())

    if proc.returncode not in (0, None) and exit_code == 0:
        exit_code = proc.returncode

    sys.exit(exit_code)
