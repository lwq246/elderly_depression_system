import asyncio
import unittest
from unittest.mock import patch

from backend.rag.policy.chunking import chunk_markdown, iter_policy_sections
from backend.rag.policy.section_meta import parse_section_directive, resolve_section_meta, strip_section_directives
from backend.rag.policy.validate import validate_policy_markdown
from backend.rag.policy.routing import (
    PATHWAY_ACTIVE,
    PATHWAY_DOMAIN,
    PATHWAY_PASSIVE,
    PATHWAY_ROUTINE,
    parse_policy_summary,
    pathways_for_summary,
    pathways_from_transcript_heuristic,
    section_pathway,
)
from backend.rag.policy.embed_text import build_embed_text
from backend.rag.policy.questions import parse_policy_questions


class TestSectionMeta(unittest.TestCase):
    def test_parse_pathway_and_retrievable(self):
        meta = parse_section_directive("<!-- pathway: passive_safety | retrievable: true -->")
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta.pathway, PATHWAY_PASSIVE)
        self.assertTrue(meta.retrievable)

    def test_reference_not_retrieved(self):
        meta = parse_section_directive("<!-- reference: not retrieved -->")
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertFalse(meta.retrievable)

    def test_strip_directives_from_body(self):
        raw = "<!-- pathway: routine | retrievable: true -->\n## Routine\n\nFollow up within 48 hours."
        cleaned = strip_section_directives(raw)
        self.assertNotIn("<!--", cleaned)
        self.assertIn("Follow up within 48 hours", cleaned)

    def test_resolve_uses_explicit_pathway(self):
        content = "<!-- pathway: active_safety | retrievable: true -->\n## Custom section\n\nSteps here."
        pathway, retrievable = resolve_section_meta("Custom section", content)
        self.assertEqual(pathway, PATHWAY_ACTIVE)
        self.assertTrue(retrievable)


class TestPolicyEmbedText(unittest.TestCase):
    def test_omits_table_rows(self):
        body = """## Routine follow-up actions

| Analyst `recommendation` | Facility action |
|--------------------------|-----------------|
| `none` | No mandatory follow-up |

Screen-positive pattern applies."""
        embed = build_embed_text("Routine follow-up actions", body)
        self.assertIn("Routine follow-up actions", embed)
        self.assertIn("escalation_pathway: routine", embed)
        self.assertNotIn("| `none` |", embed)
        self.assertIn("Screen-positive pattern", embed)

    def test_explicit_pathway_override(self):
        embed = build_embed_text("Other", "Body text here.", pathway=PATHWAY_PASSIVE)
        self.assertIn("escalation_pathway: passive_safety", embed)

    def test_chunk_includes_embed_text_and_pathway(self):
        md = """# Policy

## Routine follow-up actions

| Analyst `recommendation` | Facility action |
|--------------------------|-----------------|
| `none` | No mandatory follow-up for residents with adequate screening and no meaningful concerns identified during the session. |
"""
        chunks = chunk_markdown(md, source="test.md", doc_type="facility_policy", locale="en-AU")
        self.assertEqual(len(chunks), 1)
        self.assertIn("embed_text", chunks[0])
        self.assertEqual(chunks[0]["metadata"]["pathway"], PATHWAY_ROUTINE)

    def test_skips_non_retrievable_sections(self):
        md = """# Policy

<!-- pathway: reference | retrievable: false -->
## Scope and use

Short reference-only section that should not be indexed for RAG retrieval at analyst exit because it is governance prose only.

<!-- pathway: routine | retrievable: true -->
## Routine follow-up actions

| Analyst `recommendation` | Facility action |
|--------------------------|-----------------|
| `none` | No mandatory follow-up for residents with adequate screening and no meaningful concerns identified during the session. |
"""
        sections = iter_policy_sections(md, locale="en-AU")
        scope = next(s for s in sections if s["section"] == "Scope and use")
        self.assertFalse(scope["retrievable"])

        chunks = chunk_markdown(md, source="test.md", doc_type="facility_policy", locale="en-AU")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["metadata"]["section"], "Routine follow-up actions")


class TestPolicyValidation(unittest.TestCase):
    def _minimal_valid(self) -> str:
        return """# Facility SOP — Test (en-AU)

Locale: en-AU

<!-- pathway: reference | retrievable: false -->
## Scope and use

Reference-only governance text that is intentionally longer than the minimum chunk size so validation passes without indexing this section into the operational RAG index for analyst retrieval.

<!-- pathway: routine | retrievable: true -->
## Routine follow-up actions

| Analyst `recommendation` | Facility action | Target timeframe |
|--------------------------|-----------------|------------------|
| `none` | No mandatory follow-up | Next shift |
| `check_in` | Nurse wellbeing check | Within 48 hours |
| `visit_soon` | Nurse visit | Within 24 hours |
| `urgent` | Immediate nurse presence | Immediate |

<!-- pathway: domain_follow_up | retrievable: true -->
## Domain-led follow-up (non-crisis)

When recommendation is check_in or visit_soon without safety flags, use domain evidence to guide the nurse conversation including mood, sleep, appetite, social withdrawal, energy, and worries with documentation prompts for each domain signal.

<!-- pathway: passive_safety | retrievable: true -->
## Passive safety escalation

**Triggers:** passive suicidal thoughts without current plan, intent, or means. Duty nurse notified within 15 minutes. RN review same shift. Document verbatim quotes. Re-screen within 24 hours per facility mental health pathway.

<!-- pathway: active_safety | retrievable: true -->
## Active safety escalation

**Triggers:** current intent, plan, means, or imminent risk. Stop AI screening immediately. Notify RN now. Do not leave resident alone. Call 000 if imminent danger. Document within one hour. Minimum analyst mapping recommendation urgent.

<!-- pathway: active_safety | retrievable: true -->
## Crisis contacts (staff reference)

| Service | Contact | When |
|---------|---------|------|
| Emergency | 000 | Imminent danger to life |
| Mental health line | 000 000 000 | Staff consultation and referral guidance for after-hours crisis support at this facility |
"""

    def test_valid_minimal_policy(self):
        result = validate_policy_markdown(self._minimal_valid(), locale="en-AU")
        self.assertTrue(result.ok, result.errors)
        self.assertIn("Routine follow-up actions", result.retrievable_sections)
        self.assertIn("Scope and use", result.skipped_sections)

    def test_missing_passive_fails(self):
        text = self._minimal_valid()
        start = text.index("<!-- pathway: passive_safety")
        end = text.index("<!-- pathway: active_safety")
        text = text[:start] + text[end:]
        result = validate_policy_markdown(text, locale="en-AU")
        self.assertFalse(result.ok)
        self.assertTrue(any("passive_safety" in e for e in result.errors))


class TestChunkIdentityAndChildren(unittest.TestCase):
    def test_identity_metadata_present(self):
        md = """# Policy

<!-- pathway: routine | retrievable: true -->
## Routine follow-up actions

Follow up within 48 hours for any resident with a check_in recommendation and document the outcome in the care record so the next shift has clear visibility of the wellbeing plan.
"""
        chunks = chunk_markdown(
            md,
            source="facility-policy/en-AU.md",
            doc_type="facility_policy",
            locale="en-AU",
            doc_version="2026-08",
        )
        self.assertTrue(chunks)
        meta = chunks[0]["metadata"]
        self.assertEqual(meta["doc_id"], "en-AU")
        self.assertEqual(meta["doc_version"], "2026-08")
        self.assertEqual(meta["doc_type"], "facility_policy")
        self.assertIn("facility_id", meta)
        self.assertEqual(meta["parent_id"], "en-AU:Routine follow-up actions")

    def test_deterministic_ids_stable_across_calls(self):
        md = """# Policy

<!-- pathway: routine | retrievable: true -->
## Routine follow-up actions

Follow up within 48 hours for any resident with a check_in recommendation and document the outcome in the care record so the next shift has clear visibility of the wellbeing plan.
"""
        a = chunk_markdown(md, source="x/en-AU.md", doc_type="facility_policy", locale="en-AU")
        b = chunk_markdown(md, source="x/en-AU.md", doc_type="facility_policy", locale="en-AU")
        self.assertEqual([c["id"] for c in a], [c["id"] for c in b])
        self.assertNotIn("#", a[0]["id"])

    def test_long_section_splits_into_children_sharing_parent_text(self):
        long_body = "\n\n".join(
            f"Paragraph {i}: staff must document the resident wellbeing observation "
            f"and escalate per the facility SOP when concerns are identified." * 3
            for i in range(20)
        )
        md = f"""# Policy

<!-- pathway: domain_follow_up | retrievable: true -->
## Domain-led follow-up (non-crisis)

{long_body}
"""
        chunks = chunk_markdown(
            md,
            source="x/en-AU.md",
            doc_type="facility_policy",
            locale="en-AU",
            max_chars=800,
            overlap_chars=100,
        )
        self.assertGreater(len(chunks), 1)
        parent_ids = {c["parent_id"] for c in chunks}
        self.assertEqual(len(parent_ids), 1)
        # Every child returns the full parent section text.
        self.assertEqual({c["text"] for c in chunks}, {chunks[0]["text"]})
        # Child ids are unique and end with their index.
        self.assertEqual(len({c["id"] for c in chunks}), len(chunks))


class TestPolicyRouting(unittest.TestCase):
    def test_parse_policy_summary(self):
        tags = parse_policy_summary(
            "recommendation_target: none\npassive_suicidal_thoughts: false\n"
        )
        self.assertEqual(tags["recommendation_target"], "none")
        self.assertEqual(tags["passive_suicidal_thoughts"], "false")

    def test_routine_none_excludes_safety_pathways(self):
        tags = parse_policy_summary(
            """recommendation_target: none
passive_suicidal_thoughts: false
active_suicidal_ideation: false
escalation_pathway: routine"""
        )
        self.assertEqual(pathways_for_summary(tags), [PATHWAY_ROUTINE, PATHWAY_DOMAIN])

    def test_passive_pathway(self):
        tags = parse_policy_summary(
            """recommendation_target: visit_soon
passive_suicidal_thoughts: true
active_suicidal_ideation: false
escalation_pathway: passive_safety"""
        )
        self.assertEqual(pathways_for_summary(tags), [PATHWAY_PASSIVE, PATHWAY_ROUTINE])

    def test_heuristic_denial_routes_routine(self):
        transcript = [
            {"role": "resident", "text": "No, I do not wish to hurt myself."},
        ]
        self.assertEqual(
            pathways_from_transcript_heuristic(transcript),
            [PATHWAY_ROUTINE, PATHWAY_DOMAIN],
        )

    def test_section_pathway_mapping(self):
        self.assertEqual(section_pathway("Passive safety escalation"), PATHWAY_PASSIVE)
        self.assertEqual(section_pathway("Scope and use"), "reference")


class TestSafetyGuaranteeInclude(unittest.TestCase):
    def test_passive_mislabel_still_surfaces_active_section(self):
        """A passive-only tag must still surface the active safety section.

        Residents under-disclose intent, so any safety cue pulls BOTH safety sections.
        """
        from backend.rag.policy import retrieve as retrieve_mod

        # Summary tags PASSIVE only (a resident who is actually active but under-discloses).
        passive_summary = (
            "escalation_pathway: passive_safety\n"
            "passive_suicidal_thoughts: true\n"
            "active_suicidal_ideation: false\n"
            "recommendation_target: visit_soon\n"
        )

        def fake_query_collection(query, *, pathways=None, **kwargs):
            def row(section, pathway, sim):
                return {
                    "text": f"{section} body",
                    "metadata": {
                        "section": section,
                        "pathway": pathway,
                        "parent_id": f"en-AU:{section}",
                        "locale": "en-AU",
                    },
                    "cosine_similarity": sim,
                }

            if pathways and PATHWAY_ACTIVE in pathways:
                # Safety-filtered pass returns BOTH safety sections.
                return [
                    row("Passive safety escalation", PATHWAY_PASSIVE, 0.6),
                    row("Active safety escalation", PATHWAY_ACTIVE, 0.55),
                ]
            # Broad pass: routine/domain only — no active section semantically.
            return [
                row("Routine follow-up actions", PATHWAY_ROUTINE, 0.7),
                row("Domain-led follow-up (non-crisis)", PATHWAY_DOMAIN, 0.5),
            ]

        class _Coll:
            def count(self):
                return 10

        async def fake_summary(transcript, *, locale):
            return passive_summary

        with patch.object(retrieve_mod, "query_collection", fake_query_collection), patch.object(
            retrieve_mod, "embed_texts", lambda texts: [[0.0]]
        ), patch.object(retrieve_mod, "summarize_transcript_for_rag", fake_summary), patch.object(
            retrieve_mod, "rerank_rows", lambda q, rows, top_k=None: rows if top_k is None else rows[:top_k]
        ):
            result = asyncio.run(
                retrieve_mod._retrieve_by_tags(
                    [{"role": "resident", "text": "I sometimes wish I wouldn't wake up."}],
                    locale="en-AU",
                    collection=_Coll(),
                )
            )

        sections = {c["metadata"]["section"] for c in result.chunks}
        self.assertIn("Active safety escalation", sections)
        self.assertIn("Passive safety escalation", sections)


class TestPolicyQuestions(unittest.TestCase):
    def test_parse_numbered_questions(self):
        text = (
            "1. What is the routine follow-up SOP when recommendation is none?\n"
            "2. How should passive safety escalation be handled?\n"
        )
        self.assertEqual(
            parse_policy_questions(text, max_questions=4),
            [
                "What is the routine follow-up SOP when recommendation is none?",
                "How should passive safety escalation be handled?",
            ],
        )

    def test_parse_bulleted_questions(self):
        text = "- Documentation requirements after screening\n- Domain follow-up for poor sleep"
        qs = parse_policy_questions(text, max_questions=4)
        self.assertEqual(len(qs), 2)
        self.assertIn("Documentation requirements", qs[0])


if __name__ == "__main__":
    unittest.main()
