import unittest

from backend.app.skills import (
    load_analyst_system_prompt,
    load_companion_system_prompt,
    load_greeting,
)


class TestCompanionVocabulary(unittest.TestCase):
    def test_load_companion_no_static_vocab_en_sg(self):
        prompt = load_companion_system_prompt("en-SG")
        self.assertNotIn("## Local vocabulary reference", prompt)
        self.assertNotIn("## Retrieved local vocabulary (this turn)", prompt)

    def test_load_companion_no_static_vocab_en_au(self):
        prompt = load_companion_system_prompt("en-AU")
        self.assertNotIn("## Local vocabulary reference", prompt)

    def test_load_companion_excludes_analyst_mapping(self):
        prompt = load_companion_system_prompt("en-SG")
        self.assertNotIn("Analyst screening mapping", prompt)
        self.assertNotIn("mood_spirits", prompt)

    def test_load_analyst_excludes_locale_gloss(self):
        prompt = load_analyst_system_prompt("en-SG")
        self.assertNotIn("Analyst locale", prompt)
        self.assertNotIn("buay tahan", prompt)
        prompt_au = load_analyst_system_prompt("en-AU")
        self.assertNotIn("she'll be right", prompt_au)

    def test_companion_prompt_uses_runtime_skills(self):
        prompt = load_companion_system_prompt("en-SG")
        self.assertIn("Mirror local words (required)", prompt)
        self.assertIn("burden my children", prompt)
        self.assertIn("Companion runtime rules", prompt)
        self.assertLess(len(prompt), 14_000)

    def test_load_greeting_with_name_en_sg(self):
        greeting = load_greeting("en-SG", "Mrs Tan")
        self.assertIn("Mrs Tan", greeting)
        self.assertIn("friendly check-in", greeting)

    def test_load_greeting_generic_en_au(self):
        greeting = load_greeting("en-AU", None)
        self.assertIn("quiet yarn", greeting)

    def test_analyst_prompt_smaller_examples(self):
        prompt = load_analyst_system_prompt("en-SG")
        self.assertIn("Safety denial", prompt)
        self.assertIn("plan denial", prompt.lower())
        self.assertLess(len(prompt), 17_500)


if __name__ == "__main__":
    unittest.main()
