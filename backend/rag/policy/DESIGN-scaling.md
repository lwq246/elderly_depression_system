# Policy RAG Scaling Design

Target: **many facilities/tenants, multiple locales, thousands+ chunks**, optimized
first for **retrieval quality**.

## Status: implemented

All four phases + the pathway strategy are implemented:
- **Phase 1 (identity):** `doc_id`, `facility_id`, `doc_version`, `doc_type`,
  `parent_id`, `child_index`, `ingested_at` on every chunk; deterministic ids
  (`{doc_id}:{section}:{child_index}`, no `#offset`); `facility_id`/`doc_id` filters
  in `query.py`.
- **Phase 2 (reranker):** `policy/rerank.py` cross-encoder (`bge-reranker-base`),
  gated by `rag_rerank_enabled`, graceful fallback to cosine if unavailable;
  candidate pool → rerank → top_k in `policy/retrieve.py`.
- **Phase 3 (parent/child):** sections split into overlapping child windows for
  embedding; full parent section text returned on any child hit.
- **Phase 4 (incremental ingest):** `ingest.py --doc <doc_id>` delete-then-upsert via
  `store.delete_doc`; full `--reset` still available.
- **Pathway strategy:** directive-sourced pathways (unchanged) + guarantee-include
  safety sections instead of hard exclusion (see §2.6).

## 1. Current state (baseline)

| Area | Today | File |
|------|-------|------|
| Chunking | One chunk per `##` section; embed text capped at 1500 chars | `policy/chunking.py`, `policy/embed_text.py` |
| Metadata | `locale`, `section`, `pathway`, optional `topic_id` | `policy/chunking.py:_base_metadata` |
| Identity | `id = {source}:{section}#{offset}` — no `doc_id`/`facility_id`/`version` in metadata | `ingest.py:_upsert_chunks` |
| Store | Single Chroma collection `screening-facility-policy`, cosine | `store.py` |
| Embedder | `BAAI/bge-base-en-v1.5`, normalized | `embeddings.py` |
| Retrieval | Single-stage cosine, `top_k=3`, `min_similarity=0.35`, `pathway`/`locale` filters | `query.py`, `policy/retrieve.py` |
| Ingest | Full rebuild (`--reset`), batch 16, locale-filtered | `ingest.py` |
| Reranker | None | — |

### Why it breaks as data grows
1. **No document identity in metadata** → cannot scope by facility/doc, cannot
   update or version a single document, retrieval blends unrelated SOPs.
2. **One-chunk-per-section + 1500-char cap** → silent content loss on long sections.
3. **Full-rebuild ingest** → slow/wasteful at thousands of chunks.
4. **Single-stage cosine** → noisy top-k once the corpus is large; brittle fixed threshold.
5. **Chroma segment orphans** accumulate on `--reset`.

## 2. Target architecture

Keep the section-based, pathway-tagged approach (good domain fit). Evolve on four axes.

### 2.1 Metadata schema (do first — cheap, unblocks the rest)

Every chunk metadata:

```json
{
  "locale": "en-AU",
  "facility_id": "site-123",
  "doc_id": "rasa-racf-toolkit",
  "doc_version": "2026-08",
  "doc_type": "facility_policy",
  "section": "8 — Passive suicidal ideation",
  "pathway": "passive_safety",
  "topic_id": "8",
  "parent_id": "rasa-racf-toolkit:8",
  "ingested_at": "2026-08-11"
}
```

New fields: `facility_id`, `doc_id`, `doc_version`, `doc_type` (promote from id prefix),
`parent_id` (for parent/child), `ingested_at`. Enables tenant scoping, versioned
replace, and rollback.

### 2.2 Parent/child chunking (quality)

- **Parent** = `##` section (context unit returned to the analyst).
- **Child** = 300–500 token window (slight overlap) within the section = embedded unit.
- Retrieve on children → dedupe up to `parent_id` → return parent section text.
- Removes the 1500-char truncation; improves recall on long SOPs; preserves the
  section-level context the analyst prompt injection relies on.

### 2.3 Two-stage retrieval with reranker (highest-leverage quality win)

```
query → Chroma cosine (fetch ~20 candidates, locale + optional pathway filter)
      → cross-encoder rerank (BAAI/bge-reranker-base)
      → keep top 3–5 parents
```

- Pairs with the BGE embedder.
- Lets you relax `min_similarity` and rely on rerank score instead of a brittle cosine cutoff.
- Keep `top_k` small for the analyst prompt; widen the *pre-rerank* candidate pool.

### 2.4 Incremental, versioned ingest (ops)

- Key upserts by `doc_id` (+ `doc_version`); delete-and-replace only the affected doc.
- Deterministic child ids: `{doc_id}:{section}:{child_index}` (drop the fragile `#offset`).
- Add orphaned-segment cleanup on reset.

### 2.5 Collection structure decision

For **multi-facility with isolation needs**:

- **Recommended:** single collection + metadata filters (`facility_id`, `locale`,
  `pathway`). Scales to tens of thousands of chunks on one HNSW index; simplest ops.
  Enforce `facility_id` filter at query time for tenant separation.
- **Alternative (only if compliance/hard isolation required):** collection per
  facility. Stronger isolation and per-tenant reset/versioning, but more index
  overhead and no cross-facility queries.

Default to single-collection + strict `facility_id` filtering unless a real
compliance requirement forces per-tenant collections.

### 2.6 Pathway strategy (safety-critical)

`pathway` stays on chunk metadata and is still **directive-sourced** per section via
`<!-- pathway: ... -->` (`section_meta.py`), with the title map as fallback.

The change is how it's *used* at retrieval (`retrieve.py`):
- **Broad first:** run an unfiltered (locale-only) search — no hard pathway exclusion.
- **Guarantee-include, don't exclude:** when a passive/active cue is detected (tags or
  transcript heuristic), *also* fetch the safety sections and mark them must-include.
  A misclassified tag can never drop the crisis protocol.
- **Any safety cue pulls BOTH passive and active sections.** Residents under-disclose
  intent, so a passive/active *mislabel* must not hide the more urgent protocol. The
  clinical distinction lives in the section content (different actions/timeframes);
  retrieval always surfaces both when any safety signal appears.
- **Rerank orders the rest;** safety must-include rows survive the top_k slice.

This keeps the deterministic safety guarantee while removing (a) the false-negative
risk of the previous exclusive `[active_safety]`-only filter, and (b) the
passive/active mislabel risk.

## 3. Phased plan

### Phase 1 — Metadata + identity (foundation)
- `policy/chunking.py`: add `doc_id`, `facility_id`, `doc_version`, `doc_type`,
  `ingested_at` to `_base_metadata`; thread `facility_id`/`doc_version` through
  `chunk_markdown` and `load_skill_sources`.
- `ingest.py`: deterministic ids from `doc_id`+section (drop `#offset`);
  stamp `ingested_at`.
- `query.py`: extend `_build_where` with `facility_id` (and `doc_id`) filters.
- Re-ingest; verify counts and metadata in `main.py` health.

### Phase 2 — Two-stage reranking (quality)
- New `policy/rerank.py`: load `bge-reranker-base`; `rerank(query, candidates) -> scored`.
- `query.py`: add `n_results` candidate pool (~20) path; return candidates unranked.
- `policy/retrieve.py`: after `_collect`, rerank merged candidates, then dedupe by
  `parent_id`, keep `top_k`.
- Config: `rag_rerank_enabled`, `rag_rerank_model`, `rag_candidate_pool` in `config.py`.

### Phase 3 — Parent/child chunking (quality)
- `policy/chunking.py`: split each retrievable section into child windows; emit child
  chunks with `parent_id` + parent text carried for return.
- Store parent text either in child metadata (simplest) or a small parent lookup.
- `retrieve.py`: map retrieved children → parent text for the analyst prompt.

### Phase 4 — Incremental/versioned ingest (ops)
- `ingest.py`: `--doc <doc_id>` mode; delete-by-`doc_id` then upsert.
- `store.py`: orphaned-segment cleanup helper; keep legacy delete list.
- Optional: per-facility ingest CLI flags.

## 4. Config additions (`backend/app/config.py`)

```
rag_rerank_enabled: bool = True
rag_rerank_model: str = "BAAI/bge-reranker-base"
rag_candidate_pool: int = 20
rag_child_max_tokens: int = 500
rag_child_overlap_tokens: int = 60
rag_default_facility_id: str | None = None
```

## 5. Validation
- Build a small golden set (transcript → expected sections) per locale/facility.
- Track recall@k and rerank win-rate before/after each phase.
- Confirm tenant isolation: queries with `facility_id` never return other tenants' chunks.

## 6. Sequencing rationale
Phase 1 is a prerequisite for everything (identity + tenant scoping). Phase 2
(reranker) is the biggest single quality gain and is independent of chunking, so it
comes before Phase 3. Phase 4 (ops) can land anytime after Phase 1 but matters most
once the corpus is large.
