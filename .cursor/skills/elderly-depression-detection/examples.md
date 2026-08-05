# Gold examples (runtime — condensed)

Use for analyst prompt tuning. Full set archived in project history; keep verbatim-quote and safety patterns.

---

## Example 1 — Moderate concern (minimiser + somatic)

**Transcript (excerpt):**

> **Resident:** I'm fine. … I stay in my room mostly. … Can't be bothered now. … I wake at 3am and can't get back. … Not hungry much. … No [safety thoughts].

**Expected:** `interest_activities`, `sleep_rest`, `social_connection`, `meals_appetite` concerns with verbatim quotes; `confidence` medium; `recommendation` `check_in` or `visit_soon`; note minimisation in explanation.

---

## Example 2 — Safety denial (happy path)

**Transcript (excerpt):**

> **Resident:** Spirits okay. … Sleep is fine. … I still join bingo sometimes. … **No, I do not wish to hurt myself.**

**Expected:** `safety_check` discussed, concern **false**; `active_suicidal_ideation` **false** (denial — phrase contains "hurt myself" but resident negated); all safety flags false; `recommendation` `none` or `check_in`.

---

## Example 3 — Passive thought + plan denial

**Transcript (excerpt):**

> **Resident:** Quite low. … Sleep is poor. … **Sometimes I wish I did not wake up.** … **No plan. I will not do that.**

**Expected:** `passive_suicidal_thoughts` **true**; `active_suicidal_ideation` **false** (plan denial); `recommendation` **`visit_soon`** minimum; passive quote in evidence.

---

## Example 4 — Means access + overdose thoughts

**Transcript (excerpt):**

> **Resident:** I have pills in the drawer. … Sometimes I think about taking too many.

**Expected:** `safety_check` concern; `suicide_risk_flag` **true**; `recommendation` **`visit_soon`** or **`urgent`**; do **not** reframe as sleep medication unless resident clearly says so.
