# Elderly depression screening — full stack

Web app that simulates the UWB screening flow:

1. **uwb.entry** — start session, companion greeting (skills + culture)
2. **voice.turn** — resident STT text → companion reply
3. **uwb.exit** — close session → **analyst** JSON + validation

## Architecture

```
frontend (Next.js)  →  FastAPI backend  →  OpenAI / OpenRouter (optional)
                           ↓
                    SQLite sessions
                           ↓
              .cursor/skills/*.md (loaded at runtime)
```

**Anti-hallucination:** `validate_analyst()` checks JSON schema, evidence ⊆ resident transcript, and safety rules.

## Quick start

### 1. Backend

```powershell
cd C:\Users\leewe\Documents\CursorDepression
copy .env.example .env
# Set OPENAI_API_KEY in .env (OpenRouter key works — see .env.example)

C:\Python314\python.exe -m pip install -r backend\requirements.txt
C:\Python314\python.exe -m uvicorn backend.app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 2. Frontend

```powershell
cd C:\Users\leewe\Documents\CursorDepression\frontend
npm install
npm run dev
```

Open http://localhost:3000

Optional: set `BACKEND_URL` in `frontend/.env.local` if the API is not on `http://127.0.0.1:8000`.

**Windows note:** If you see `Application Control policy has blocked` for `@next/swc-win32-x64-msvc`, that is expected on locked-down PCs. This project sets `experimental.useWasmBinary` in `next.config.ts` so Next.js uses the WASM compiler instead. The warning may still print; wait for `Ready` (first start can take ~30–60s). If port 3000 is busy, Next uses 3001 automatically.

**ENOENT on `.next/server/app/page.js`:** Stop every `npm run dev` process (Ctrl+C in each terminal), then from `frontend/` run `npm run dev:clean` (or delete `.next` manually and `npm run dev`). This happens when the dev server keeps running while `.next` is deleted or partially rebuilt.

## LLM configuration

`OPENAI_API_KEY` is **required**. Without it, companion and analyst requests fail.

**OpenRouter (GPT-4o mini):** In `.env`, set `OPENAI_API_KEY` to your [OpenRouter key](https://openrouter.ai/keys), `OPENAI_BASE_URL=https://openrouter.ai/api/v1`, and `OPENAI_MODEL=openai/gpt-4o-mini`. Restart the backend; `/api/health` should show `llm_configured: true` and the model name.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health + LLM mode |
| GET | `/api/residents` | Test residents (R-001 … R-999) |
| POST | `/api/sessions/entry` | `uwb.entry` |
| POST | `/api/sessions/{id}/message` | Resident turn |
| POST | `/api/sessions/{id}/exit` | `uwb.exit` + analyst |
| GET | `/api/sessions/{id}` | Session + report |
| GET | `/api/sessions` | List for nurse dashboard |

## Test residents

| ID | Persona |
|----|---------|
| R-001 | Mrs Tan — cooperative |
| R-002 | Mr Lim — minimiser |
| R-003 | Mrs Chen — passive safety |
| R-005 | Mr Raj — active safety |
| R-006 | Mr Koh — short replies |
| R-999 | No name lookup |

## Project layout

```
backend/app/     FastAPI, DB, skills loader, validator, LLM
frontend/app/       Next.js App Router pages + globals.css
frontend/components/  Client UI (ScreeningConsole)
frontend/lib/       API client + types
.cursor/skills/  Conversation + analyst skills (source of truth)
data/            SQLite + RAG Chroma index (created at runtime)
```

## RAG (analyst only — optional)

**Domain criteria:** loaded directly into the analyst system prompt from `reference.md` (always — no RAG).

**RAG (optional):** facility operational SOP from `.cursor/skills/facility-policy/` (`en-SG.md`, `en-AU.md`). Retrieved by session locale at analyst time when `RAG_ENABLED=true`.

```powershell
# 1. Install deps (includes chromadb)
C:\Python314\python.exe -m pip install -r backend\requirements.txt

# 2. Build vector index (uses OpenRouter embeddings)
C:\Python314\python.exe C:\Users\leewe\Documents\CursorDepression\backend\rag\ingest.py --reset

# 3. Enable in .env
# RAG_ENABLED=true

# 4. Restart backend — check health
# {"rag_enabled": true, "rag_chunks": 12, ...}

# Inspect indexed chunks (metadata + text preview)
C:\Python314\python.exe C:\Users\leewe\Documents\CursorDepression\backend\rag\inspect_index.py
C:\Python314\python.exe C:\Users\leewe\Documents\CursorDepression\backend\rag\inspect_index.py --full
C:\Python314\python.exe C:\Users\leewe\Documents\CursorDepression\backend\rag\inspect_index.py --section "Severity guide"
```

**Do not index transcripts** (PHI). Companion calls do not use RAG.

## Edge voice (local STT + TTS on ThinkPad / Pi)

Mic → **whisper.cpp** (`ggml-tiny.en`) → screening API → **Piper** TTS → speaker. Audio stays in RAM; only text hits the cloud.

```powershell
C:\Python314\python.exe -m pip install -r edge\requirements.txt
C:\Python314\python.exe edge\download_models.py
C:\Python314\python.exe edge\run_voice_room.py --resident R-001 --locale en-SG
```

See [edge/README.md](edge/README.md) for full setup.

## Next steps

- Wire UWB hardware events
- Add auth for nurse dashboard
- Expand `validate_analyst()` unit tests from your 10 chat scenarios
