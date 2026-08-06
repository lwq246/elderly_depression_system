"""RAG: Chroma index for facility policy (analyst) and culture vocabulary (companion).

Layout:
  query.py, embeddings.py, store.py — shared infrastructure
  policy/  — facility SOP ingest + analyst retrieval
  vocab/   — culture terms ingest + companion retrieval + transcript normalize
  ingest.py, inspect_index.py — CLI entry points
"""
