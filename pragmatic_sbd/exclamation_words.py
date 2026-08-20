# pysbd/lang/common.py
import re

from pragmatic_sbd.lang.common.standard import PUA_EXCLAMATION

EXCLAMATION_WORDS = (
    "ǃʼOǃKung",
    "!Kung-Ekoka",
    "!Xuun",
    "ǃKhung",
    "ǃXung",
    "!Kung",
    "!Xun",
    "!Xũ",
    "ǃXû",
    "ǃXo",
    "ǃKu",
    "ǃHu",
    "ǃung",
    "Yahoo!",
    "Yum!",
    "Y!J",
)

# Sorted by length descending to match compound words before prefixes
EXCLAMATION_WORDS_REGEX = re.compile(
    "|".join(re.escape(w) for w in sorted(EXCLAMATION_WORDS, key=len, reverse=True))
)


def mask_exclamation_words(text: str) -> str:
    """Mask exclamation marks within known proper nouns and click consonants."""
    return EXCLAMATION_WORDS_REGEX.sub(
        lambda m: m.group(0).replace("!", PUA_EXCLAMATION).replace("ǃ", PUA_EXCLAMATION),
        text,
    )
