# Facility screening SOP — {site_name} ({locale})

Locale: {locale}

Operational policy for staff after AI-assisted wellbeing screening. **Configure** contact names, times, and systems for your site before production use.

<!-- pathway: reference | retrievable: false -->
## Scope and use

- Applies to screening room sessions triggered by UWB band entry.
- AI output is **screening support only** — nurses and clinicians decide care.
- Use this SOP to map analyst `recommendation` levels to **facility actions**, not as a diagnosis.

<!-- pathway: routine | retrievable: true -->
## Routine follow-up actions

| Analyst `recommendation` | Facility action | Target timeframe |
|--------------------------|-----------------|------------------|
| `none` | No mandatory follow-up; note in routine handover if useful | Next shift handover |
| `check_in` | Assigned nurse brief wellbeing check | Within **48 hours** |
| `visit_soon` | Nurse visit; document in care record | Within **24 hours** |
| `urgent` | Immediate nurse presence; escalate per active safety SOP below | **Immediate** |

Screen-positive pattern (5+ concern domains with evidence): treat as minimum **`visit_soon`** even if passive safety only.

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

**Triggers:** passive suicidal thoughts (e.g. wish not to wake, better off dead) **without** current plan, intent, or means.

| Step | Action |
|------|--------|
| 1 | Duty nurse notified within **15 minutes** of session end |
| 2 | Do not leave resident alone if distress is visible |
| 3 | Senior nurse or team leader review **same shift** |
| 4 | Document verbatim resident quotes in care system |
| 5 | Re-screen or clinical review per facility mental health pathway within **24 hours** |

Minimum analyst mapping: `recommendation` **`visit_soon`** or higher.

<!-- pathway: active_safety | retrievable: true -->
## Active safety escalation

**Triggers:** current intent, plan, means, or imminent risk (pills, overdose, hurt/kill self, etc.).

| Step | Action |
|------|--------|
| 1 | **Stop AI screening** — staff take over in room immediately |
| 2 | Notify duty nurse and senior nurse **now** — do not delay for analyst JSON |
| 3 | Do not leave resident alone |
| 4 | Call emergency services if imminent danger to life |
| 5 | Follow facility mental health crisis protocol; preserve means if safe to do so |
| 6 | Document actions and quotes within **1 hour** |

Minimum analyst mapping: `recommendation` **`urgent`**.

<!-- pathway: active_safety | retrievable: true -->
## Crisis contacts (staff reference)

**Do not read aloud to residents** unless your site SOP explicitly requires it during handoff.

| Service | Contact | When |
|---------|---------|------|
| Emergency | **[CONFIGURE: emergency number]** | Imminent danger |
| Mental health crisis line | **[CONFIGURE: crisis line]** | Staff consultation / referral guidance |

Replace with your facility's approved contact list and on-call roster.

<!-- pathway: reference | retrievable: false -->
## Documentation and handoff

- Log screening session ID, resident ID, end time, and analyst `recommendation` in the care record.
- Attach **verbatim resident evidence quotes** from the nurse dashboard — not AI paraphrase.
- Handover note must state: **screening only, not a diagnosis**.
- If validation errors appear on the report, flag for **human review** before clinical decisions.
