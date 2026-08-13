import unittest

from backend.app.skills import (
    load_analyst_system_prompt,
    load_companion_system_prompt,
    load_greeting,
)


class TestCompanionPrompt(unittest.TestCase):
    def test_companion_does_not_inline_local_vocabulary_en_sg(self):
        prompt = load_companion_system_prompt("en-SG")
        # Vocabulary now lives in the Chroma vocab collection and is retrieved per turn and
        # re-injected into the user message — it must NOT be inlined in the system prompt.
        self.assertNotIn("## Local vocabulary reference", prompt)
        self.assertNotIn("## Retrieved local vocabulary (this turn)", prompt)

    def test_companion_does_not_inline_local_vocabulary_en_au(self):
        prompt = load_companion_system_prompt("en-AU")
        self.assertNotIn("## Local vocabulary reference", prompt)

    def test_companion_excludes_analyst_mapping(self):
        prompt = load_companion_system_prompt("en-SG")
        self.assertNotIn("Analyst screening mapping", prompt)
        self.assertNotIn("mood_spirits", prompt)
        self.assertLess(len(prompt), 26_000)


class TestAnalystPrompt(unittest.TestCase):
    def test_analyst_inlines_local_vocabulary(self):
        prompt = load_analyst_system_prompt("en-SG")
        self.assertIn("## Local vocabulary reference", prompt)
        self.assertIn("buay tahan", prompt)
        prompt_au = load_analyst_system_prompt("en-AU")
        self.assertIn("## Local vocabulary reference", prompt_au)
        self.assertIn("she'll be right", prompt_au)

    def test_analyst_prompt_has_examples(self):
        prompt = load_analyst_system_prompt("en-SG")
        self.assertIn("Safety denial", prompt)
        self.assertIn("plan denial", prompt.lower())
        self.assertLess(len(prompt), 19_000)


class TestGreetings(unittest.TestCase):
    def test_load_greeting_with_name_en_sg(self):
        greeting = load_greeting("en-SG", "Mrs Tan")
        self.assertIn("Mrs Tan", greeting)
        self.assertIn("friendly check-in", greeting)

    def test_load_greeting_generic_en_au(self):
        greeting = load_greeting("en-AU", None)
        self.assertIn("quiet yarn", greeting)


if __name__ == "__main__":
    unittest.main()
