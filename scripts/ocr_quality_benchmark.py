#!/usr/bin/env python3
"""Independent OCR quality benchmark. Reads local files only; never uploads content."""
import argparse
import json
import re
import unicodedata
from pathlib import Path


def normalize(value):
    return unicodedata.normalize("NFC", value).replace("\r\n", "\n").strip()


def edit_distance(a, b):
    previous = list(range(len(b) + 1))
    for i, left in enumerate(a, 1):
        current = [i]
        for j, right in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (left != right)))
        previous = current
    return previous[-1]


def benchmark(reference, hypothesis):
    reference = normalize(reference)
    hypothesis = normalize(hypothesis)
    if not reference:
        raise ValueError("Independent reference text is required")
    ref_words = re.findall(r"\S+", reference)
    hyp_words = re.findall(r"\S+", hypothesis)
    return {
        "reference_characters": len(reference),
        "ocr_characters": len(hypothesis),
        "reference_words": len(ref_words),
        "ocr_words": len(hyp_words),
        "character_errors": edit_distance(reference, hypothesis),
        "word_errors": edit_distance(ref_words, hyp_words),
        "cer": round(edit_distance(reference, hypothesis) / len(reference), 6),
        "wer": round(edit_distance(ref_words, hyp_words) / len(ref_words), 6),
        "note": "Requires independently transcribed ground truth. OCR confidence is not accuracy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--ocr", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = benchmark(args.reference.read_text(encoding="utf-8"),
                       args.ocr.read_text(encoding="utf-8"))
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
