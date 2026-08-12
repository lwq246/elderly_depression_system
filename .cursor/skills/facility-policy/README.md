# Facility policy (RAG index)

Operational SOPs indexed into Chroma for the **analyst** at session end.

## Upload workflow (LLM convert → review → ingest)

1. **Convert** raw facility policy (Word/PDF pasted into `.md`, or existing prose):

```powershell
C:\Python314\python.exe C:\Users\leewe\Documents\CursorDepression\backend\rag\convert_policy.py convert `
  --input path\to\raw-policy.md `
  --locale en-AU `
  --site-name "My RACF" `
  --validate
```

Drafts are written to `data/policy_drafts/` by default.

2. **Review** the draft — fix `[CONFIGURE: ...]` placeholders, verify escalation steps and contacts.

3. **Validate** again:

```powershell
C:\Python314\python.exe C:\Users\leewe\Documents\CursorDepression\backend\rag\convert_policy.py validate `
  --input data\policy_drafts\en-AU-....md `
  --locale en-AU
```

4. **Approve** (copies validated draft into this folder):

```powershell
C:\Python314\python.exe C:\Users\leewe\Documents\CursorDepression\backend\rag\convert_policy.py approve `
  --input data\policy_drafts\en-AU-....md `
  --locale en-AU
```

5. **Re-ingest** Chroma:

```powershell
C:\Python314\python.exe C:\Users\leewe\Documents\CursorDepression\backend\rag\ingest.py --reset
```

## Section directives

Each `##` section may include an HTML comment before the heading:

```markdown
<!-- pathway: routine | retrievable: true -->
## Routine follow-up actions
```

| Pathway | Use |
|---------|-----|
| `routine` | Recommendation → facility action timeframes |
| `domain_follow_up` | Non-crisis domain-led nurse prompts |
| `passive_safety` | Passive suicidal thoughts pathway |
| `active_safety` | Active ideation / means / crisis |
| `reference` | Governance prose — set `retrievable: false` to skip RAG |

Reformat a raw policy with `backend/rag/convert_policy.py convert` — a content-preserving pass that adds these directives and is checked for content loss (`check_conversion_coverage`).

## Files

| File | Locale |
|------|--------|
| `en-SG.md` | Singapore facilities (add to `RAG_INDEX_LOCALES` to index) |
| `en-AU.md` | Australian facilities |

Set `RAG_INDEX_LOCALES=en-AU` (default) or `en-AU,en-SG` in `.env` to control which files are embedded.

Clinical domain rubrics stay in the analyst system prompt (`reference.md`). This folder is **facility ops only**.
