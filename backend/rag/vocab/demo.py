"""Tiny demo: show what the literal (Aho-Corasick) vocab lane retrieves for a text.

Usage (from repo root):
    C:/Python314/python.exe -m backend.rag.vocab.demo --locale en-AU "Been feeling a bit crook and worn out"
    C:/Python314/python.exe -m backend.rag.vocab.demo --locale en-SG "Very sian lately, cannot sleep"

With no text argument it runs a few built-in examples. Requires the vocab collection to
be ingested (backend/rag/vocab/ingest.py); it reads the real glossary from Chroma.
"""

from __future__ import annotations

import argparse

from backend.rag.vocab.retrieve import _literal_matches

# (locale, text) — mixes en-SG / en-AU and a few edge cases (substring guard, minimiser,
# multiword alias, no-match) so one run shows the range of behaviour.
_DEFAULT_EXAMPLES = [
    ("en-AU", "Been feeling a bit crook and worn out"),
    ("en-AU", "she'll be right, no worries mate"),
    ("en-AU", "just knackered and flat this week"),
    ("en-AU", "an Asian meal with the family"),
    ("en-SG", "Very sian lately, cannot sleep also"),
    ("en-SG", "buay tahan already, so stress"),
    ("en-SG", "my heart very heavy these days"),
    ("en-SG", "no appetite, don't feel like eating"),
    ("en-SG", "feeling heaty and got wind in the stomach"),
    ("en-AU", "everything is lovely, no complaints at all"),
]


def show(locale: str, text: str) -> None:
    terms = _literal_matches(locale, text)
    retrieved = ", ".join(f"{t.canonical} -> {t.meaning}" for t in terms) or "(none)"
    print(f"Text:      {text}")
    print(f"Retrieved: {retrieved}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo the literal vocab retrieval.")
    parser.add_argument("--locale", default="en-AU")
    parser.add_argument("text", nargs="*", help="Text to scan (omit to run built-in examples).")
    args = parser.parse_args()

    if args.text:
        show(args.locale, " ".join(args.text))
    else:
        for locale, text in _DEFAULT_EXAMPLES:
            show(locale, text)


if __name__ == "__main__":
    main()
