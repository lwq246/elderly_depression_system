# Facility policy (RAG index)

Operational SOPs indexed into Chroma for the **analyst** at session end. Edit for your site, then re-ingest:

```powershell
C:\Python314\python.exe C:\Users\leewe\Documents\CursorDepression\backend\rag\ingest.py --reset
```

| File | Locale |
|------|--------|
| `en-SG.md` | Singapore facilities (on disk; add to `RAG_INDEX_LOCALES` to index) |
| `en-AU.md` | Australian facilities |

Set `RAG_INDEX_LOCALES=en-AU` (default) or `en-AU,en-SG` in `.env` to control which files are embedded.

Clinical domain rubrics stay in the analyst system prompt (`reference.md`). This folder is **facility ops only**.
