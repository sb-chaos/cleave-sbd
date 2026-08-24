# Design Philosophy

`cleave-sbd` is built to run fast, stay lightweight, and never corrupt text coordinates. These 10 design rules govern how we write code across the library.

---

## 1. Zero External Dependencies
We rely strictly on the Python 3.11+ standard library (`re`, `itertools`, `bisect`, `dataclasses`, `typing`, `tomllib`). `pyproject.toml` has zero runtime dependencies, eliminating supply-chain audits, installation headaches, and version drift.

## 2. Strict Typing (PEP 561)
Every file is fully type-annotated and checked in strict mode with Basedpyright and Mypy. We use modern native unions (`T | None`), structural `Protocol` typing, and memory-optimized `slots=True`. Untyped data from TOML files is sanitized at the ingestion boundary and immediately mapped to concrete types.

## 3. Layered Decoupling of Data & Logic
We enforce a strict one-way import hierarchy:
```text
Layer 0: Domain Models & Protocols (models.py, protocols.py)
    │
    ▼
Layer 1: Rules & Lookup Tables (rules/)
    │
    ▼
Layer 2: Pure Functional Transformers (normalizer.py, disambiguator.py, processors/)
    │
    ▼
Layer 3: Orchestrators & Public API (segmenter.py, __init__.py)
```
Data models carry zero business logic. Logic modules declare no custom data carrier classes.

## 4. Right-Sized Immutable Modeling
We use `typing.NamedTuple` for zero-overhead mathematical vectors, offsets, and static rules (`Rule`, `OffsetMap`, `NormalizationResult`). We reserve `@dataclass(slots=True, frozen=True)` for rich domain entities (`TextSpan`) that need optional fields or custom formatting.

## 5. Declarative Static Automata
No runtime closures, lambdas, or dynamic regex compilations inside loops. All regex patterns and replacement templates are pre-compiled at import time into immutable `SCREAMING_SNAKE_CASE` constants.

## 6. C-Speed Execution & Invariant Coordinates
Hot loops rely on C-accelerated standard library modules. When text is cleaned, an immutable, $O(\log K)$ `OffsetMap` uses `bisect_right` to project character coordinates back to the raw source text without string searching.

## 7. Hybrid Lazy Streaming & Pure Concurrency
For large books or corpora, `Segmenter.stream()` yields sentences lazily across paragraph boundaries, keeping memory usage constant at $O(\text{chunk\_size})$. Because models and transformers are pure and deeply immutable, they run across worker threads and processes without locks.

## 8. Fail-Fast Configuration & Non-Destructive Fallbacks
Invalid configurations fail immediately during initialization (`ValueError`). In contrast, messy real-world text never crashes worker pools: coordinate lookups clamp to `[0, len(raw)]`, unparseable segments return full spans, and empty inputs yield empty tuples `()`.

## 9. Downward Dependency Flow & Encapsulation
Dependencies flow downward only. Every module explicitly defines its public API via `__all__`, keeping helper functions and internal regexes private behind leading underscores.

## 10. Explicit Naming Standards
Spatial coordinate identifiers are explicit (`clean_start`, `raw_start`, `clean_keys`, `cum_deltas`). Pure functional routines use imperative action verbs (`normalize_with_map`, `mask_exclamation_words`, `disambiguate`).
