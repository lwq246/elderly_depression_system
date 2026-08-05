import unittest

from backend.app.skills import (
    _extract_companion_vocabulary,
    load_analyst_system_prompt,
    load_companion_system_prompt,
)


class TestCompanionVocabulary(unittest.TestCase):
    def test_extract_includes_words_table_skips_policy_and_sources(self):
        md = """# Title

## Policy: mirror-first

| Mode | When |
|------|------|
| standard | default |

## Words residents often use (wellbeing screening)

| They may say | Meaning |
|--------------|---------|
| sian | bored, fed up |

## Sources

See reference.md
"""
        out = _extract_companion_vocabulary(md)
        self.assertIn("sian", out)
        self.assertIn("Words residents often use", out)
        self.assertNotIn("Policy", out)
        self.assertNotIn("Sources", out)

    def test_load_companion_includes_vocab_reference_en_sg(self):
        prompt = load_companion_system_prompt("en-SG", "standard")
        self.assertIn("## Local vocabulary reference", prompt)
        self.assertIn("sian", prompt)
        self.assertIn("buay tahan", prompt)
        self.assertIn("Singlish particles", prompt)

    def test_load_companion_includes_vocab_reference_en_au(self):
        prompt = load_companion_system_prompt("en-AU", "standard")
        self.assertIn("## Local vocabulary reference", prompt)
        self.assertIn("crook", prompt)
        self.assertIn("CALD caution", prompt)

    def test_load_companion_excludes_analyst_mapping(self):
        prompt = load_companion_system_prompt("en-SG", "standard")
        self.assertNotIn("Analyst screening mapping", prompt)
        self.assertNotIn("mood_spirits", prompt)

    def test_load_analyst_includes_locale_gloss_en_sg(self):
        prompt = load_analyst_system_prompt("en-SG")
        self.assertIn("sian", prompt)
        self.assertIn("buay tahan", prompt)
        self.assertNotIn("she'll be right", prompt)

    def test_load_analyst_includes_locale_gloss_en_au(self):
        prompt = load_analyst_system_prompt("en-AU")
        self.assertIn("crook", prompt)
        self.assertIn("she'll be right", prompt)
        self.assertNotIn("buay tahan", prompt)


    def test_companion_prompt_uses_runtime_skills(self):
        prompt = load_companion_system_prompt("en-SG", "standard")
        self.assertIn("Mirror local words (required)", prompt)
        self.assertIn("Companion runtime rules", prompt)
        self.assertLess(len(prompt), 16_000)

    def test_analyst_prompt_smaller_examples(self):
        prompt = load_analyst_system_prompt("en-SG")
        self.assertIn("Safety denial", prompt)
        self.assertIn("plan denial", prompt.lower())
        self.assertLess(len(prompt), 17_500)


if __name__ == "__main__":
    unittest.main()
