# Australia culture skill — sources and attribution

Principles distilled for **en-AU** speech adaptation. Not a reproduction of source documents. For compliance audit — not sent to residents.

## How online research shaped this skill

| Research theme | Applied in `SKILL.md` as |
|----------------|--------------------------|
| CALD residents — language diversity | Simple English; concrete daily-life words; reflect mixed-language speech |
| Later-life migration / loss of identity | Loneliness when family interstate/overseas; gentle family probes |
| Linguistic isolation in RAC | Confirm understanding; do not assume idioms land equally |
| Stoicism / "she'll be right" | One gentle probe after minimisation; somatic entry (sleep, appetite) |
| Older men's presentation | Boredom, irritability, physical complaints before mood words |
| Rural stoicism & help-seeking | Warm steady tone; activity-based life references (garden, morning tea) |
| Royal Commission CALD dementia care | Cultural connection matters; communication impacts wellbeing |
| RACGP Silver Book multicultural care | Curiosity, sensitive enquiry, active listening; interpreters for complex care |

## References

| Source | URL | Relevance |
|--------|-----|-----------|
| NSW TMHC — Older people & mental health in multicultural communities | https://www.nsw.gov.au/departments-and-agencies/transcultural-mental-health-centre/research-planning-evidence/community-population-mental-health-profiles/older-people-and-mental-health-multicultural-communities | CALD older people; loneliness; isolation; depression resources |
| Who speaks my language? — RAC linguistic diversity (2024) | https://www.culturaldiversity.com.au/files/Australas-J-Ageing-2024-O-Dwyer-Who-speaks-my-language-Linguistic-diversity-among-people-living-in-Australian.pdf | Lone speakers of LOTE; person-centred communication planning |
| Dementia care CALD — Royal Commission analysis (ECU) | https://ro.ecu.edu.au/cgi/viewcontent.cgi?article=4072&context=ecuworks2022-2026 | Language support; cultural connection; food/music |
| RACGP Silver Book — Multiculturalism in aged care | https://www.racgp.org.au/clinical-resources/clinical-guidelines/key-racgp-guidelines/view-all-racgp-guidelines/silver-book/silver-book-part-b/multiculturalism-in-aged-care | Cross-cultural communication; depression in CALD; active listening |
| Stoicism & help-seeking rural Australia (RRH) | https://www.rrh.org.au/journal/article/5399/ | "Getting on with it"; avoid emotional talk — indirect probing |
| Rural older Australians mental health lived experience (2025) | https://www.tandfonline.com/doi/full/10.1080/13607863.2025.2529269 | Stigma; visibility in communities; help-seeking vs privacy |
| Social participation & loneliness rural AU (IJERPH) | https://www.mdpi.com/1660-4601/21/7/886 | Stoicism disconnect; "don't get lonely" but high loneliness scores |
| Older men masculinity & suicide 80+ (Am J Men's Health) | https://journals.sagepub.com/doi/10.1177/1557988320966540 | Strong silent types; control; activity framing; safety relevance |
| Engaging older men in depression care (PMC) | https://pmc.ncbi.nlm.nih.gov/articles/PMC2981127/ | Indirect approach; somatic symptoms; avoid word "depression" |

### Local vocabulary sources

| Source | URL | Relevance |
|--------|-----|-----------|
| Cultural Diversity in Ageing — Communication practice guide | https://www.culturaldiversity.com.au/files/Communication.pdf | Plain English; avoid colloquialism for CALD |
| Multicultural NSW Playbook — plain English | https://playbook.multicultural.nsw.gov.au/chapters/creative-and-translations/ | No puns/colloquialism; reading age 9 |
| My Aged Care — CALD support | https://www.myagedcare.gov.au/support-cald-people | Culturally appropriate communication rights |
| healthdirect — Depression in older people | https://www.healthdirect.gov.au/depression-in-older-people | Somatic presentation; stigma; "not coping" |
| NSW Health — Wellbeing in Later Life | https://www.health.nsw.gov.au/mentalhealth/resources/Publications/wellbeing-in-later-life.pdf | Beyond Blue; older adult mental health programs |
| AIHW — CALD older Australians | https://www.aihw.gov.au/reports/older-people/older-australians/contents/population-groups-of-interest/culturally-linguistically-diverse-people | Language diversity in RAC; plain English priority |
| ANU ANDC — crook | https://slll.cass.anu.edu.au/centres/andc/meanings-origins/c | Crook = unwell / bad; cuppa in older AU everyday speech |
| ANU ANDC — yakka / hard yakka | https://slll.cass.anu.edu.au/centres/andc/meanings-origins/y | Hard yakka = strenuous work / effort |
| ANU ANDC — no worries | https://slll.cass.anu.edu.au/centres/andc/meanings-origins/n | Minimising / “all fine” assurance |
| Macquarie Word Map — crook as Rookwood | https://www.macquariedictionary.com.au/resources/aus/word/map/search/word/crook/New%20South%20Wales/ | Older-speaker “very unwell”; CALD-unsafe to introduce |
| PalliAGED — Mental illness in practice | https://www.palliaged.com.au/Improving-Care/Complex-Needs/Mental-Illness | Mood/withdrawal cues in aged care |
| healthdirect — Depression (general symptoms) | https://www.healthdirect.gov.au/depression | Sad, low, isolated, sleep/appetite, irritability |

Canonical term list (runtime): `backend/rag/vocab/data.py` → Chroma collection `screening-culture-vocabulary`.

## Culture vocabulary RAG (en-AU)

Distilled for companion per-turn retrieval. One general meaning per row. **Not** sent verbatim to residents — injected when a resident uses a matching term.

| Term group (examples) | General meaning | Primary sources |
|-----------------------|-----------------|-----------------|
| crook, crook as a dog, crook as Rookwood | unwell | ANDC; Macquarie Word Map |
| under the weather, off colour, lurgy | mildly unwell | Everyday Aus.; healthdirect somatic entry |
| flat, a bit down, a bit blue, not myself, black dog, down in the dumps | low mood | healthdirect; Beyond Blue / Black Dog Institute public language |
| not coping | struggling (often instead of “depressed”) | healthdirect older depression |
| knackered, worn out, buggered, stuffed, run down, shattered | exhausted / fatigue | Informal Aus. fatigue terms; healthdirect somatic cues |
| off your food, gone off my food, not eating | low appetite | RAC daily-life phrasing; healthdirect |
| not sleeping, crappy sleep, tossing and turning | poor sleep | healthdirect somatic depression |
| aches and pains, bung knee, dicky ticker | pain / body worry | healthdirect older depression presentation |
| keeping to yourself, a bit quiet, not going out | withdrawal | PalliAGED; healthdirect “not leaving the house” |
| nothing to do, bored stiff, can't be bothered | boredom / low energy / withdrawal | RAC boredom/loneliness literature |
| lonely, a bit lonely, rattling around, missing the kids | loneliness | AIHW CALD; IJERPH rural loneliness |
| she'll be right, she'll be apples, no worries, don't get lonely | minimising | ANDC; RRH stoicism; IJERPH |
| doing it tough, tough time, hard yakka, had a gutful | struggling | ANDC yakka; everyday Aus. hardship phrasing |
| cranky, snappy, on edge, a bit nervy | irritable / anxious | healthdirect irritability; older men's presentation |
| been going, how you going | how are you | Standard Aus. wellbeing opener |

**Excluded deliberately:** `flat out` (busy, not low mood), `gone off` alone (spoiled food), `go crook at` (get angry), `yarn` (conversation, not a symptom), `rooted` / `wog` (too vulgar or ambiguous for AI).

**CALD note:** Mirror colloquial terms only when the resident uses them first; default to plain English ([Communication practice guide](https://www.culturaldiversity.com.au/files/Communication.pdf)).

## Also draws on (shared communication skill)

- RASA Mental Health RACF Toolkit: https://www.rasa.org.au/wp-content/uploads/2023/11/Mental-Health-RACF-Toolkit_RASA_Final.pdf
- Murray PHN Residential Aged Care guide: https://murrayphn.org.au/wp-content/uploads/2025/07/Enhancing-Mental-Health-In-Residential-Aged-Care-A-Practice-Guide-For-Clinicians.pdf

## Attribution notice

- Principles only — no verbatim PDF or article text in `SKILL.md`
- Screening support, not diagnosis
- AI speaker is not a substitute for professional interpreters (TIS 131 450) when resident needs full language support
