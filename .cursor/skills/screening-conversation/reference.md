# Session integration reference

For developers wiring UWB, speaker, STT, and analyst pipeline.

## Session context (passed to conversation skill)

```json
{
  "event": "uwb.entry",
  "resident_id": "R-1042",
  "resident": {
    "preferred_name": "Mrs Tan",
    "locale": "en-SG"
  },
  "facility": {
    "country": "SG",
    "default_locale": "en-SG",
    "speech_register": "standard"
  },
  "room_id": "screening-01"
}
```

- **`resident_id`** — from UWB band mapping; never sent to TTS
- **`preferred_name`** — from resident registry lookup; use in greeting
- If lookup fails, omit `preferred_name` and use generic greeting from culture `greeting.txt`

## Prompt assembly (conversation)

```text
system = screening-conversation/SKILL.md
       + culture-{locale}/SKILL.md

first_tts = culture-{locale}/greeting.txt  (with preferred_name inserted)
```

Supported locales: `en-SG`, `en-AU`. See culture folders under `screening-conversation/`.

### speech_register

| Value | Meaning |
|-------|---------|
| `standard` | Clear English; mirror resident local words only |
| `local-light` | Companion may use a few familiar local words per turn (see `local-vocabulary.md`) |

## Event flow

| Order | Event | System action |
|-------|-------|---------------|
| 1 | `uwb.entry` | Map band → `resident_id`; load profile; start session; TTS greeting |
| 2 | `voice.turn` (repeat) | STT → LLM (screening-conversation) → TTS to room speaker |
| 3 | `uwb.exit` | Same `resident_id` left room; TTS brief close if needed; `session.end` |
| 4 | `session.end` | Persist transcript; run elderly-depression-detection analyst |

## Hardware assumptions

- **Input:** Room microphone + STT
- **Output:** Room speaker + TTS (no display required)
- **Presence:** UWB anchors detect band enter/exit at door threshold

## Exit edge cases

| Case | Behaviour |
|------|-----------|
| Exit during TTS playback | Finish current phrase or truncate gracefully; no new questions |
| Exit before permission granted | Silent end; log short session |
| Safety handoff mid-session | Staff take over; stop AI TTS; analyst still runs on partial transcript |
| Re-entry same day | New session; do not assume prior conversation context unless product requires it |

## Analyst handoff payload

```json
{
  "session_id": "uuid",
  "resident_id": "R-1042",
  "started_at": "ISO-8601",
  "ended_at": "ISO-8601",
  "end_reason": "uwb.exit",
  "transcript": [
    { "role": "assistant", "text": "..." },
    { "role": "resident", "text": "..." }
  ]
}
```

Pass `transcript` to **elderly-depression-detection** skill for nurse JSON output.
