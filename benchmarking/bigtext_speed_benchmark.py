"""Speed benchmark comparing pragmatic-sbd against popular NLP sentence tokenizers.

Supported engines:
- pragmatic-sbd (clean=False, clean=True, char_span=True)
- blingfire
- nltk (sent_tokenize)
- spacy (sentencizer / blank("en"))
- spacy (en_core_web_sm dependency parse)
- stanza (tokenize)
- syntok
- pysbd (if available)

Usage:
    uv run python tests/bigtext_speed_benchmark.py
    uv run python tests/bigtext_speed_benchmark.py --iterations 5 --warmup 1
    uv run python tests/bigtext_speed_benchmark.py --file path/to/text.txt
"""

from __future__ import annotations

import argparse
import importlib
import json
import statistics
import sys
import time
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pragmatic_sbd

DEFAULT_BENCHMARK_URL: str = "https://www.gutenberg.org/cache/epub/100/pg100.txt"
DEFAULT_BENCHMARK_PATH: Path = Path("benchmarks/pg100.txt")

FALLBACK_SAMPLE_TEXT: str = (
    """\
The Adventures of Sherlock Holmes by Arthur Conan Doyle.
To Sherlock Holmes she is always THE woman. I have seldom heard him mention her under any other name.
In his eyes she eclipses and predominates the whole of her sex. It was not that he felt any emotion akin to love for Irene Adler.
All emotions, and that one particularly, were abhorrent to his cold, precise but admirably balanced mind.
He was, I take it, the most perfect reasoning and observing machine that the world has seen, but as a lover he would have placed himself in a false position.
He never spoke of the softer passions, save with a gibe and a sneer. They were admirable things for the observer—excellent for drawing the veil from men's motives and actions.
But for the trained reasoner to admit such intrusions into his own delicate and finely adjusted temperament was to introduce a distracting factor which might throw a doubt upon all his mental results.
Grit in a sensitive instrument, or a crack in one of his own high-power lenses, would not be more disturbing than a strong emotion in a nature such as his.
And yet there was but one woman to him, and that woman was the late Irene Adler, of dubious and questionable memory.
I had seen little of Holmes lately. My marriage had drifted us away from each other.
My own complete happiness, and the home-centred interests which rise up around the man who first finds himself master of his own establishment, were sufficient to absorb all my attention.
While Holmes, who loathed every form of society with his whole Bohemian soul, remained in our lodgings in Baker Street, buried among his old books, and alternating from week to week between cocaine and ambition.
The drowsiness of the drug, and the fierce energy of his own keen nature.
He was still, as ever, deeply attracted by the study of crime, and occupied his immense faculties and extraordinary powers of observation in following out those clues, and clearing up those mysteries which had been abandoned as hopeless by the official police.
From time to time I heard some vague account of his doings: of his summons to Odessa in the case of the Trepoff murder, of his clearing up of the singular tragedy of the Atkinson brothers at Trincomalee, and finally of the mission which he had accomplished so delicately and successfully for the reigning family of Holland.
Beyond these signs of his activity, however, which I merely shared with all the readers of the daily press, I knew little of my former friend and companion.
"""
    * 1000
)  # Repeat for a realistic ~1.5 MB benchmark workload if offline


@dataclass
class EngineResult:
    """Benchmark performance metrics for a single tokenizer engine."""

    name: str
    available: bool
    status_message: str = "OK"
    sentence_count: int = 0
    iterations: int = 0
    min_ms: float = 0.0
    mean_ms: float = 0.0
    median_ms: float = 0.0
    std_dev_ms: float = 0.0
    throughput_mb_s: float = 0.0
    throughput_chars_per_sec: float = 0.0
    throughput_sents_per_sec: float = 0.0
    speedup_vs_baseline: float = 1.0
    raw_times_s: list[float] = field(default_factory=list)


TokenizerFn = Callable[[str], Sequence[object]]


def setup_pragmatic_sbd_fast() -> tuple[TokenizerFn | None, str | None]:
    """Pragmatic SBD without cleaner (pure SBD)."""
    segmenter = pragmatic_sbd.Segmenter(language="en", clean=False, char_span=False)
    return segmenter.segment, None


def setup_pragmatic_sbd_clean() -> tuple[TokenizerFn | None, str | None]:
    """Pragmatic SBD with pre-cleaning enabled."""
    segmenter = pragmatic_sbd.Segmenter(language="en", clean=True, char_span=False)
    return segmenter.segment, None


def setup_pragmatic_sbd_char_span() -> tuple[TokenizerFn | None, str | None]:
    """Pragmatic SBD with character span offset calculation."""
    segmenter = pragmatic_sbd.Segmenter(language="en", clean=False, char_span=True)
    return segmenter.segment, None


def setup_blingfire() -> tuple[TokenizerFn | None, str | None]:
    """BlingFire sentence tokenizer."""
    try:
        blingfire: Any = importlib.import_module("blingfire")  # pyright: ignore[reportExplicitAny,reportUnknownMemberType]

        def tokenize(text: str) -> list[str]:
            res: str = blingfire.text_to_sentences(text)  # pyright: ignore[reportAny]
            return res.split("\n")

        return tokenize, None
    except ImportError:
        return None, "blingfire not installed"
    except Exception as exc:
        return None, f"blingfire initialization error: {exc}"


def setup_nltk() -> tuple[TokenizerFn | None, str | None]:
    """NLTK sent_tokenize."""
    try:
        nltk: Any = importlib.import_module("nltk")  # pyright: ignore[reportExplicitAny,reportUnknownMemberType]
        try:
            nltk.sent_tokenize("Test sentence. Another sentence.")  # pyright: ignore[reportAny]
        except LookupError:
            nltk.download("punkt", quiet=True)  # pyright: ignore[reportAny]
            nltk.download("punkt_tab", quiet=True)  # pyright: ignore[reportAny]

        def tokenize(text: str) -> list[str]:
            res: list[str] = nltk.sent_tokenize(text)  # pyright: ignore[reportAny]
            return res

        return tokenize, None
    except ImportError:
        return None, "nltk not installed"
    except Exception as exc:
        return None, f"nltk initialization error: {exc}"


def setup_spacy_sentencizer() -> tuple[TokenizerFn | None, str | None]:
    """spaCy blank English model with rule-based Sentencizer pipe."""
    try:
        spacy: Any = importlib.import_module("spacy")  # pyright: ignore[reportExplicitAny,reportUnknownMemberType]
        nlp: Any = spacy.blank("en")  # pyright: ignore[reportAny,reportExplicitAny]
        nlp.add_pipe("sentencizer")  # pyright: ignore[reportAny]

        def tokenize(text: str) -> list[str]:
            if len(text) > nlp.max_length:
                nlp.max_length = len(text) + 100000
            doc: Any = nlp(text)  # pyright: ignore[reportAny,reportExplicitAny]
            return [sent.text for sent in doc.sents]  # pyright: ignore[reportAny]

        return tokenize, None
    except ImportError:
        return None, "spacy not installed"
    except Exception as exc:
        return None, f"spacy sentencizer error: {exc}"


def setup_spacy_dep() -> tuple[TokenizerFn | None, str | None]:
    """spaCy en_core_web_sm dependency parse sentence segmenter."""
    try:
        spacy: Any = importlib.import_module("spacy")
        try:
            nlp: Any = spacy.load("en_core_web_sm", disable=["ner"])
        except Exception:
            try:
                spacy_cli: Any = importlib.import_module("spacy.cli")
                spacy_cli.download("en_core_web_sm")
                nlp = spacy.load("en_core_web_sm", disable=["ner"])
            except Exception as exc:
                return (
                    None,
                    f"spacy model 'en_core_web_sm' not installed (install via: uv pip install en_core_web_sm): {exc}",
                )

        def tokenize(text: str) -> list[str]:
            if len(text) > nlp.max_length:
                nlp.max_length = len(text) + 100000
            doc: Any = nlp(text)
            return [sent.text for sent in doc.sents]

        return tokenize, None
    except ImportError:
        return None, "spacy not installed"
    except Exception as exc:
        return None, f"spacy dependency model error: {exc}"


def setup_syntok() -> tuple[TokenizerFn | None, str | None]:
    """Syntok segmenter and tokenizer."""
    try:
        syntok_seg: Any = importlib.import_module("syntok.segmenter")  # pyright: ignore[reportExplicitAny,reportUnknownMemberType]
        syntok_tok: Any = importlib.import_module("syntok.tokenizer")  # pyright: ignore[reportExplicitAny,reportUnknownMemberType]
        tokenizer_inst: Any = syntok_tok.Tokenizer()  # pyright: ignore[reportAny,reportExplicitAny]

        def tokenize(text: str) -> list[str]:
            tokens: Any = tokenizer_inst.split(text)  # pyright: ignore[reportAny,reportExplicitAny]
            token_sentences: Any = syntok_seg.split(iter(tokens))  # pyright: ignore[reportAny,reportExplicitAny]
            sents: list[str] = []
            for sentence in token_sentences:  # pyright: ignore[reportAny]
                sents.append("".join(str(tok) for tok in sentence).strip())  # pyright: ignore[reportAny]
            return sents

        return tokenize, None
    except ImportError:
        return None, "syntok not installed"
    except Exception as exc:
        return None, f"syntok error: {exc}"


def setup_stanza() -> tuple[TokenizerFn | None, str | None]:
    """Stanza tokenize pipeline."""
    try:
        stanza: Any = importlib.import_module("stanza")  # pyright: ignore[reportExplicitAny,reportUnknownMemberType]
        try:
            pipeline_inst: Any = stanza.Pipeline(  # pyright: ignore[reportAny,reportExplicitAny]
                lang="en",
                processors="tokenize",
                download_method=None,
                verbose=False,
            )
        except Exception:
            stanza.download("en", processors="tokenize", verbose=False)
            pipeline_inst = stanza.Pipeline(
                lang="en",
                processors="tokenize",
                download_method=None,
                verbose=False,
            )

        def tokenize(text: str) -> list[str]:
            doc: Any = pipeline_inst(text)  # pyright: ignore[reportAny,reportExplicitAny]
            return [e.text for e in doc.sentences]  # pyright: ignore[reportAny]

        return tokenize, None
    except ImportError:
        return None, "stanza not installed"
    except Exception as exc:
        return None, f"stanza error: {exc}"


def setup_pysbd() -> tuple[TokenizerFn | None, str | None]:
    """Legacy pySBD segmenter."""
    try:
        pysbd: Any = importlib.import_module("pysbd")  # pyright: ignore[reportExplicitAny,reportUnknownMemberType]
        segmenter: Any = pysbd.Segmenter(language="en", clean=False)  # pyright: ignore[reportAny,reportExplicitAny]

        def tokenize(text: str) -> list[str]:
            res: list[str] = segmenter.segment(text)  # pyright: ignore[reportAny]
            return res

        return tokenize, None
    except ImportError:
        return None, "pysbd not installed"
    except Exception as exc:
        return None, f"pysbd error: {exc}"


AVAILABLE_ENGINES: list[tuple[str, Callable[[], tuple[TokenizerFn | None, str | None]]]] = [
    ("pragmatic-sbd (clean=False)", setup_pragmatic_sbd_fast),
    ("pragmatic-sbd (clean=True)", setup_pragmatic_sbd_clean),
    ("pragmatic-sbd (char_span=True)", setup_pragmatic_sbd_char_span),
    ("blingfire", setup_blingfire),
    ("nltk sent_tokenize", setup_nltk),
    ("spacy sentencizer", setup_spacy_sentencizer),
    ("spacy en_core_web_sm", setup_spacy_dep),
    ("syntok", setup_syntok),
    ("stanza", setup_stanza),
    ("pysbd", setup_pysbd),
]


def load_benchmark_text(
    file_path: Path | None = None,
    auto_download: bool = True,
    url: str = DEFAULT_BENCHMARK_URL,
) -> tuple[str, str]:
    """Retrieve benchmark text from file, URL download, or synthetic fallback."""
    target_path = file_path or DEFAULT_BENCHMARK_PATH

    if target_path.exists():
        text = target_path.read_text(encoding="utf-8", errors="replace")
        return text, f"Loaded from existing file: {target_path.as_posix()}"

    if auto_download:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading benchmark text from {url} to {target_path} ...", file=sys.stderr)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pragmatic-sbd-benchmark)"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                target_path.write_text(content, encoding="utf-8")
                return content, f"Downloaded from {url} and saved to {target_path.as_posix()}"
        except Exception as exc:
            print(f"Warning: Failed to download from {url}: {exc}. Using fallback text.", file=sys.stderr)

    return FALLBACK_SAMPLE_TEXT, "Using built-in multi-paragraph benchmark sample text"


def run_benchmark(
    text: str,
    iterations: int = 5,
    warmup: int = 1,
    selected_engines: list[str] | None = None,
) -> list[EngineResult]:
    """Run speed benchmarks across all selected tokenizers with terminal progress tracking."""
    text_bytes = len(text.encode("utf-8"))
    text_chars = len(text)
    text_mb = text_bytes / (1024 * 1024)

    results: list[EngineResult] = []
    baseline_mean_s: float | None = None

    print(
        f"\n>>> Running benchmark configuration: {warmup} warmup pass(es) | {iterations} timed pass(es) per engine\n",
        file=sys.stderr,
    )

    for name, setup_fn in AVAILABLE_ENGINES:
        if selected_engines and not any(sel.lower() in name.lower() for sel in selected_engines):
            continue

        fn, err_msg = setup_fn()
        if fn is None:
            print(f"{name}: Unavailable ({err_msg or 'Disabled'})", file=sys.stderr)
            results.append(
                EngineResult(
                    name=name,
                    available=False,
                    status_message=err_msg or "Unavailable",
                )
            )
            continue

        # Warmup passes
        for w in range(max(0, warmup)):
            pass_label = f"warmup {w + 1}"
            print(f"{name}: pass {pass_label} started...", end="", flush=True, file=sys.stderr)
            t0 = time.perf_counter()
            _ = fn(text)
            elapsed = time.perf_counter() - t0
            print(f"\r{name}: pass {pass_label} took {elapsed:.4f} seconds - complete", file=sys.stderr)

        # Timed iterations
        times: list[float] = []
        sentence_count: int = 0
        for i in range(max(1, iterations)):
            pass_label = f"#{i + 1}"
            print(f"{name}: pass {pass_label} started...", end="", flush=True, file=sys.stderr)
            t0 = time.perf_counter()
            segments = fn(text)
            t1 = time.perf_counter()
            elapsed = t1 - t0
            times.append(elapsed)
            sentence_count = len(segments)
            print(f"\r{name}: pass {pass_label} took {elapsed:.4f} seconds - complete", file=sys.stderr)

        min_s = min(times)
        mean_s = statistics.mean(times)
        median_s = statistics.median(times)
        std_dev_s = statistics.stdev(times) if len(times) > 1 else 0.0

        throughput_mb_s = text_mb / mean_s if mean_s > 0 else 0.0
        throughput_chars_per_sec = text_chars / mean_s if mean_s > 0 else 0.0
        throughput_sents_per_sec = sentence_count / mean_s if mean_s > 0 else 0.0

        if baseline_mean_s is None and "pragmatic-sbd (clean=False)" in name:
            baseline_mean_s = mean_s

        speedup = (baseline_mean_s / mean_s) if (baseline_mean_s and mean_s > 0) else 1.0

        results.append(
            EngineResult(
                name=name,
                available=True,
                status_message="OK",
                sentence_count=sentence_count,
                iterations=iterations,
                min_ms=min_s * 1000.0,
                mean_ms=mean_s * 1000.0,
                median_ms=median_s * 1000.0,
                std_dev_ms=std_dev_s * 1000.0,
                throughput_mb_s=throughput_mb_s,
                throughput_chars_per_sec=throughput_chars_per_sec,
                throughput_sents_per_sec=throughput_sents_per_sec,
                speedup_vs_baseline=speedup,
                raw_times_s=times,
            )
        )
        print("", file=sys.stderr)  # Spacing line between engines

    return results


def print_results_table(text: str, source_msg: str, results: list[EngineResult]) -> None:
    """Format and print a rich console table with benchmark results."""
    text_chars = len(text)
    text_words = len(text.split())
    text_bytes = len(text.encode("utf-8"))
    text_kb = text_bytes / 1024.0

    print("=" * 115)
    print(" PRAGMATIC-SBD SPEED BENCHMARK REPORT")
    print("=" * 115)
    print(f"Source Text : {source_msg}")
    print(
        f"Text Stats  : {text_chars:,} characters | {text_words:,} words | {text_kb:,.1f} KB ({text_bytes:,} bytes)"
    )
    print("-" * 115)
    print(
        f"{'Engine':<32} {'Status':<24} {'Sentences':>10} {'Min (ms)':>10} {'Mean (ms)':>11} {'StdDev':>9} {'Throughput':>12} {'Speedup':>9}"
    )
    print("-" * 115)

    for r in results:
        if not r.available:
            print(
                f"{r.name:<32} {r.status_message:<24} {'-':>10} {'-':>10} {'-':>11} {'-':>9} {'-':>12} {'-':>9}"
            )
            continue

        tp_str = f"{r.throughput_mb_s:>7.2f} MB/s"
        speedup_str = f"{r.speedup_vs_baseline:>8.2f}x"
        print(
            f"{r.name:<32} {'OK':<24} {r.sentence_count:>10,d} {r.min_ms:>10.2f} {r.mean_ms:>11.2f} {r.std_dev_ms:>9.2f} {tp_str:>12} {speedup_str:>9}"
        )

    print("=" * 115)
    print("Note: Speedup is normalized relative to 'pragmatic-sbd (clean=False)' baseline.")
    print(
        "To install comparison libraries: uv run --with nltk,spacy,stanza,blingfire,syntok,pysbd python tests/bigtext_speed_benchmark.py"
    )
    print("=" * 115)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run sentence boundary disambiguation speed benchmarks across various NLP libraries.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        default=DEFAULT_BENCHMARK_PATH,
        help="Path to the input text file for benchmarking.",
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=5,
        help="Number of timed benchmark iterations per engine.",
    )
    parser.add_argument(
        "-w",
        "--warmup",
        type=int,
        default=1,
        help="Number of untimed warmup runs before measuring.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Disable automatic downloading of Gutenberg benchmark text if missing.",
    )
    parser.add_argument(
        "-e",
        "--engines",
        type=str,
        default="",
        help="Comma-separated list of engine substrings to run (e.g. 'pragmatic,spacy').",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON output instead of the formatted table.",
    )
    parser.add_argument(
        "--save-json",
        type=Path,
        default=None,
        help="Save benchmark output metrics to a JSON file.",
    )
    return parser.parse_args()


def main() -> int:
    """Main entrypoint for benchmark execution."""
    args = parse_args()

    file_path = args.file if args.file != DEFAULT_BENCHMARK_PATH or args.file.exists() else None
    text, source_msg = load_benchmark_text(
        file_path=file_path,
        auto_download=not args.no_download,
    )

    selected = [e.strip() for e in args.engines.split(",") if e.strip()] if args.engines else None

    results = run_benchmark(
        text=text,
        iterations=args.iterations,
        warmup=args.warmup,
        selected_engines=selected,
    )

    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        print_results_table(text, source_msg, results)

    if args.save_json:
        args.save_json.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source_info": source_msg,
            "text_length_chars": len(text),
            "text_length_bytes": len(text.encode("utf-8")),
            "iterations": args.iterations,
            "warmup": args.warmup,
            "results": [asdict(r) for r in results],
        }
        args.save_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Benchmark results saved to: {args.save_json.resolve()}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
