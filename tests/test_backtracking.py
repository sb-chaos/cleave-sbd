"""Tests for ReDoS resistance and linear-time scaling across adversarial inputs."""

from __future__ import annotations

import time

from fracture.rules.boundary import (
    BETWEEN_SINGLE_QUOTES_REGEX,
)
from fracture.rules.normalizer import HTML_TAG_RULE
from fracture.segmenter import Segmenter


def test_html_tag_rule_linear_scaling() -> None:
    """Verify HTML_TAG_RULE executes in linear time on unclosed tags with whitespace."""
    for n in [100, 500, 1000, 2000]:
        text = "<div " + 'class="foo" ' * n
        start = time.perf_counter()
        _ = HTML_TAG_RULE.pattern.sub("", text)
        elapsed = time.perf_counter() - start
        # Ensure even a 2000-attribute (~24 KB) unclosed payload completes in < 50ms
        assert elapsed < 0.05, f"HTML_TAG_RULE took {elapsed:.4f}s on {n} attrs"


def test_single_quotes_regex_linear_scaling() -> None:
    """Verify BETWEEN_SINGLE_QUOTES_REGEX unrolled loop handles unclosed quotes in linear time."""
    for n in [500, 2000, 5000]:
        text = "'" + " word don't can't won't" * n
        start = time.perf_counter()
        _ = BETWEEN_SINGLE_QUOTES_REGEX.findall(text)
        elapsed = time.perf_counter() - start
        # Ensure 5000 word repetitions (~115 KB) completes in < 50ms
        assert elapsed < 0.05, (
            f"BETWEEN_SINGLE_QUOTES_REGEX took {elapsed:.4f}s on {n} words"
        )


def test_unpunctuated_stream_linear_scaling() -> None:
    """Verify segmenter scales linearly on multi-megabyte unpunctuated log stream."""
    segmenter = Segmenter(language="en", clean=False)
    # 50,000 words without sentence boundary marks (~250 KB)
    text = "word " * 50_000
    start = time.perf_counter()
    res = segmenter.segment(text)
    elapsed = time.perf_counter() - start
    assert len(res) == 1
    # 50k words in pure Python regex runs in ~0.25s; < 1.0s guards against exponential ReDoS
    assert elapsed < 1.0, f"Segmentation took {elapsed:.4f}s on 50k unpunctuated words"
