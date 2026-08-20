import re
import time
from pathlib import Path

URL_EMAIL_KEYWORDS = (".com", ".net", ".org", ".io", ".gov", ".edu", "http://", "https://", "@", "www.")

NO_SPACE_SENTENCE_ALPHA = re.compile(r"(?<=[a-z])\.(?=[A-Z])")
NO_SPACE_SENTENCE_DIGIT = re.compile(r"(?<=\d)\.(?=[A-Z])")
NO_SPACE_SENTENCE_COMBINED = re.compile(r"(?<=[a-z\d])\.(?=[A-Z])")


def current_impl(text: str) -> str:
    if "." not in text:
        return text
    words = text.split(" ")
    cleaned_words: list[str] = []
    for word in words:
        if "." not in word:
            cleaned_words.append(word)
            continue
        word_lower = word.lower()
        if any(k in word_lower for k in URL_EMAIL_KEYWORDS):
            cleaned_words.append(word)
            continue
        w = NO_SPACE_SENTENCE_ALPHA.sub(". ", word)
        w = NO_SPACE_SENTENCE_DIGIT.sub(". ", w)
        cleaned_words.append(w)
    return " ".join(cleaned_words)


def optimized_impl(text: str) -> str:
    if "." not in text:
        return text

    def replace_no_space_sentence(match: re.Match[str]) -> str:
        start = match.start()
        text_str = match.string

        # Find boundaries of the word containing the match
        word_start = start
        while word_start > 0 and text_str[word_start - 1] not in " \n\r\t":
            word_start -= 1

        word_end = start + 1
        text_len = len(text_str)
        while word_end < text_len and text_str[word_end] not in " \n\r\t":
            word_end += 1

        word = text_str[word_start:word_end].lower()
        if any(k in word for k in URL_EMAIL_KEYWORDS):
            return match.group(0)
        return ". "

    return NO_SPACE_SENTENCE_COMBINED.sub(replace_no_space_sentence, text)


def main():
    res1: str = ""
    res2: str = ""
    path = Path("benchmarks/pg100.txt")
    if not path.exists():
        print("Benchmark file not found.")
        return
    text = path.read_text(encoding="utf-8")

    # Warmup
    _ = current_impl(text)
    _ = optimized_impl(text)

    # Benchmark current
    t0 = time.perf_counter()
    for _ in range(5):
        res1 = current_impl(text)
    t1 = time.perf_counter()
    time_current = (t1 - t0) * 1000
    print(f"Current implementation time: {time_current:.2f} ms")

    # Benchmark optimized
    t2 = time.perf_counter()
    for _ in range(5):
        res2 = optimized_impl(text)
    t3 = time.perf_counter()
    time_opt = (t3 - t2) * 1000
    print(f"Optimized implementation time: {time_opt:.2f} ms")

    print(f"Speedup: {time_current / time_opt:.2f}x")
    assert res1 == res2, "Outputs do not match!"


if __name__ == "__main__":
    main()
