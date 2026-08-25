"""Immutable domain models and coordinate mapping primitives."""

from bisect import bisect_right
from dataclasses import dataclass
from typing import NamedTuple

__all__ = [
    "NormalizationResult",
    "OffsetMap",
    "TextSpan",
]


class OffsetMap(NamedTuple):
    """Coordinate projection map between cleaned and raw text.

    Attributes:
        clean_keys: Clean text character offsets where delta transitions occur.
        cum_deltas: Cumulative offsets to add to clean indices to yield raw indices.
        raw_length: Total length of original raw text.
        clean_length: Total length of normalized text.
    """

    clean_keys: tuple[int, ...]
    cum_deltas: tuple[int, ...]
    raw_length: int
    clean_length: int

    @classmethod
    def identity(cls, length: int) -> "OffsetMap":
        """Create an identity 1:1 offset map.

        Args:
            length: Length of the text.

        Returns:
            OffsetMap with identity coordinate mapping.
        """
        return cls(clean_keys=(), cum_deltas=(), raw_length=length, clean_length=length)

    def clean_to_raw(self, clean_idx: int) -> int:
        """Project a cleaned text index back to its raw source offset.

        Args:
            clean_idx: Character offset in cleaned text.

        Returns:
            Corresponding character offset in raw text.
        """
        if not self.clean_keys:
            return min(clean_idx, self.raw_length)

        pos = bisect_right(self.clean_keys, clean_idx) - 1
        if pos < 0:
            return min(clean_idx, self.raw_length)
        return min(clean_idx + self.cum_deltas[pos], self.raw_length)

    def clean_span_to_raw_span(
        self, clean_start: int, clean_end: int
    ) -> tuple[int, int]:
        """Project a cleaned text span (start, end) back to raw source offsets.

        Args:
            clean_start: Start offset in cleaned text.
            clean_end: End offset in cleaned text.

        Returns:
            Tuple of (raw_start, raw_end) offsets in raw source text.
        """
        raw_start = self.clean_to_raw(clean_start)
        raw_end = self.clean_to_raw(clean_end)
        return (raw_start, max(raw_start, raw_end))


class NormalizationResult(NamedTuple):
    """Container pairing normalized text with its coordinate OffsetMap.

    Attributes:
        text: Normalized text string.
        offset_map: Coordinate mapping from clean text to raw text.
    """

    text: str
    offset_map: OffsetMap


@dataclass(slots=True, frozen=True)
class TextSpan:
    """Sentence span with source coordinates and optional normalized coordinates.

    Attributes:
        sent: Sentence text content.
        start: Start offset in original raw text.
        end: End offset in original raw text.
        clean_start: Optional start offset in cleaned text.
        clean_end: Optional end offset in cleaned text.
        raw_slice: Optional unnormalized source text slice.
        trailing_delim: Optional trailing paragraph or chunk delimiter.
    """

    sent: str
    start: int
    end: int
    clean_start: int | None = None
    clean_end: int | None = None
    raw_slice: str | None = None
    trailing_delim: str = ""

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
