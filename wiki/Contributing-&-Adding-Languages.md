# Contributing & Adding Languages

We welcome contributions to **cleave-sbd**! This guide details development workflows, quality gates, and step-by-step instructions for adding support for new languages.

---

## 1. Development Setup

We use [`uv`](https://github.com/astral-sh/uv) for fast, deterministic dependency management and virtual environments:

```bash
# 1. Clone repository
git clone https://github.com/sb-chaos/cleave-sbd.git
cd cleave-sbd

# 2. Install all development dependencies (pytest, basedpyright, ruff)
uv sync --all-groups
```

---

## 2. Automated Quality Gates (`validate.sh`)

Every pull request must pass the automated validation script before merging:

```bash
bash validate.sh
```

`validate.sh` automatically runs:
1. **Ruff Auto-Fixes & Formatting:** `uv run ruff check --fix && uv run ruff format`
2. **Strict Lint Verification:** `uv run ruff check && uv run ruff format --check`
3. **Strict Type Checking:** `uv run basedpyright` (PEP 561 / strict mode with 0 errors)
4. **Pytest Test Suite:** `uv run pytest`
5. **Distribution Build:** `uv build`

---

## 3. Step-by-Step: Adding a New Language (e.g., the 23rd Language)

`cleave-sbd` is engineered with strict unidirectional decoupling. Adding a new language requires **zero modifications to core engine logic** (`segmenter.py`, `disambiguator.py`, or `models.py`).

### Step 1: Create the Language TOML Configuration

Add a new configuration file in `src/csbd/language/configs/<iso_code>.toml` (e.g., `src/csbd/language/configs/ko.toml` for Korean):

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

[clean_rules]
# Optional language-specific normalization rules
```

### Step 2: Register the Language

Add the language definition to `src/csbd/language/lang.py` under the `SUPPORTED_LANGUAGES` registry mapping.

### Step 3: Add Unit Tests

Create a golden test file in `tests/fixtures/golden_rules/<iso_code>.json` containing language-specific test cases (abbreviations, dialogues, numbers, quotes), and verify with:

```bash
uv run pytest tests/test_languages.py -k <iso_code>
```

---

## 4. Architectural Rules for Contributors

When submitting changes, adhere strictly to the project's [Architecture & Engineering Philosophy](Architecture-and-Engineering-Philosophy):

1. **Zero External Runtime Dependencies:** Rely solely on Python 3.11+ standard library primitives. Never add dependencies to `[project.dependencies]`.
2. **Strict Typing (PEP 561):** All new code must be fully type-annotated without untyped dictionaries (`dict[str, Any]`) or implicit `Any`.
3. **Layered Decoupling:** Never declare data models in processing or orchestrator layers.
4. **Declarative Rules:** Do not write runtime lambda callbacks or dynamic regex compilations inside loops. Use immutable `Rule(pattern, replacement)` tuples.
5. **Coordinate Invariance:** Preserve 1:1 length invariance with PUA sentinels, or use `_DeltaCollector` for normalizations.
