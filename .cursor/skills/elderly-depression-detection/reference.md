# Domain reference (team audit)

GDS-inspired domains rephrased for natural care-center dialogue. Not administered as a formal questionnaire.

## Domain criteria

### mood_spirits — Mood & spirits

| State | Criteria |
|-------|----------|
| Concern | Low mood, not in good spirits, unhappy most of the time, morning worse than afternoon (diurnal pattern) |
| No concern | Generally positive or mixed but functional mood |
| Not discussed | Spirits or mood never addressed |

**Listen for:** "not myself", "down in the dumps", "putting on a brave face"

---

### interest_activities — Interest & activities

| State | Criteria |
|-------|----------|
| Concern | Lost interest in hobbies, lounge activities, reading, garden; boredom; emptiness; stopped attending events they used to enjoy |
| No concern | Engages with activities, looks forward to things |
| Not discussed | Activities or interests never addressed |

**Late-life note:** Withdrawal and anhedonia often appear before explicit sadness.

---

### energy — Energy

| State | Criteria |
|-------|----------|
| Concern | Low energy, tiring easily, everything feels like effort |
| No concern | Adequate energy for daily routines |
| Not discussed | Energy never addressed |

**Listen for:** "everything is an effort", "can't be bothered"

---

### meals_appetite — Meals & appetite

| State | Criteria |
|-------|----------|
| Concern | Eating less, no interest in food, skipping meals, weight loss mentioned |
| No concern | Normal appetite, enjoys meals or dining room |
| Not discussed | Meals or appetite never addressed |

---

### sleep_rest — Sleep & rest

| State | Criteria |
|-------|----------|
| Concern | Poor sleep, restless nights, waking early, difficulty falling asleep |
| No concern | Sleeps reasonably well |
| Not discussed | Sleep never addressed |

---

### social_connection — People & connection

| State | Criteria |
|-------|----------|
| Concern | Loneliness, few visitors, prefers staying in room, withdrawal from others |
| No concern | Regular contact with family, friends, or residents |
| Not discussed | Social contact never addressed |

---

### emotional_weight — Worries & outlook

| State | Criteria |
|-------|----------|
| Concern | Hopelessness, helplessness, worthlessness, feeling a burden, excessive worry, not satisfied with life |
| No concern | Generally accepts life situation; manageable worries |
| Not discussed | Outlook or worries never addressed |

**Listen for:** "what's the point", "they'd be better off without me" (also check safety)

---

### safety_check — Safety check

| State | Criteria |
|-------|----------|
| Concern | Thoughts of not wanting to live, wishing they weren't here, self-harm thoughts (current or unclear timing) |
| No concern | Denies such thoughts, or past-only with clear denial of current thoughts |
| Not discussed | Safety never addressed |

**Denial examples (no concern):** "No", "Nothing like that", "I do not wish to hurt myself", "No safety thoughts", "No plan."

**Escalation:** Any current intent, plan, or means → `active_suicidal_ideation: true`, `recommendation: urgent`

---

### coping_strengths — What helps

| State | Criteria |
|-------|----------|
| Concern | No coping strategies; nothing helps; complete inability to find comfort |
| No concern | Identifies people, activities, faith, routines, or memories that help |
| Not discussed | Coping never addressed |

Default `concern: false` unless absence of supports is itself concerning.

---

## Indicator domains

Use `indicators` to summarise cross-cutting signals for staff dashboards:

| Domain | Examples |
|--------|----------|
| `emotional` | Low mood, hopelessness, irritability, tearfulness |
| `behavioural` | Withdrawal, stopped activities, social isolation |
| `physical` | Fatigue, appetite change, sleep disturbance, psychomotor slowing |
| `elderly_specific` | Feeling a burden, fear of being a nuisance, grief, adjustment to care home |

### Severity guide

| Level | Meaning |
|-------|---------|
| `none` | Not present or explicitly denied |
| `mild` | Mentioned briefly, minimal functional impact described |
| `moderate` | Clear difficulty, affects daily life |
| `notable` | Prominent, persistent, or multiple related statements |

---

## Screening thresholds (for implementers)

These rules belong in application code, not in the analyst prompt:

| Signal | Suggested level |
|--------|-----------------|
| Active ideation or `suicide_risk_flag` | Elevated / urgent |
| 5+ concern domains | Screen positive → elevated |
| 3–4 concern domains | Moderate |
| 0–2 concern domains | Low |
| Passive thoughts only | Visit soon minimum |

Adjust thresholds after nurse pilot feedback.

---

## Sources and attribution

Domain themes and screening concepts in this skill are **distilled in original wording** for staff-facing transcript analysis. They are **not** a reproduction of copyrighted toolkits or a validated automated GDS score.

### Primary instrument (public domain)

| Source | URL | How we use it |
|--------|-----|----------------|
| **Geriatric Depression Scale (GDS)** — Yesavage et al., Stanford | https://stanford.edu/~yesavage/GDS.html | **Domain structure only** (mood, interest, energy, appetite, sleep, social withdrawal, hopelessness, etc.). Questions and labels are **rephrased** for natural dialogue — the GDS is **not** administered or scored as a formal test in this product. |

### Research supporting analyst rules

| Source | URL | How we use it |
|--------|-----|----------------|
| Recognizing depression in the elderly (PMC review) | https://pmc.ncbi.nlm.nih.gov/articles/PMC9741828/ | Stigma-aware screening language; somatic presentation; "low/down" vs diagnostic labels in staff summaries |
| Depression in older adults (BJMP) | https://www.bjmp.org/content/depression-older-adults | Masked/somatic depression; under-reporting; withdrawal and anhedonia in late life |
| Somatic symptoms as barrier to detection (PMC) | https://pmc.ncbi.nlm.nih.gov/articles/PMC2805563/ | Map fatigue, sleep, appetite cues to relevant domains even when mood is not named |
| Engaging older men in depression care (PMC) | https://pmc.ncbi.nlm.nih.gov/articles/PMC2981127/ | Indirect disclosure; interpret minimisation and somatic-only quotes in transcripts |
| Barriers to depression screening in older adults (Gerontology) | https://doi.org/10.1093/geroni/igy023.1890 | Conservative evidence rules; trust and conversational (non-questionnaire) context |
| Help-seeking barriers — systematic review (PMC) | https://pmc.ncbi.nlm.nih.gov/articles/PMC10463345/ | Stigma; residents may under-report — `discussed: false` vs false certainty |
| Murray PHN — Enhancing Mental Health in Residential Aged Care | https://murrayphn.org.au/wp-content/uploads/2025/07/Enhancing-Mental-Health-In-Residential-Aged-Care-A-Practice-Guide-For-Clinicians.pdf | Screening measures as conversation prompts (not diagnosis); risk items including suicidal ideation |
| RASA — Mental Health in RACF Toolkit | https://www.rasa.org.au/wp-content/uploads/2023/11/Mental-Health-RACF-Toolkit_RASA_Final.pdf | Safety escalation; staff handoff when distress or suicidal thoughts appear |
| ARIIA — Screening tools in residential aged care (AU) | https://www.ariia.org.au/knowledge-implementation-hub/mental-health-and-wellbeing/mental-health-and-wellbeing-evidence-themes/screening-tools | GDS-12R for cognitive impairment; CSDD for dementia; referral not diagnosis |
| Suicidal ideation in LTC — assessment guide (2024) | https://nursinghomebehavioralhealth.org/wp-content/uploads/2024/09/WEBSITE_Assessment-and-Initial-Management-of-Suicidal-Ideation-Across-Long-Term-Care-Settings_FINAL_10.15.24_508.pdf | Passive vs active ideation; three plain-language probes |
| AI conversational screening — rural older adults (BMC Geriatrics) | https://link.springer.com/article/10.1186/s12877-026-07038-0 | Transcript cue patterns; AI limitations — conservative evidence rules |
| Paykel Suicide Scale validation in NH (2025) | https://doi.org/10.1080/13607863.2025.2545357 | Brief passive ideation screening in institutions |
| Singapore NH depression prevalence study | https://doi.org/10.1080/13607863.2013.775638 | Pain, social contact, length of stay as contextual factors |

### Original product design (not from URLs)

| Element | Origin |
|---------|--------|
| JSON schema (`transcript_topics`, `indicators`, `recommendation`) | Internal skill design for nurse workflow |
| `estimate_confidence` = topic coverage (not severity) | Internal design choice |
| Screen-positive threshold (5+ concern domains) | Internal rule — calibrate with nurse pilot |
| Passive vs active suicidal ideation flags | Standard clinical screening convention |
| UWB session → transcript → analyst pipeline | Project scenario (see `screening-conversation/reference.md`) |

### Attribution and use notice

- **Internal use:** This reference is for compliance, clinical advisors, and engineering audit — not read aloud to residents.
- **Principles, not copies:** Skill text summarises published guidance; it does not embed PDF or article text.
- **Screening only:** Output is **screening support for staff review**, not a medical diagnosis or substitute for qualified clinical judgment.
- **Not a validated instrument:** This analyst skill is **not** the GDS, PHQ-9, or any licensed scale. Do not market outputs as equivalent to those tools without regulatory and psychometric validation.
- **Open-access papers:** Where articles use CC BY or similar licenses, retain attribution when distributing this reference document.

For resident-facing communication sources, see [../screening-conversation/communication-guide.md](../screening-conversation/communication-guide.md).

