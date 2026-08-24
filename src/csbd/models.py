"""Immutable domain models and zero-overhead NamedTuple primitives."""

from bisect import bisect_right
from dataclasses import dataclass
from typing import NamedTuple

__all__ = [
    "NormalizationResult",
    "OffsetMap",
    "TextSpan",
]


class OffsetMap(NamedTuple):
    """Immutable, bisect-accelerated coordinate projection map between cleaned and raw text."""

    clean_keys: tuple[int, ...]
    cum_deltas: tuple[int, ...]
    raw_length: int
    clean_length: int

    @classmethod
    def identity(cls, length: int) -> "OffsetMap":
        """Construct an identity offset map for uncleaned text (1:1 mapping)."""
        return cls(clean_keys=(), cum_deltas=(), raw_length=length, clean_length=length)

    def clean_to_raw(self, clean_idx: int) -> int:
        """Map a character offset from the cleaned text to the raw source text in O(log K) time."""
        if not self.clean_keys:
            return min(clean_idx, self.raw_length)

        pos = bisect_right(self.clean_keys, clean_idx) - 1
        if pos < 0:
            return min(clean_idx, self.raw_length)
        return min(clean_idx + self.cum_deltas[pos], self.raw_length)

    def clean_span_to_raw_span(
        self, clean_start: int, clean_end: int
    ) -> tuple[int, int]:
        """Project a (start, end) coordinate span from cleaned text to raw source text."""
        raw_start = self.clean_to_raw(clean_start)
        raw_end = self.clean_to_raw(clean_end)
        return (raw_start, max(raw_start, raw_end))


class NormalizationResult(NamedTuple):
    """Lightweight result tuple pairing cleaned text with its OffsetMap."""

    text: str
    offset_map: OffsetMap


@dataclass(slots=True, frozen=True)
class TextSpan:
    """A sentence span with original source coordinates and optional normalized coordinates."""

    sent: str
    start: int
    end: int
    clean_start: int | None = None
    clean_end: int | None = None
    raw_slice: str | None = None

    def __repr__(self) -> str:
        return self.sent

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TextSpan):
            return (
                self.sent == other.sent
                and self.start == other.start
                and self.end == other.end
            )
        return False
