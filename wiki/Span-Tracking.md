# Span Tracking & Coordinate Invariance

When you segment text, downstream tools often need to highlight the original document or PDF. If you clean the text first (stripping HTML, fixing line breaks), character positions shift. 

We solve this using two complementary mechanisms:
1. **PUA Sentinel Masking:** 1:1 character replacements for zero-drift disambiguation (`clean=False`).
2. **Cumulative Delta Tracking (`OffsetMap`):** An $O(\log K)$ binary search map that projects coordinates from cleaned text back to raw source text (`clean=True`).

---

## 1. PUA Sentinel Masking (Zero-Drift Mode)

In standard mode (`clean=False`), `cleave-sbd` never modifies the length of the string buffer:

$$\text{len}(\text{masked\_text}) == \text{len}(\text{original\_text})$$

Periods and punctuation inside abbreviations, numbers, quotes, and ellipses are temporarily substituted 1:1 with single-character Unicode Private Use Area (PUA) codepoints (`\ue000`–`\ue021`):

| Punctuation Type | Character | PUA Sentinel | Codepoint |
| :--- | :---: | :---: | :---: |
| Standard Period (Abbr / Honorific) | `.` | `\ue000` | `PUA_PERIOD` |
| CJK Fullwidth Period | `。` | `\ue001` | `PUA_CJK_PERIOD` |
| Fullwidth Period | `．` | `\ue002` | `PUA_FULLWIDTH_PERIOD` |
| Exclamation Mark | `!` | `\ue004` | `PUA_EXCLAMATION` |
| Question Mark | `?` | `\ue005` | `PUA_QUESTION` |
| Ellipsis Dot | `.` | `\ue020` | `PUA_ELLIPSIS_DOT` |

Because every substitution preserves length 1:1, slice coordinates `(start, end)` extracted from `masked_text` map directly to `original_text[start:end]`. Once boundaries are identified, `unmask_all()` restores sentinels in a single C-level `.translate()` pass.

---

## 2. Cumulative Delta Tracking (`OffsetMap`)

When you enable `clean=True`, normalizers strip HTML tags, fix quote formatting, and repair broken OCR/PDF line breaks. These operations change string length.

To preserve original coordinates, we track every length modification in an immutable `OffsetMap`:

```
Raw Source Text (Length = 39):
[0]                                                    [38]
 v                                                      v
"<p>Hello world! This is a test sentence.</p>"

Transformations Applied:
 1. Strip '<p>'  at raw [0:3]   -> Net shift: +3 chars deleted
 2. Strip '</p>' at raw [35:39] -> Net shift: +4 chars deleted (Total cumulative delta: +7)

Cleaned Text Buffer (Length = 32):
[0]                                  [31]
 v                                    v
"Hello world! This is a test sentence."

OffsetMap Internal Arrays:
  clean_keys:  ( 0,  32 )
  cum_deltas:  ( 3,   7 )
```

### Projection via `bisect_right` ($O(\log K)$)

When sentence boundaries are found in the cleaned buffer, `OffsetMap.clean_span_to_raw_span()` projects them back to raw coordinates in $O(\log K)$ time:

```python
# Project Clean Span [0:12] ("Hello world!")
raw_start = offset_map.clean_to_raw(0)  # 0  + 3 = 3  (points to 'H' in raw text)
raw_end = offset_map.clean_to_raw(12)  # 12 + 3 = 15 (points to '!' in raw text)
# -> Raw Span: [3:15] maps directly to: "<p>[Hello world!] This is..."

# Project Clean Span [13:32] ("This is a test sentence.")
raw_start = offset_map.clean_to_raw(13)  # 13 + 3 = 16 (points to 'T' in raw text)
raw_end = offset_map.clean_to_raw(32)  # 32 + 7 = 39 (points to end of raw text)
# -> Raw Span: [16:39] maps directly to: "...[This is a test sentence.]</p>"
```

---

## 3. The `TextSpan` Structure

When `char_span=True` is enabled, sentences are returned as immutable, slotted `TextSpan` objects:

```python
@dataclass(slots=True, frozen=True)
class TextSpan:
    sent: str  # Normalized sentence string (for LLMs / NLP models)
    start: int  # Raw original document start index (for UI highlights)
    end: int  # Raw original document end index (for UI highlights)
    clean_start: int | None  # Cleaned buffer start index (optional)
    clean_end: int | None  # Cleaned buffer end index (optional)
    raw_slice: str | None  # Raw uncleaned slice text[start:end] (optional)
```

This guarantees:
1. **Downstream NLP models & LLMs** receive clean, normalized sentence text via `span.sent`.
2. **Frontend UI renderers & PDF viewers** receive exact source coordinates (`span.start`, `span.end`) to paint highlights onto the original document without offset drift.
