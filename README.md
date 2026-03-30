# JAFAT

**Just Another Fscking Agent Tool** — a Rich CLI wrapper for [Cursor Agent](https://cursor.sh) headless mode.

Stream agent responses with live Markdown rendering, inline tool-call visualization, and a clean config system.

---

## Getting Started

### Prerequisites

- Python 3.11+
- [Cursor](https://cursor.sh) installed with `cursor agent` available in your PATH (or the standalone `agent` binary)

### Install with uv (recommended)

Install as a persistent tool:

```sh
uv tool install jafat
```

Or run without installing:

```sh
uvx jafat ask "What does this repo do?"
```

### Install with pip

```sh
pip install jafat
```

### Install from source

```sh
git clone https://github.com/wwff-tech/jafat
cd jafat
uv tool install -e .
```

---

## Usage

```sh
# Ask a question without modifying files (read-only)
jafat ask "Explain the authentication flow"

# Run the agent with full tool access
jafat run "Refactor foo.py to use dataclasses"

# Show tool calls inline as they happen
jafat run --verbose "Add type hints to bar.py"

# Use a specific model
jafat run --model composer-2 "Fix the bug in baz.py"

# Run in an isolated git worktree
jafat run --worktree my-branch "Rewrite the tests"

# List available models
jafat models

# Show account/auth status
jafat status
```

### Config

Initialise a config file at `~/.config/jafat/config.toml`:

```sh
jafat config init
jafat config show
```

Default config values:

```toml
[defaults]
model   = "composer-2-fast"
trust   = true
verbose = false
force   = false
partial = true
```

---

## Development

This project uses [uv](https://docs.astral.sh/uv/) for environment management.

```sh
# Set up the dev environment
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check src tests

# Format
uv run ruff format src tests

# Type check
uv run mypy src

# Lint markdown
npx markdownlint-cli "**/*.md" --ignore node_modules
```

---

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).
