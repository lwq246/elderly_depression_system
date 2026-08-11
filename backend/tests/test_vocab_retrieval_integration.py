import unittest

from backend.tests.vocab_retrieval_cases import run_vocab_retrieval_cases


class VocabRetrievalIntegrationTests(unittest.TestCase):
    def test_all_synthetic_cases(self) -> None:
        failures: list[str] = []
        for result in run_vocab_retrieval_cases():
            if not result["pass"]:
                retrieved = ", ".join(r["term"] for r in result["matches"]) or "(none)"
                failures.append(f"{result['case_id']}: {result['check']} | retrieved: {retrieved}")
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
