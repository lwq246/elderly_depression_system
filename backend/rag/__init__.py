"""RAG: Chroma index for facility policy (analyst).

Layout:
  query.py, embeddings.py, store.py — shared infrastructure
  policy/  — facility SOP ingest + analyst retrieval
  ingest.py, inspect_index.py — CLI entry points

Local culture vocabulary is not retrieved via RAG — it is inlined into the companion and
analyst prompts directly from culture-*/local-vocabulary.md (see backend/app/skills.py).
"""
