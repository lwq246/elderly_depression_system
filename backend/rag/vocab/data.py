"""Culture vocabulary for RAG ingest — one general meaning per culture term.

Source of truth for term → meaning rows. Audit references for en-AU additions:
`.cursor/skills/screening-conversation/culture-en-AU/reference.md` (section Culture vocabulary RAG).
"""

from __future__ import annotations

# locale → list of (variant terms, single general meaning)
VOCABULARY_TERMS: dict[str, list[tuple[list[str], str]]] = {
    "en-SG": [
        (["giddy"], "dizzy"),
        (["breathless", "panting"], "short of breath"),
        (["no strength", "no energy"], "fatigue"),
        (["cannot sleep", "sleep very poor"], "insomnia"),
        (["no appetite", "don't feel like eating"], "low appetite"),
        (["heart pain", "heart very heavy"], "sadness"),
        (["stress", "worried", "tension"], "anxiety"),
        (["sian"], "low mood"),
        (["buay tahan"], "overwhelmed"),
        (["heaty", "heatiness"], "unwell"),
        (["wind"], "bloating"),
        (["sakit"], "pain"),
        (["tolong"], "need help"),
    ],
    "en-AU": [
        (["been going", "how you going"], "how are you"),
        (["crook", "crook as a dog"], "unwell"),
        (["flat", "a bit flat"], "low mood"),
        (["down in the dumps"], "low mood"),
        (["bit blue", "feeling blue"], "low mood"),
        (["not myself", "don't feel myself"], "low mood"),
        (["black dog"], "low mood"),
        (["out of sorts"], "unwell"),
        (["run down"], "fatigue"),
        (["knackered", "worn out", "buggered", "rooted", "stuffed"], "exhausted"),
        (["off your food", "gone off my food"], "low appetite"),
        (["not sleeping", "crappy sleep"], "poor sleep"),
        (["aches and pains", "everything hurts"], "pain"),
        (["a bit quiet", "keeping to yourself"], "withdrawal"),
        (["nothing to do", "bored stiff"], "boredom"),
        (["can't be bothered"], "low energy"),
        (["overwhelmed", "stressed out"], "overwhelmed"),
        (["doing it tough", "tough time"], "struggling"),
        (["hard yakka"], "struggling"),
        (["lonely", "a bit lonely"], "loneliness"),
        (["don't get lonely"], "minimising"),
        (["she'll be right"], "minimising"),
        (["dusty"], "irritable"),
        (["ropeable"], "angry"),
    ],
}


def vocabulary_locales() -> list[str]:
    return list(VOCABULARY_TERMS.keys())
