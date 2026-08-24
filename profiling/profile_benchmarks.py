"""Comprehensive profiler for fracture pipeline and large benchmark datasets."""

from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import time
from pathlib import Path
from typing import Final

import fracture


def profile_file(
    file_path: str,
    language: str = "en",
    *,
    stream_mode: bool = False,
    chunk_paragraphs: int = 1000,
) -> None:
    """Run cProfile on a text file and output detailed stage and function statistics.

    Args:
        file_path: Relative or absolute path to the benchmark file.
        language: Two-letter ISO language code. Defaults to 'en'.
        stream_mode: If True, uses seg.stream(); if False, uses seg.segment().
        chunk_paragraphs: Number of paragraphs per chunk in streaming mode. Defaults to 1000.
    """
    path: Final[Path] = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        return

    text: Final[str] = path.read_text(encoding="utf-8")
    size_mb: Final[float] = len(text) / (1024 * 1024)
    mode_name = (
        f"STREAMING (segmenter.stream, chunk_paragraphs={chunk_paragraphs})"
        if stream_mode
        else "BATCH (segmenter.segment)"
    )

    print(f"\n{'=' * 70}")
    print(
        f"Profiling {path.name} ({size_mb:.2f} MB, {len(text):,} characters) [{mode_name}]"
    )
    print(f"{'=' * 70}")

    seg = fracture.Segmenter(language=language, clean=False)

    pr = cProfile.Profile()
    pr.enable()

    start = time.perf_counter()
    sentences = (
        list(seg.stream(text, chunk_paragraphs=chunk_paragraphs))
        if stream_mode
        else list(seg.segment(text))
    )
    elapsed = time.perf_counter() - start

    pr.disable()

    print(
        f"Result: {len(sentences):,} sentences in {elapsed:.3f}s ({size_mb / elapsed:.2f} MB/s)"
    )

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats(pstats.SortKey.TIME)
    ps.print_stats(25)
    print("\n--- Top 25 Functions by Internal Self Time (tottime) ---")
    print(s.getvalue())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profile fracture on benchmark files.")
    parser.add_argument(
        "--file",
        "-f",
        default="benchmarks/pg100.txt",
        help="Path to the benchmark text file (default: benchmarks/pg100.txt)",
    )
    parser.add_argument(
        "--stream",
        "-s",
        action="store_true",
        help="Toggle streaming mode (segmenter.stream) instead of batch mode (segmenter.segment)",
    )
    parser.add_argument(
        "--chunk-paragraphs",
        "-c",
        type=int,
        default=1000,
        help="Number of paragraphs held in each chunk during streaming mode (default: 1000)",
    )
    args = parser.parse_args()

    target_file = args.file
    if not Path(target_file).exists():
        target_file = "benchmarks/1661-0.txt"

    profile_file(
        target_file,
        stream_mode=args.stream,
        chunk_paragraphs=args.chunk_paragraphs,
    )
