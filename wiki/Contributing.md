# Contributing & Adding Languages

We welcome contributions. Adding a new language takes about 10 minutes and requires zero changes to the core segmentation engine.

---

## 1. Quick Setup

We use [`uv`](https://github.com/astral-sh/uv) for fast, deterministic development:

```bash
# 1. Clone repository
git clone https://github.com/sb-chaos/cleave-sbd.git
cd cleave-sbd

# 2. Install all development dependencies (pytest, basedpyright, ruff)
uv sync --all-groups
```

---

## 2. Quality Checks (`validate.sh`)

Before opening a PR, run the local validation script:

```bash
bash validate.sh
```

This runs:
1. **Ruff Auto-Fixes & Formatting:** `uv run ruff check --fix && uv run ruff format`
2. **Strict Lint Verification:** `uv run ruff check && uv run ruff format --check`
3. **Strict Type Checking:** `uv run basedpyright` (PEP 561 / strict mode with 0 errors)
4. **Pytest Test Suite:** `uv run pytest`
5. **Distribution Build:** `uv build`

---

## 3. How to Add a New Language (e.g. the 23rd Language)

Adding a language requires **zero changes to core engine logic** (`segmenter.py`, `disambiguator.py`, or `models.py`).

### Step 1: Create the Language TOML File

Add a configuration file in `src/csbd/language/configs/<iso_code>.toml` (e.g. `src/csbd/language/configs/ko.toml` for Korean):

```toml
[language]
code = "ko"
name = "Korean"
replace_all_abbr_periods = false

[punctuations]
marks = ["。", "！", "？", ".", "!", "?"]

[abbreviations]
standard = [
    "etc",
    "co",
    "inc",
]
prepositive = [
    "dr",
    "prof",
    "mr",
    "ms",
]
number = [
    "no",
    "vol",
    "p",
]
```

### Step 2: Register the Language

Add the language definition to `src/csbd/language/lang.py` under the `SUPPORTED_LANGUAGES` mapping.

### Step 3: Add Golden Tests

Create a test file in `tests/fixtures/golden_rules/<iso_code>.json` with language-specific test sentences, and run:

```bash
uv run pytest tests/test_languages.py -k <iso_code>
```

---

## 4. Design Invariants for Contributors

When submitting changes, follow the [Architecture Philosophy](Architecture-Philosophy):

1. **Zero Runtime Dependencies:** Rely solely on Python 3.11+ standard library modules. Never add packages to `[project.dependencies]`.
2. **Strict Typing (PEP 561):** All code must be fully annotated with zero untyped dictionaries or implicit `Any`.
3. **Layered Decoupling:** Never declare data models inside processing or orchestrator layers.
4. **Declarative Rules:** Avoid runtime lambdas or dynamic regex compilations inside loops. Use immutable `Rule(pattern, replacement)` tuples.
