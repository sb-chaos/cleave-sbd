"""pragmatic_sbd: Python Sentence Boundary Disambiguation."""

<<<<<<< HEAD
from pragmatic_sbd.disambiguator import Disambiguator
from pragmatic_sbd.normalizer import Normalizer
from pragmatic_sbd.segmenter import Segmenter, TextSpan

__all__ = [
    "Disambiguator",
    "Normalizer",
    "Segmenter",
    "TextSpan",
]
=======
from pragmatic_sbd.cleaner import Cleaner
from pragmatic_sbd.processor import Processor
from pragmatic_sbd.segmenter import Segmenter, Text, TextSpan

__all__ = ["Cleaner", "Processor", "Segmenter", "Text", "TextSpan"]
>>>>>>> add-type-annotations
