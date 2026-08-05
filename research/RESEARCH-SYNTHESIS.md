# Research Synthesis — Screening Conversation & Elderly Depression Detection

**Completed:** 30 rounds (2026-07-31)  
**Purpose:** Evidence base for skill development — screening support only, not diagnosis.

---

## Executive summary

Conversational AI voice check-ins are feasible for elderly wellbeing monitoring and can reduce PHQ-9/GDS scores in pilots, but must supplement (not replace) clinical care. The strongest skill improvements are: **indirect/somatic entry**, **OARS every turn**, **voice-first TTS design**, **three-step safety ladder**, **conservative analyst evidence rules**, and **locale-specific stigma/face-saving adaptations**.

---

## 1. Conversational AI & voice screening

| Finding | Implication for skills |
|---------|------------------------|
| AI call services (e.g. Clova CareCall) linked call patterns to GDS-SF depression risk in 2,896 Korean elders (BMC Geriatrics 2026) | Detection analyst should treat **coverage + conversational cues** as signals, not questionnaire scores |
| 4-feature speech model achieved 92% sensitivity in assisted-living contexts (Frontiers Digital Health 2025) | Future acoustic features possible; current skills stay **transcript/quote-based** |
| Welzijn.AI uses EQ-5D-5L domains + language biomarkers with stakeholder co-design (arXiv 2025) | Domain map aligns with our 9 topics; reinforce **gradual conversation flow** |
| Voice care pilots show PHQ-9 reductions over 6 months (JMIR Aging 2025) | Frame sessions as **routine friendly check-ins**, not tests |
| iShe LLM voice companion: 100% retention, GDS-15 reduction (JMIR preprint) | Short daily sessions work; keep **one question per turn** |

**Sources:** [BMC Geriatrics AI call study](https://link.springer.com/article/10.1186/s12877-026-07038-0), [Frontiers speech model](https://www.frontiersin.org/journals/digital-health/articles/10.3389/fdgth.2025.1675103/full), [Welzijn.AI](https://arxiv.org/html/2502.07983), [JMIR Aging voice care](https://aging.jmir.org/2025/1/e76653)

---

## 2. Motivational interviewing (OARS)

| Finding | Implication |
|---------|-------------|
| OARS (Open questions, Affirmations, Reflections, Summaries) validated for elder care behaviour change (U Arizona MI guide) | **Every reply:** reflect → optional affirm → one open question |
| MI increases advance directive completion 79% in seniors (Supportive Care review) | Affirm autonomy; accept "not now" |
| MI reduces depression symptoms in chronic pain elders (Chang et al. 2015) | Validation without fixing is evidence-based |
| Conversational (not clinical) language elicits more honest screening answers (Gerontology 2018) | Avoid PHQ jargon aloud |

---

## 3. Masked / somatic depression

| Finding | Implication |
|---------|-------------|
| Older adults describe distress somatically; physicians attribute to ageing (PMC9741828) | **Never dismiss** fatigue/sleep/appetite as "just ageing" |
| Loss of interest/withdrawal often > explicit sadness in late life | Weight `interest_activities` and `social_connection` heavily |
| GDS de-emphasises somatic items; PHQ-9 somatic items confound with medical illness | Our conversational domains intentionally use **daily-life language** |
| NH depression prevalence up to 54% undetected (UK feasibility study) | Analyst: conservative flags, note minimisation |

---

## 4. Screening instruments (mapping, not administering)

| Tool | Use in product |
|------|----------------|
| **GDS-15** | Domain inspiration; yes/no spirit; cut-off ≥5 → formal assessment |
| **GDS-12R** | Residential/cognitive impairment variant — inform `discussed: false` when resident cannot answer |
| **PHQ-2** | Two conversational probes: low mood + anhedonia ("not quite yourself" / lost interest) |
| **Whooley questions** | Bedside-friendly; less distressing than full GDS in acute settings |
| **CSDD** | Dementia settings need informant data — voice-only room may have **lower coverage** for severe dementia |
| **Paykel Scale** | Brief passive ideation screen validated in NH (2025) |

**Product rule:** Skills **do not** score GDS/PHQ. Analyst maps quotes to domains.

---

## 5. Suicide screening in LTC

| Step | Plain-language probe |
|------|---------------------|
| 1 | "Better off dead" / wish not to be here → passive vs active |
| 2 | Thoughts of hurting themselves |
| 3 | If past only: **"How about now — past couple of weeks?"** |

- Passive ideation common in LTC; still requires monitoring (NH behavioral health guide 2024)
- PHQ-9 item 9 triggers further assessment; C-SSRS for stratification in clinical settings
- Prevalence of suicidal thoughts in LTC: 5–33% past month (systematic review)

---

## 6. Stigma & help-seeking

- Stigma is top barrier; "seen as weak" OR=0.25 for service use (BMC Geriatrics 2023 review)
- Frame as **wellbeing / daily life / spirits**, not mental health test
- Trusted relationship + conversational language = best facilitators (Gerontology qualitative study)
- Older men: double stigma; somatic-only disclosure; avoid "depression" label early (PMC2981127, UC Davis IMPACT)

---

## 7. Voice / TTS design for elders

| Practice | Evidence |
|----------|----------|
| Short sentences, one idea each | CMU GetGoing senior dialog system |
| Attention prefix before key info ("The next thing…") | Improves comprehension/retention |
| Slower pace via pauses (SSML breaks 300–1000ms) | Wolters et al.; TTS best practices |
| Offer repeat: "Ask me to say that again" | Reduces speaker anxiety |
| No markdown/visual refs in spoken output | Already in skill — keep |

---

## 8. Singapore (en-SG)

- NH depression prevalence **21.1%** (Singapore NH study); risk factors: long stay, pain, lack of social contact
- Multicultural norms: face-saving, family involvement, indirect disclosure
- Outreach: G-RACE, APCATS for geriatric psychiatry

---

## 9. Australia (en-AU)

- ARIIA: GDS-15, GDS-12R, CSDD, GAI for anxiety; tools for **referral**, not diagnosis
- CSDD in ACFI since 2008; 23% probable depression in Sydney NH audit
- CALD elders: language loss, stigma, crisis-before-help; Aged Care Diversity Framework
- "Cup of tea and a chat" preferred mental healthcare framing (HSC qualitative study)
- FIRST study: 20% depression risk in RACS; pain, sleepiness, frailty associated

---

## 10. Loneliness & social connection

- Loneliness 56–95.5% in LTC reviews; compounds depression risk
- `social_connection` domain critical; probe visitors, calls, lounge participation
- Social prescription / facilitated contact as follow-up (not in conversation skill)

---

## 11. Ethical AI

| Principle | Implementation |
|-----------|----------------|
| Autonomy & voluntary use | Permission at session start; accept no |
| Privacy | No credentials in logs; transcript handoff to staff only |
| Non-diagnostic | Both skills: screening support only |
| Co-design | Locale culture skills; stakeholder values (Welzijn.AI) |
| Limited human-likeness | Warm companion, not faux clinician |
| Revocable consent / safe storage | Product implementer requirement |

Sources: MESA-Bot co-design (ACM 2025), Welzijn.AI, Frontiers social robots ethics 2025.

---

## 12. Recommended skill updates (applied)

1. **communication-guide.md** — Add AI/voice screening sources, TTS pacing, older-men indirect entry, PHQ-2 conversational mapping
2. **elderly-depression-detection/reference.md** — Add ARIIA, CSDD, Paykel, AI screening sources
3. **screening-conversation/SKILL.md** — Note ethical consent; reinforce Whooley-style two-probe entry
4. **culture-en-AU** — CALD plain-English default reinforced
5. **culture-en-SG** — Family/face-saving probe patterns

---

## Round index

| Round | Topic | Log |
|-------|-------|-----|
| 1–30 | See `research/rounds/round-NN.md` | Automated via `scripts/research/run_research_round.py` |

---

## Scheduler

- **Task name:** `CursorDepression-SkillResearch`
- **Interval:** Every 30 minutes — **one round per tick**
- **Total:** 30 rounds (~15 hours from round 1)
- **Script:** `scripts/research/run_research_round.ps1` (calls Python without `--all`)
- **Stops after:** Round 30 (`research/state.json`); scheduler continues but script no-ops

**Note:** Earlier batch run (all 30 at once) was archived to `research/rounds-batch-2026-07-31/`. Scheduled run is the active pipeline.
