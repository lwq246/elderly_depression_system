# Facility screening SOP — Australia (en-AU)
Locale: en-AU

Operational policy for staff after AI-assisted wellbeing screening in residential aged care (RACF). **Configure** contact names, times, escalation trees, and care-record field names for your site before production use.

<!-- pathway: reference | retrievable: true -->
## Scope and use

- Applies to screening room sessions triggered by UWB band entry (resident identified by band, not spoken ID).
- AI output is **screening support only** — registered nurses, ENs, and clinicians decide all care.
- Use this SOP to map analyst `recommendation` levels and safety flags to **facility actions**, not as a diagnosis.
- Covers post-session staff response only. Companion conversation behaviour is governed separately.
- Aligns with the Aged Care Quality Standards (person-centred care, dignity, risk management) — this SOP does not replace your facility’s clinical governance or mental health emergency plan.
- This document is indexed for **analyst policy retrieval at session exit** — staff should still follow local clinical judgment when the AI output and the resident’s presentation do not align.

<!-- pathway: reference | retrievable: true -->
## Staff roles and responsibilities

| Role | Responsibility |
|------|----------------|
| **AI companion (in room)** | Greet resident, lead wellbeing check-in, end when UWB exit detected — no clinical decisions |
| **Duty nurse / shift coordinator** | Receives alerts for `visit_soon` and above; assigns follow-up within timeframes below |
| **Registered nurse (RN) in charge** | Reviews passive and active safety escalations; approves handover and GP / mental health referrals |
| **Care staff on floor** | Observes resident after session if distress visible; does not leave alone when SOP requires presence |
| **Nurse dashboard reviewer** | Reads analyst JSON, verifies evidence quotes against transcript, documents actions in care record |
| **Facility manager / clinical lead** | Reviews monthly QA samples, override patterns, and repeated validation failures |

Staff must not wait for the analyst report before acting on **visible imminent risk** in the room — follow active safety escalation immediately.

**Delegation:** ENs and care workers may conduct assigned `check_in` visits per facility protocol; passive and active safety pathways require **RN oversight** unless your state delegation framework explicitly permits otherwise.

<!-- pathway: reference | retrievable: true -->
## Before and during screening

**Eligibility:** Resident is generally able to participate in a brief voice conversation. If they are acutely unwell, asleep, in acute distress, or mid-procedure, defer screening and note reason in care record.

**Consent and dignity:** Screening is voluntary. If the resident declines to continue, stop the session (UWB exit or staff override). Document refusal — no mandatory analyst follow-up unless staff observe safety concern independently.

**Cognitive impairment:** A resident with dementia or fluctuating capacity may give inconsistent answers. Treat analyst output as one data point; corroborate with staff observation, family, and care plan history.

**Distress during session:** If the resident becomes visibly upset or discloses imminent risk during conversation, staff enter the room and follow active safety escalation — do not rely on the session completing normally.

**Language:** Companion uses plain English. If the resident needs an interpreter, use your facility’s usual language-access pathway; note limitation on analyst evidence in handover.

**Hearing and speech:** If the resident cannot hear the speaker clearly or STT fails repeatedly, offer a staff-led check-in instead of forcing the AI session. Document accommodation in the care record.

**Room environment:** Screening room should be quiet, private, and familiar. Reduce competing noise from TVs or corridor traffic where possible — poor audio affects transcript quality and analyst confidence.

<!-- pathway: reference | retrievable: true -->
## Analyst output reference (staff mapping)

Use the nurse dashboard JSON together with this SOP. Key fields:

| Field | Staff use |
|-------|-----------|
| `recommendation` | Primary driver for follow-up timeframe (`none` → `urgent`) |
| `passive_suicidal_thoughts` | Triggers passive safety pathway when true |
| `active_suicidal_ideation` | Triggers active safety pathway; expect `urgent` |
| `suicide_risk_flag` | Summary safety flag — review even if recommendation seems low |
| `transcript_topics[].concern` | Domain-level screening signals with verbatim `evidence` |
| `estimate_confidence` | Low confidence = incomplete screening; nurse may schedule informal follow-up |
| `explanation` | Nurse-facing summary — screening language only, not diagnosis |

**Screen-positive pattern:** Five or more domains with `concern: true` and resident evidence → minimum **`visit_soon`**, even without safety flags.

**Validation errors on report:** Treat affected domains as **unverified**. RN reviews transcript manually before clinical action. Do not dismiss safety concerns solely because the JSON failed validation.

<!-- pathway: routine | retrievable: true -->
## Routine follow-up actions

| Analyst `recommendation` | Facility action | Target timeframe |
|--------------------------|-----------------|------------------|
| `none` | No mandatory follow-up; note in routine handover if useful | Next shift handover |
| `check_in` | Assigned nurse brief wellbeing check (in person or per your protocol) | Within **48 hours** |
| `visit_soon` | Nurse visit; document mood, safety, and supports in care record | Within **24 hours** |
| `urgent` | Immediate nurse presence; escalate per active safety SOP below | **Immediate** |

Screen-positive pattern (5+ concern domains with evidence): treat as minimum **`visit_soon`** even if passive safety only.

**Edge cases:**

- **`check_in` + `passive_suicidal_ideation: true`** → follow passive safety escalation; do not treat as routine check-in only.
- **`none` but staff disagree** → nurse clinical judgment prevails; document override and reason.
- **Several domains `discussed: false`** → analyst may under-call concern; nurse may schedule informal check-in if clinical picture warrants.
- **Low `estimate_confidence`** → short or vague session; prefer nurse re-engagement over assuming `none` means well.
- **Companion safety handoff occurred** → treat as minimum **`visit_soon`** until RN reviews, even if analyst recommendation is lower.

<!-- pathway: domain_follow_up | retrievable: true -->
## Domain-led follow-up (non-crisis)

When `recommendation` is `check_in` or `visit_soon` without safety flags, use domain evidence to guide the nurse conversation:

| Domain signal (examples) | Nurse focus | Document |
|--------------------------|-------------|----------|
| Mood / spirits low | Open-ended mood check; what helps on better days | Quote + observation |
| Sleep poor | Sleep hygiene, pain, toileting, medication review trigger | Sleep pattern notes |
| Appetite low | Weight trend, oral intake, dental issues, GP if sustained | Food/fluid chart reference |
| Social withdrawal | Visitors, activities, loneliness, bereavement | Social care plan update |
| Energy / fatigue | Medical review triggers, activity pacing, depression screen by GP if indicated | Referral if persistent |
| Worries / outlook | Practical worries (family, finances, health); chaplain or SW if appropriate | Non-diagnostic summary |

These are **prompts for nurse conversation**, not automatic diagnoses or referrals.

<!-- pathway: passive_safety | retrievable: true -->
## Passive safety escalation

**Triggers:** passive suicidal thoughts (e.g. wish not to wake, better off dead, feeling a burden) **without** current plan, intent, or means. Analyst flag: `passive_suicidal_thoughts: true`.

| Step | Action |
|------|--------|
| 1 | Duty nurse notified within **15 minutes** of session end |
| 2 | Do not leave resident alone if distress is visible |
| 3 | Registered nurse in charge review **same shift** |
| 4 | Document verbatim resident quotes in care system |
| 5 | GP or mental health nurse follow-up per RACF pathway within **24 hours** |
| 6 | Consider increased observation per facility risk plan until review completed |
| 7 | Review medications and access to means per facility policy (see Medication and means safety) |

Minimum analyst mapping: `recommendation` **`visit_soon`** or higher.

**Plan denial:** If resident reported passive thoughts but **denied plan or intent** (e.g. “No plan. I will not do that.”), passive pathway may still apply — active escalation is not automatic. RN confirms current risk in person.

**Not passive safety:** clear denial of current thoughts (e.g. “No, I do not wish to hurt myself”) with no other risk indicators — document and follow routine pathway unless staff observe otherwise.

**Past vs current:** Thoughts described as historical only, with clear denial of current intent → document; RN judgment on whether passive flag in analyst output reflects residual risk.

<!-- pathway: active_safety | retrievable: true -->
## Active safety escalation

**Triggers:** current intent, plan, means, or imminent risk (pills, overdose, hurt/kill self, etc.). Analyst flag: `active_suicidal_ideation: true` → `recommendation` **`urgent`**.

| Step | Action |
|------|--------|
| 1 | **Stop AI screening** — staff take over in room immediately |
| 2 | Notify RN in charge and senior clinician **now** — do not delay for analyst JSON |
| 3 | Do not leave resident alone |
| 4 | Call **000** if imminent danger to life |
| 5 | Follow facility mental health emergency protocol; preserve means if safe to do so |
| 6 | Document actions and quotes within **1 hour** |
| 7 | Notify GP and next of kin per facility policy and resident preferences |
| 8 | Complete incident report per facility requirements if self-harm attempt or near-miss |

Minimum analyst mapping: `recommendation` **`urgent`**.

**Means access:** References to pills in drawer, stockpiling medication, or “taking too many” with self-harm context → active pathway even if resident minimises intent. Do not reframe as sleep medication without explicit resident clarification documented by RN.

**Companion handoff:** If the AI companion stated that a care team member will speak with the resident soon, staff must **honour that** — enter room promptly; do not resume AI screening.

<!-- pathway: active_safety | retrievable: true -->
## Medication and means safety

Applies when transcript or analyst report mentions medication access, overdose thoughts, or stockpiled tablets.

| Situation | Action |
|-----------|--------|
| Pills accessible in room | RN review; secure or supervise per risk plan |
| PRN sedatives or opioids | Medication review with GP or pharmacist if self-harm concern |
| Recent medication change | Note in handover; correlate with mood/sleep changes |
| No imminent risk but means mentioned | Document; consider means restriction as part of care plan review |

Staff do not remove medications without RN/medical direction and resident rights review.

<!-- pathway: reference | retrievable: true -->
## CALD, language, and cultural safety

Many RACF residents speak languages other than English at home.

| Situation | Facility action |
|-----------|-----------------|
| Resident struggled with AI English session | Offer TIS **131 450** or accredited interpreter for nurse follow-up |
| Cultural idioms in transcript (e.g. “heart heavy”, “crook”) | Use analyst evidence quotes; ask resident to explain in their words |
| Family as interpreter | Avoid for safety-sensitive disclosures; use professional interpreter where feasible |
| Shame or stigma around mental health | RN uses non-stigmatising language; do not label resident “depressed” in chart without clinical assessment |

Document language used and whether interpreter was offered or declined.

<!-- pathway: reference | retrievable: true -->
## Cognitive impairment and fluctuating capacity

| Presentation | Guidance |
|--------------|----------|
| Inconsistent answers across domains | Weight staff observation over single AI session |
| Unable to understand safety questions | Defer formal screening; document capacity note |
| Known dementia diagnosis | Screening is optional signal; align with behavioural observation charts |
| Resident agrees but confabulates | Verify concerns with care team before escalation |

Analyst `discussed: false` on many domains is common — does not mean resident is well.

<!-- pathway: domain_follow_up | retrievable: true -->
## Bereavement, loss, and end-of-life context

| Signal | Guidance |
|--------|----------|
| Recent death of spouse or friend | Validate grief; distinguish from depression via RN assessment — not AI |
| Palliative care resident | Screening may be inappropriate; follow individual care plan |
| “Wish not to wake” with terminal illness | Urgent RN review; may be distress or treatment burden — not automatic psychiatric pathway |
| Anniversary or birthday low mood | `check_in` may suffice; document psychosocial support offered |

Do not dismiss passive language solely because resident is elderly or unwell — context determines pathway.

<!-- pathway: domain_follow_up | retrievable: true -->
## Men's mental health and stoicism

Australian older men often minimise mood concerns (“I’m fine”, “she’ll be right”).

- Nurse follow-up may need **somatic entry** (sleep, pain, energy) before mood.
- Single-session `none` with low confidence does not rule out concern.
- Consider GP review if somatic complaints persist without clear medical cause.

<!-- pathway: domain_follow_up | retrievable: true -->
## Sleep and rest concerns

Poor sleep is one of the most common domain signals and is often the easiest entry point for a reluctant resident.

| Signal in transcript | Nurse focus | Escalate if |
|----------------------|-------------|-------------|
| Wakes repeatedly, early-morning waking | Pain, toileting, noise, caffeine, nocturia | Sustained 2+ weeks or paired with low mood |
| Cannot get to sleep, racing thoughts | Anxiety, worry, recent change or loss | Paired with passive safety language |
| Sleeping most of the day | Withdrawal, boredom, sedation, low mood | Marked change from baseline |
| Nightmares or distress on waking | Grief, trauma, medication side-effect | Distress persists after reassurance |

- Review PRN sedative use and timing with the RN before assuming a sleep-hygiene fix.
- Offer non-drug options first (routine, daytime light and activity, reduced evening noise) per care plan.
- Document the baseline sleep pattern so change over time is visible at the next screening.

<!-- pathway: domain_follow_up | retrievable: true -->
## Pain and physical comfort

Untreated pain frequently presents as low mood, irritability, or withdrawal in older residents — especially those who cannot easily self-report.

| Presentation | Nurse focus | Document |
|--------------|-------------|----------|
| “Everything aches”, reluctance to move | Site, pattern, and impact on activity and sleep | Pain score + observation |
| Guarding, grimacing, resisting care | Non-verbal pain in cognitive impairment | Behaviour chart reference |
| Mood lifts when comfortable | Correlate pain relief with mood | Note for care plan |

- Use an appropriate pain tool (e.g. Abbey Pain Scale for residents with dementia) per facility policy.
- Flag new or worsening pain for GP or nurse practitioner review; do not attribute pain to ageing alone.
- Poorly controlled pain with passive safety language is a **compound concern** — raise both with the RN.

<!-- pathway: domain_follow_up | retrievable: true -->
## Appetite, nutrition, and hydration

| Signal | Nurse focus | Action |
|--------|-------------|--------|
| Skipping meals, “not hungry” | Mood, dentition, taste change, medication | Food/fluid chart; weight trend |
| Unintentional weight loss | Dysphagia, illness, low mood | GP review; dietitian referral if sustained |
| Refusing fluids | Confusion, UTI, low mood, end-of-life context | Hydration plan; RN review |
| Eats only with company | Loneliness, environment | Social dining, mealtime support |

- Sustained appetite change across two or more screenings warrants GP and dietitian review.
- Distinguish reduced appetite from **active food refusal**, which may signal distress or a wish to withdraw — escalate the latter to the RN.

<!-- pathway: domain_follow_up | retrievable: true -->
## Social connection and loneliness

Loneliness is a strong driver of low mood in residential aged care and is often understated by stoic residents.

| Signal | Nurse focus | Support options |
|--------|-------------|-----------------|
| Few or no visitors | Family contact, transport barriers, estrangement | Volunteer visitor, video calls |
| Declines group activities | Hearing, mobility, English, interest fit | One-to-one before group; interest-matched activity |
| Recent loss of a friend on-site | Grief, changed routine | Peer support, chaplaincy |
| “Nobody would notice” language | **Screen for passive safety** — may be more than loneliness | RN review same shift |

- Link findings to the lifestyle and activities team and to the individualised care plan.
- Watch for loneliness language that shades into passive safety (“burden”, “no point”) — route to the passive safety pathway if present.

<!-- pathway: domain_follow_up | retrievable: true -->
## Anxiety, worry, and agitation

| Presentation | Nurse focus | Escalate if |
|--------------|-------------|-------------|
| Persistent worry about family, health, or money | Practical problem-solving; reassurance | Interfering with sleep or eating |
| Restlessness, pacing, calling out | Unmet need (pain, toileting, boredom, fear) | Risk to self or others |
| Panic-like episodes | Triggers, breathing, medical causes | Recurrent or severe |
| Repetitive questioning (dementia) | Orientation, routine, environment | Escalating distress |

- Rule out medical and environmental causes before assuming a psychological cause.
- Persistent anxiety with functional impact warrants GP review; do not start or change medication on an AI signal.

<!-- pathway: domain_follow_up | retrievable: true -->
## Dementia and behavioural support

Behavioural and psychological symptoms of dementia (BPSD) can mimic or mask depression signals in screening.

| Presentation | Nurse focus | Support |
|--------------|-------------|---------|
| Apathy, withdrawal | Distinguish from low mood; check baseline | Meaningful activity, life-history cues |
| Agitation late in the day | Sundowning triggers, environment | Routine, lighting, reduced stimulation |
| Distress you cannot settle | Unmet need, pain, delirium | RN review; medical assessment |

- Use a non-pharmacological approach first, guided by the resident’s behaviour support plan.
- For complex BPSD, consider Dementia Support Australia **1800 699 799**.
- Do not record AI-generated mental-health labels in the dementia care plan — use observed behaviour and RN assessment.

<!-- pathway: domain_follow_up | retrievable: true -->
## Alcohol and other substance use

Applies when the transcript mentions drinking, “a few too many”, or relying on tablets to cope. This is a **wellbeing** concern; suspected self-harm via medication follows the active safety and medication/means pathways instead.

| Signal | Nurse focus | Action |
|--------|-------------|--------|
| Regular alcohol use affecting mood or falls | Quantity, interactions with medication | GP review; document |
| “Only thing that helps me cope” | Underlying mood, sleep, or pain concern | Domain follow-up + GP |
| Requests for extra sedatives | Dependence, pain, anxiety | Medication review with RN/GP |

- Approach non-judgementally; residents retain the right to make choices about legal substances within a shared risk framework.
- Where use is linked to self-harm intent, escalate via **Active safety escalation** and **Medication and means safety**.

<!-- pathway: reference | retrievable: true -->
## Family and next of kin

- **Default:** Do not contact family solely on the basis of AI screening output without RN review.
- **`check_in` / `visit_soon`:** Involve family only if clinically appropriate and consistent with resident wishes and care plan.
- **`urgent` or active safety:** Follow facility emergency notification policy; respect advance care directives and nominated contacts.
- Document who was contacted, when, and what was shared (factual, non-diagnostic language).

**Burden on family:** Common worry in older residents — note in handover; social work referral if persistent and affecting mood.

<!-- pathway: domain_follow_up | retrievable: true -->
## GP and mental health referral pathways

| Trigger | Typical action |
|---------|----------------|
| `visit_soon`, passive safety resolved at review | GP notification within 24–48h per facility protocol |
| Persistent low mood / functional decline | GP review; consider geriatric psychiatry or PMHC referral |
| Active safety post-crisis | Emergency department or community mental health per local pathway |
| Medication-related mood change | GP or pharmacist review |

Document referral made, declined, or deferred — and reason.

<!-- pathway: routine | retrievable: true -->
## After-hours and weekends

| `recommendation` | After-hours action |
|------------------|-------------------|
| `none` / `check_in` | Log for next shift; `check_in` still due within **48 hours** from session end |
| `visit_soon` | On-call RN or nurse-in-charge contacts resident or ensures welfare check before next routine round |
| `urgent` / active safety | Immediate on-call RN and senior clinician; **000** if imminent risk — same as business hours |

Replace on-call names and numbers with your facility roster.

<!-- pathway: active_safety | retrievable: true -->
## Crisis contacts (staff reference)

**Do not read aloud to residents** unless your facility SOP explicitly requires it during handoff.

| Service | Contact | When |
|---------|---------|------|
| Emergency | **000** | Imminent danger |
| Lifeline | **13 11 14** (24h) | Staff reference / support options |
| Beyond Blue | **1300 22 4636** | Staff reference |
| Suicide Call Back Service | **1300 659 467** | Staff reference for follow-up planning |
| TIS National (interpreters) | **131 450** | Staff arrange for CALD follow-up |

Replace with your facility’s approved contact list, RACF escalation tree, GP after-hours line, and on-call roster.

<!-- pathway: reference | retrievable: true -->
## Screening room technology (UWB and audio)

| Issue | Action |
|-------|--------|
| UWB exit not detected | Staff manual session end in dashboard; document technical fault |
| Wrong resident on band | Stop session; verify identity; incident log if data crossed |
| Poor STT / resident not heard | Retry once; then offer staff-led check-in |
| Speaker too loud or startling | Adjust volume; note resident distress in record |

Technology failures do not delay **visible** safety response in the room.

<!-- pathway: reference | retrievable: true -->
## Documentation and handoff

- Log screening session ID, resident ID, end time, and analyst `recommendation` in the care record.
- Attach **verbatim resident evidence quotes** from the nurse dashboard — not AI paraphrase.
- Handover note must state: **screening only, not a diagnosis**.
- Record safety flags (`passive_suicidal_thoughts`, `active_suicidal_ideation`) and which SOP path was followed.
- If validation errors appear on the report, flag for **human review** before clinical decisions — treat domains with missing or unverified evidence as unconfirmed.
- Retain records per your facility retention schedule and the Privacy Act 1988 (Cth) / Australian Privacy Principles for personal information.
- Note whether RAG-retrieved policy sections were used for reference — clinical action remains nurse-led.

**Handover template (minimum):** session date/time · recommendation · safety flags · domains with concern · actions taken · next review time · who notified.

<!-- pathway: reference | retrievable: true -->
## Re-screening and monitoring

| Situation | Guidance |
|-----------|----------|
| Prior `visit_soon` or safety escalation | Next routine UWB screening is not a substitute for scheduled nurse follow-up — complete assigned visit first |
| Resident stable after `check_in` | No fixed re-screen interval; follow care plan and nurse judgment |
| Repeated `check_in` or `visit_soon` within 14 days | RN review for care plan update; consider GP or mental health referral |
| Resident refused screening | Do not force; note refusal; RN may offer staff-led check-in within 7 days if appropriate |
| Improvement after intervention | Continue care plan; routine screening may resume on normal UWB schedule |

<!-- pathway: reference | retrievable: true -->
## Privacy and information sharing

- Screening transcripts and analyst reports contain sensitive health information — access on need-to-know basis only.
- Do not share full transcripts in open ward areas or non-secure messaging.
- External disclosure (GP, hospital, family) follows resident consent, substitute decision-maker rules, and your facility privacy policy.
- De-identified aggregate data for quality improvement is permitted per local governance — no resident names in routine audit exports.
- Residents may request access to their information per APP 12 — route to privacy officer.

<!-- pathway: reference | retrievable: true -->
## Staff training and competency

| Topic | Frequency |
|-------|-----------|
| Reading analyst dashboard and evidence quotes | At onboarding + annual refresh |
| Passive vs active safety pathways | Annual mandatory |
| CALD and interpreter use | Annual |
| Manual session override and UWB faults | On deployment + as needed |
| This SOP and local escalation tree | Annual sign-off |

New staff must not review safety escalations unsupervised until competency signed off by RN educator or clinical lead.

<!-- pathway: reference | retrievable: true -->
## Staff wellbeing and debrief

Supporting residents in distress affects staff.

- After **active safety** events: offer debrief with RN in charge or EAP per facility policy.
- Document critical incidents; do not rely on AI transcript alone for staff incident reports.
- Rotate screening room coverage if staff report vicarious distress.

<!-- pathway: reference | retrievable: true -->
## Complaints and resident rights

- Residents may refuse AI screening without affecting other care — document only.
- Complaints about the companion or screening process → facility complaints officer; preserve session ID for review.
- Charter of Aged Care Rights applies — dignity, choice, and quality care in all pathways above.

<!-- pathway: reference | retrievable: true -->
## Quality assurance

- Monthly sample: nurse reviewer checks that `urgent` and safety cases had documented actions within SOP timeframes.
- Track overrides where staff escalated above analyst `recommendation` — feed back to clinical governance, not as a system fault.
- Report repeated validation failures or missing evidence to the person responsible for screening room operations.
- Quarterly review: false-negative near-misses (staff escalated despite low AI recommendation).
- Annual review: update crisis contacts, on-call roster, and GP pathways in this document.

<!-- pathway: reference | retrievable: true -->
## Elder abuse and safeguarding concerns

Screening may surface signs of abuse, neglect, or exploitation. These follow your facility safeguarding policy — they are **not** part of the suicide-risk pathways above.

| Concern | Examples | Action |
|---------|----------|--------|
| Physical / neglect | Unexplained injury, poor hygiene, fear of a person | RN and facility safeguarding lead same shift |
| Financial | Missing money, pressure over will or accounts | Escalate to manager; do not confront the alleged party |
| Emotional | Intimidation, isolation by another person | Document verbatim; protect the resident |

- Serious Incident Response Scheme (SIRS) reportable incidents must be notified per legislation and facility policy.
- Support contacts: Older Persons Advocacy Network (OPAN) **1800 700 600**; national elder abuse line **1800 353 374**.
- Never promise secrecy about a safeguarding disclosure; explain who needs to know and why.

<!-- pathway: reference | retrievable: true -->
## Consent, capacity, and substitute decision-making

- Screening participation is voluntary; a resident may stop at any time without affecting other care.
- Capacity is decision-specific and may fluctuate — a person may consent to a chat but not to a care change.
- Where a resident lacks capacity for a relevant decision, involve the **enduring guardian, attorney, or person responsible** per your state framework and the resident’s advance care directive.
- Document the basis for any decision made on the resident’s behalf, and the least-restrictive option considered.
- An AI screening result never overrides a valid advance care directive or a documented refusal of treatment.

<!-- pathway: reference | retrievable: true -->
## Transitions: admission, hospital transfer, and respite

Mood and safety risk often shift around transitions.

| Transition | Watch for | Action |
|------------|-----------|--------|
| New admission (first 4–6 weeks) | Adjustment distress, disorientation, homesickness | Increase informal check-ins; settle-in plan |
| Return from hospital | Delirium, pain, medication changes, low mood | RN review; reconcile medications |
| Respite / short stay | Limited baseline, unfamiliar environment | Corroborate AI signal with family and referrer |
| Room or wing change | Loss of familiar staff and peers | Anticipate and support |

- Treat a low or safety-flagged screening during a transition as **at least `visit_soon`** until the RN reviews the context.

<!-- pathway: reference | retrievable: true -->
## Integration with care plans

- Update individualised care plan when repeated domain concerns appear (sleep, social, mood).
- Link screening outcomes to existing behavioural support plans for dementia residents where relevant.
- Do not enter AI-generated labels (e.g. “depression”) into care plan problem list — use observable terms and RN assessment.
