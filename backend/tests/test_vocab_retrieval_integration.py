import unittest

from backend.app.config import settings
from backend.rag.store import get_vocab_collection
from backend.tests.vocab_retrieval_cases import run_vocab_retrieval_cases


def _integration_ready() -> str | None:
    if not settings.openai_api_key:
        return "OPENAI_API_KEY required for RAG embeddings"
    try:
        if get_vocab_collection().count() == 0:
            return "vocab index empty — run backend/rag/ingest.py --reset"
    except Exception as exc:
        return str(exc)
    return None


@unittest.skipIf(_integration_ready() is not None, _integration_ready() or "")
class VocabRetrievalIntegrationTests(unittest.TestCase):
    def test_all_synthetic_cases(self) -> None:
        failures: list[str] = []
        for result in run_vocab_retrieval_cases():
            if not result["pass"]:
                chroma = ", ".join(
                    f"{r['term']} (cosine_sim={r['cosine_similarity']})"
                    for r in result.get("chroma_hits") or []
                ) or "(none)"
                retrieved = ", ".join(
                    f"{r['term']} (cosine_sim={r['cosine_similarity']})"
                    for r in result["retrieved"]
                ) or "(none)"
                failures.append(
                    f"{result['case_id']}: {result['check']} | "
                    f"chroma: {chroma} | retrieved: {retrieved}"
                )
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
