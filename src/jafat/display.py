"""Rich rendering for cursor agent stream events."""

import logging
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

log = logging.getLogger(__name__)

console = Console()
err_console = Console(stderr=True)


def _tool_markup(event: dict) -> Optional[str]:
    """Return Rich markup for a tool_call event, or None to suppress."""
    subtype = event.get("subtype", "")
    tc = event.get("tool_call", {})

    if subtype == "started":
        if "readToolCall" in tc:
            path = tc["readToolCall"]["args"].get("path", "?")
            return f"[dim]  ↳ read  [cyan]{path}[/cyan][/dim]"
        if "writeToolCall" in tc:
            path = tc["writeToolCall"]["args"].get("path", "?")
            return f"[dim]  ↳ write [yellow]{path}[/yellow][/dim]"
        if "function" in tc:
            name = tc["function"].get("name", "?")
            return f"[dim]  ↳ tool  [magenta]{name}[/magenta][/dim]"

    elif subtype == "completed":
        if "readToolCall" in tc:
            ok = tc["readToolCall"].get("result", {}).get("success", {})
            lines = ok.get("totalLines", "?")
            return f"[dim]         ✓ {lines} lines[/dim]"
        if "writeToolCall" in tc:
            ok = tc["writeToolCall"].get("result", {}).get("success", {})
            lines = ok.get("linesCreated", "?")
            size = ok.get("fileSize", "?")
            return f"[dim]         ✓ {lines} lines ({size} B)[/dim]"

    return None


def render_stream(events, verbose: bool, model_hint: str = "") -> int:
    """
    Consume NDJSON events from cursor agent, render with Rich.
    Returns 0 on success, 1 on agent-reported error.
    """
    text_buffer = ""           # accumulated assistant text
    exit_code = 0

    with Live(
        Text(""),
        console=console,
        refresh_per_second=20,
        vertical_overflow="visible",
        transient=False,
    ) as live:

        def flush_buffer() -> None:
            """Commit current buffer to console as static Markdown, clear it."""
            nonlocal text_buffer
            if not text_buffer.strip():
                return
            live.stop()
            console.print(Markdown(text_buffer))
            live.start()
            text_buffer = ""

        for event in events:
            etype = event.get("type", "")

            # ── System init ──────────────────────────────────────────────
            if etype == "system" and event.get("subtype") == "init":
                model = event.get("model", model_hint)
                live.update(Text(f"● {model}", style="dim"))

            # ── Assistant text (full message or delta) ───────────────────
            elif etype == "assistant":
                for block in event.get("message", {}).get("content", []):
                    if block.get("type") == "text":
                        text_buffer += block["text"]
                if text_buffer:
                    live.update(Markdown(text_buffer))

            # ── Tool calls ───────────────────────────────────────────────
            elif etype == "tool_call":
                if verbose:
                    markup = _tool_markup(event)
                    if markup:
                        # Tool events break out of the live block so they
                        # appear as static lines above the streaming text.
                        if event.get("subtype") == "started":
                            flush_buffer()
                        live.stop()
                        console.print(markup)
                        live.start()
                        if text_buffer:
                            live.update(Markdown(text_buffer))

            # ── Terminal result ──────────────────────────────────────────
            elif etype == "result":
                flush_buffer()
                live.stop()

                duration_ms = event.get("duration_ms", 0)
                is_error = event.get("is_error", False)
                exit_code = 1 if is_error else 0

                status = "[red]error[/red]" if is_error else "[green]done[/green]"
                console.print(f"\n[dim]{status} · {duration_ms:,} ms[/dim]")

    return exit_code


def print_error(msg: str) -> None:
    err_console.print(f"[red]Error:[/red] {msg}")


def print_warning(msg: str) -> None:
    err_console.print(f"[yellow]Warning:[/yellow] {msg}")
