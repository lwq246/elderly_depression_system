"""en-AU culture-core vocabulary for companion mirror-first context.

Locale-specific terms only — generic English depression wording is handled by the LLM.
Not stored in Chroma. See culture-en-AU/reference.md for research sources.
"""

from __future__ import annotations

VOCABULARY_TERMS_EN_AU: list[tuple[list[str], str]] = [
    # Check-in (Aus.)
    (["been going", "how you going", "how ya going"], "how are you"),
    # Low mood (Aus. idiom)
    (["flat", "a bit flat", "feeling flat"], "low mood"),
    (["down in the dumps"], "low mood"),
    (["bit blue", "feeling blue", "a bit blue"], "low mood"),
    (["black dog"], "low mood"),
    # Unwell / fatigue (Aus. slang)
    (["crook", "crook as a dog", "feel crook", "a bit crook"], "unwell"),
    (["out of sorts", "feel out of sorts"], "unwell"),
    (["under the weather"], "unwell"),
    (["knackered", "buggered", "rooted", "stuffed"], "exhausted"),
    (["can't be bothered", "cannot be bothered"], "low energy"),
    (["flat out"], "busy"),
    # Sleep / appetite (Aus. phrasing)
    (["not sleeping", "crappy sleep", "poor sleep"], "poor sleep"),
    (["off your food", "gone off my food"], "low appetite"),
    # Withdrawal (RAC phrasing)
    (["keeping to yourself", "keep to yourself"], "withdrawal"),
    (["a bit quiet", "very quiet", "become quiet"], "withdrawal"),
    # Struggling / stoicism
    (["doing it tough", "tough time", "going through a tough time"], "struggling"),
    (["hard yakka", "doing it hard"], "struggling"),
    (["not coping", "not coping on my own", "can't cope on my own"], "struggling"),
    (["she'll be right", "she will be right"], "minimising"),
    (["don't get lonely"], "minimising"),
    (["don't make a fuss", "not making a fuss"], "minimising"),
    (["getting on with it", "get on with it", "just get on with it"], "minimising"),
    (["soldier on", "just soldier on"], "minimising"),
    (["i'm fine", "yeah fine"], "minimising"),
    # Irritability (Aus. colloquial)
    (["dusty", "feeling dusty"], "irritable"),
    (["ropeable", "feel ropeable"], "angry"),
    (["cranky", "feel cranky"], "irritable"),
    # Cognitive (Aus.)
    (["brain fog", "mind foggy"], "cognitive concern"),
    # Help (Aus.)
    (["need a hand", "could use a hand"], "need help"),
]
