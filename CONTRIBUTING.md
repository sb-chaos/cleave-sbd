# Contributing to cleave-sbd

Thank you for your interest in contributing to **cleave-sbd**!

## Development Setup

We use [`uv`](https://github.com/astral-sh/uv) for fast, deterministic dependency management and virtual environments:

```bash
# 1. Clone the repository
git clone https://github.com/sblasing/cleave-sbd.git
cd cleave-sbd

# 2. Sync all development dependencies
uv sync --all-groups
```

## Running Tests and Diagnostics

Before submitting a pull request, ensure all tests, linting, formatting, and type checks pass:

```bash
# Run pytest test suite
uv run pytest

# Run type checker (strict mode)
uv run basedpyright src/

# Run linter checks
uv run ruff check .

# Check formatting
uv run ruff format --check src/
```

## Core Architectural Principles

When making contributions, adhere to the core design principles of `cleave-sbd`:

1. **Strict Typing (PEP 561):** All code in `src/csbd/` must be fully type-annotated and pass `basedpyright` in strict mode with zero errors or warnings.
2. **Length Invariance:** Any preprocessing, masking, or normalization supporting character spans (`char_span=True`) must maintain exact $1:1$ character length preservation using Private Use Area (PUA) sentinels (`\ue000`–`\ue009`). Never add or remove characters in span mode.
3. **Declarative & Immutable:** Prefer pre-compiled regular expressions (`re.compile`), immutable data structures (`frozenset`, frozen dataclasses), and pure functional transformations over procedural loops or stateful mutations.
4. **Zero Runtime Dependencies:** `cleave-sbd` is a pure-Python library with zero external runtime dependencies.

## Contributing Workflows

### Fixing Bugs

1. Add a minimal reproducing test case to [`tests/regression/test_issues.py`](tests/regression/test_issues.py).
2. Implement the fix in `src/csbd/` ensuring length preservation and strict typing.
3. Verify that all tests and lint checks pass.

### Adding or Enhancing Language Support

1. Language rule sets live in [`src/csbd/language/configs/`](src/csbd/language/configs/).
2. Create or update the language module (e.g. `src/csbd/language/configs/<language>.toml`) using typed rules and frozenset collections.
3. Register the language in [`src/csbd/language/lang.py`](src/csbd/language/lang.py).
4. Add comprehensive test cases in `tests/lang/test_<language>.py`.

## Pull Request Guidelines

- Branch naming: `feat/<feature-name>`, `fix/<bug-name>`, or `refactor/<description>`.
- Commit messages: Follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`, `chore:`).
- Ensure all CI checks (pytest, ruff, basedpyright) pass locally before pushing.
