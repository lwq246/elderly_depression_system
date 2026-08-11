"""en-SG culture-core vocabulary for companion mirror-first context.

Locale-specific terms only — generic English depression wording is handled by the LLM.
Not stored in Chroma. See culture-en-SG/reference.md for research sources.
"""

from __future__ import annotations

VOCABULARY_TERMS_EN_SG: list[tuple[list[str], str]] = [
    # Singlish / local mood
    (["sian", "very sian", "sian sian", "sian liao"], "low mood"),
    (["no mood", "mood very low", "mood not good", "no mood at all"], "low mood"),
    (["heart pain", "heart very heavy", "heart ache", "heart very pain"], "sadness"),
    (["heart very sore", "heart feel heavy"], "sadness"),
    (["boh hua", "feel boh hua"], "low mood"),
    (["buay ho", "buay ho siah"], "unwell"),
    (["sim kua", "sim beh ho"], "anxiety"),
    (["not like myself", "i'm not like myself"], "low mood"),
    (["old and useless", "useless already", "old already useless"], "worthlessness"),
    # Hokkien / Malay overwhelm
    (["buay tahan", "cannot tahan", "buay tahan already", "really cannot tahan"], "overwhelmed"),
    (["tak boleh tahan", "tak tahan"], "overwhelmed"),
    (["cannot cope already"], "overwhelmed"),
    (["too much already"], "overwhelmed"),
    # Local fatigue phrasing
    (["no strength", "no strength at all"], "fatigue"),
    (["tired until cannot"], "fatigue"),
    (["body very heavy"], "fatigue"),
    (["letih", "rasa letih"], "fatigue"),
    (["lemah", "badan lemah"], "fatigue"),
    # Local sleep phrasing
    (["cannot sleep", "sleep very poor", "cannot sleep also", "cannot sleep well"], "insomnia"),
    (["sleep very little"], "insomnia"),
    (["susah tidur", "tidur susah"], "insomnia"),
    # Local appetite phrasing
    (["no appetite at all"], "low appetite"),
    (["food no taste", "food tasteless"], "low appetite"),
    (["jiak buay liao", "eat buay liao"], "low appetite"),
    (["hilang selera", "tiada selera makan"], "low appetite"),
    # SG somatic (ward English + Malay)
    (["giddy", "very giddy", "feel giddy"], "dizzy"),
    (["pening", "rasa pening"], "dizzy"),
    (["breathless", "feel breathless"], "short of breath"),
    (["panting", "keep panting"], "short of breath"),
    (["sakit", "very sakit", "rasa sakit"], "pain"),
    (["head very pain"], "pain"),
    (["sakit kepala", "kepala sakit"], "pain"),
    (["sakit perut"], "pain"),
    (["chest very tight"], "pain"),
    (["sesak nafas", "susah bernafas"], "short of breath"),
    # TCM / Malay bodily
    (["heaty", "heatiness", "very heaty", "body heaty"], "unwell"),
    (["wind", "stomach wind", "got wind", "angin"], "bloating"),
    (["loya", "feel loya"], "nausea"),
    (["lao sai", "lau sai", "cirit-birit"], "diarrhea"),
    (["rasa tidak sihat", "tak sihat"], "unwell"),
    # Withdrawal / quiet (local)
    (["diam", "very diam", "diam diam", "keep diam"], "withdrawal"),
    (["hide in room", "stay in room"], "withdrawal"),
    (["children never visit", "nobody visit"], "loneliness"),
    (["empty nest", "children all moved out", "children moved out already"], "loneliness"),
    (["same same every day"], "boredom"),
    # Face / minimising
    (["never mind", "nevermind lah", "okay lah", "still ok"], "minimising"),
    (["can lah", "can manage lah"], "minimising"),
    (["don't worry lah"], "minimising"),
    (["aiya never mind", "bo chap"], "minimising"),
    (["paiseh", "very paiseh", "malu", "feel malu"], "minimising"),
    (["don't tell children", "don't want family know"], "minimising"),
    (["don't want to burden", "don't burden children"], "minimising"),
    (["i am a burden", "burden to children", "burden to family"], "worthlessness"),
    (["pretend ok", "act strong"], "minimising"),
    # Singlish cognitive
    (["very blur", "mind blur"], "cognitive concern"),
    # Help (Malay / local)
    (["tolong", "tolong me", "tolong please", "tolong lah"], "need help"),
]
