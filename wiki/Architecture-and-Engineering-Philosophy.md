# Architecture & Engineering Philosophy

`cleave-sbd` is designed from first principles under strict architectural constraints to guarantee high cohesion, loose coupling, thread-safe concurrency, and C-level execution speed.

---

## The 10 Core Architectural Principles

### 1. Zero External Runtime Dependencies
Built exclusively on the Python 3.11+ standard library (`re`, `itertools`, `bisect`, `dataclasses`, `typing`, `tomllib`). `pyproject.toml` contains zero third-party runtime dependencies, eliminating supply-chain vulnerabilities, installation friction, and version drift.

### 2. Strict Typing & PEP 561 Compliance
Verified in strict mode under Basedpyright, Pyright, and Mypy. Fully PEP 561 compliant with an embedded `py.typed` marker. Uses modern native union syntax (`T | None`), structural `typing.Protocol` interfaces, and memory-optimized `slots=True`.

### 3. Layered Decoupling of Data & Logic
Strict unidirectional import hierarchy:
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
Data models carry no computational algorithms or side effects; functional transformers declare no custom data carrier classes.

### 4. Right-Sized Immutable Modeling
Uses lightweight `typing.NamedTuple` for zero-overhead mathematical vectors, rules, and coordinate maps (`Rule`, `OffsetMap`, `NormalizationResult`), while reserving `@dataclass(slots=True, frozen=True)` for rich domain entities (`TextSpan`) requiring optional fields, custom representation formatting, or computed helper properties.

### 5. Declarative Static Automata
Avoids inline `lambda` callbacks, runtime closures, and dynamic regular expression compilation in hot loops. All regex patterns and replacement templates are pre-compiled at module import time into immutable constants (`SCREAMING_SNAKE_CASE`).

### 6. C-Speed Execution & Invariant Coordinates
Employs monotonic `OffsetMap` structures with $O(\log K)$ standard library `bisect_right` binary searching. This enables exact bidirectional character coordinate mapping back to raw source text even after destructive text normalization (HTML stripping, whitespace normalization, PDF line-wrap repair).

### 7. Hybrid Lazy Streaming & Pure Concurrency
Supports unbounded multi-megabyte corpora through lazy paragraph chunk streaming (`Segmenter.stream()`) with constant $O(\text{chunk\_size})$ memory overhead. Because all domain models and transformation passes are stateless and deeply immutable, they execute safely across multi-worker threads and processes without locks.

### 8. Fail-Fast Configuration & Non-Destructive Fallbacks
Invalid configuration options or illegal parameter combinations fail fast during initialization (`ValueError`, `KeyError`). For messy real-world text inputs, the pipeline falls back gracefully without exceptions: coordinate lookups clamp to valid text bounds `[0, len(raw)]`, unparseable segments return full spans, and empty inputs return empty tuples `()`.

### 9. Unidirectional Dependency Flow & Encapsulation
Dependencies flow downward only. Every module explicitly defines and restricts its public surface area via `__all__`, encapsulating private regex automata and internal helpers behind leading underscores.

### 10. Deterministic Spatial & Action Standards
Spatial coordinate identifiers are explicit and unambiguous (`clean_start`, `raw_start`, `clean_keys`, `cum_deltas`), and functional transformation routines use clear imperative verbs (`normalize_with_map`, `mask_exclamation_words`, `disambiguate`).
