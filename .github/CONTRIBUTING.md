# Contributing to JAFAT

Thank you for taking the time to contribute!

## Getting Started

1. Fork the repository and clone your fork.
2. Set up the dev environment:

   ```sh
   uv sync
   ```

3. Create a branch for your change:

   ```sh
   git checkout -b feat/my-change
   ```

## Making Changes

- Keep changes focused. One concern per PR.
- Add or update tests in `tests/` for any logic you change.
- Run the full check suite before opening a PR:

  ```sh
  uv run ruff check src tests
  uv run ruff format src tests
  uv run mypy src
  uv run pytest
  ```

## Commit Style

Use short imperative commit messages, e.g. `add worktree flag to ask command`.

## Opening a Pull Request

- Fill in the PR template.
- Link any related issues.
- Keep the description concise — let the diff speak.

## Reporting Issues

Use the [bug report](.github/ISSUE_TEMPLATE/bug_report.md) or [feature request](.github/ISSUE_TEMPLATE/feature_request.md) templates.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating.
