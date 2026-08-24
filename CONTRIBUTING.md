# Contributing to cleave-sbd

Thank you for contributing to **cleave-sbd**!

---

## Quick Setup

We use [`uv`](https://github.com/astral-sh/uv) for fast, deterministic development:

```bash
# 1. Clone repository
git clone https://github.com/sb-chaos/cleave-sbd.git
cd cleave-sbd

# 2. Sync all development dependencies
uv sync --all-groups
```

---

## Automated Validation & Quality Gates

Run the local validation script before submitting any pull request:

```bash
bash validate.sh
```

This runs safe auto-formatting, strict linting (`ruff`), strict type checking (`basedpyright`), test suites (`pytest`), and package builds (`uv build`).

---

## Complete Contributing Guide & Adding Languages

For detailed guides, please see our GitHub Wiki:

* **[Contributing](https://github.com/sb-chaos/cleave-sbd/wiki/Contributing)**: Step-by-step instructions for adding the 23rd language, creating TOML configs, and registering rules.
* **[Design Philosophy](https://github.com/sb-chaos/cleave-sbd/wiki/Design-Philosophy)**: Core design principles, layered decoupling, and strict typing standards.
