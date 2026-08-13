import asyncio
import unittest
from unittest.mock import patch

from backend.rag.policy.chunking import chunk_markdown, iter_policy_sections
from backend.rag.policy.section_meta import parse_section_directive, resolve_section_pathway, strip_section_directives
from backend.rag.policy.validate import validate_policy_markdown
from backend.rag.policy.routing import (
    PATHWAY_ACTIVE,
    PATHWAY_GENERAL,
    PATHWAY_PASSIVE,
    parse_policy_summary,
    pathways_for_summary,
    section_pathway,
)
from backend.rag.policy.embed_text import build_embed_text
from backend.rag.policy.summary import SUMMARY_SYSTEM
from backend.rag.policy.convert import check_conversion_coverage


class TestSectionMeta(unittest.TestCase):
    def test_parse_pathway(self):
        meta = parse_section_directive("<!-- pathway: passive_safety -->")
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta.pathway, PATHWAY_PASSIVE)

    def test_legacy_retrievable_kv_is_ignored(self):
        # Older docs may still carry `| retrievable: ...`; the pathway must still parse.
        meta = parse_section_directive("<!-- pathway: passive_safety | retrievable: false -->")
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta.pathway, PATHWAY_PASSIVE)

    def test_strip_directives_from_body(self):
        raw = "<!-- pathway: routine -->\n## Routine\n\nFollow up within 48 hours."
        cleaned = strip_section_directives(raw)
        self.assertNotIn("<!--", cleaned)
        self.assertIn("Follow up within 48 hours", cleaned)

    def test_resolve_uses_explicit_pathway(self):
        content = "<!-- pathway: active_safety -->\n## Custom section\n\nSteps here."
        self.assertEqual(resolve_section_pathway("Custom section", content), PATHWAY_ACTIVE)


class TestPolicyEmbedText(unittest.TestCase):
    def test_omits_table_rows(self):
        body = """## Routine follow-up actions

| Analyst `recommendation` | Facility action |
|--------------------------|-----------------|
| `none` | No mandatory follow-up |

Screen-positive pattern applies."""
        embed = build_embed_text("Routine follow-up actions", body)
        self.assertIn("Routine follow-up actions", embed)
        # Non-safety sections are labelled 'general' now.
        self.assertIn("escalation_pathway: general", embed)
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
        self.assertEqual(chunks[0]["metadata"]["pathway"], PATHWAY_GENERAL)

    def test_indexes_all_sections(self):
        md = """# Policy

<!-- pathway: reference -->
## Scope and use

Reference/governance prose that is now indexed for retrieval like every other section.

<!-- pathway: routine -->
## Routine follow-up actions

| Analyst `recommendation` | Facility action |
|--------------------------|-----------------|
| `none` | No mandatory follow-up for residents with adequate screening and no meaningful concerns identified during the session. |
"""
        sections = iter_policy_sections(md, locale="en-AU")
        self.assertNotIn("retrievable", sections[0])
        scope = next(s for s in sections if s["section"] == "Scope and use")
        # 'reference' is no longer a valid pathway — non-safety sections are 'general'.
        self.assertEqual(scope["pathway"], PATHWAY_GENERAL)

        chunks = chunk_markdown(md, source="test.md", doc_type="facility_policy", locale="en-AU")
        indexed = {c["metadata"]["section"] for c in chunks}
        self.assertIn("Scope and use", indexed)
        self.assertIn("Routine follow-up actions", indexed)


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
        # Every section is now indexed, including the reference "Scope and use".
        self.assertIn("Routine follow-up actions", result.indexed_sections)
        self.assertIn("Scope and use", result.indexed_sections)

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
            "passive_suicidal_thoughts: false\nactive_suicidal_ideation: true\n"
        )
        self.assertEqual(tags["passive_suicidal_thoughts"], "false")
        self.assertEqual(tags["active_suicidal_ideation"], "true")

    def test_no_safety_cue_returns_none(self):
        tags = parse_policy_summary(
            """passive_suicidal_thoughts: false
active_suicidal_ideation: false"""
        )
        self.assertIsNone(pathways_for_summary(tags))

    def test_passive_pathway(self):
        tags = parse_policy_summary(
            """passive_suicidal_thoughts: true
active_suicidal_ideation: false"""
        )
        self.assertEqual(pathways_for_summary(tags), [PATHWAY_PASSIVE])

    def test_active_pathway(self):
        tags = parse_policy_summary(
            """passive_suicidal_thoughts: false
active_suicidal_ideation: true"""
        )
        self.assertEqual(pathways_for_summary(tags), [PATHWAY_ACTIVE])

    def test_active_takes_precedence_over_passive(self):
        tags = parse_policy_summary(
            """passive_suicidal_thoughts: true
active_suicidal_ideation: true"""
        )
        self.assertEqual(pathways_for_summary(tags), [PATHWAY_ACTIVE])

    def test_section_pathway_mapping(self):
        self.assertEqual(section_pathway("Passive safety escalation"), PATHWAY_PASSIVE)
        self.assertEqual(section_pathway("Active safety escalation"), PATHWAY_ACTIVE)
        # Everything non-safety collapses to 'general'.
        self.assertEqual(section_pathway("Scope and use"), PATHWAY_GENERAL)


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
            # Broad pass: general sections only — no active section semantically.
            return [
                row("Routine follow-up actions", PATHWAY_GENERAL, 0.7),
                row("Domain-led follow-up (non-crisis)", PATHWAY_GENERAL, 0.5),
            ]

        class _Coll:
            def count(self):
                return 10

        async def fake_summary(transcript, *, locale):
            return passive_summary

        with patch.object(retrieve_mod, "query_collection", fake_query_collection), patch.object(
            retrieve_mod, "embed_texts", lambda texts: [[0.0]]
        ), patch.object(retrieve_mod, "summarize_transcript_for_rag", fake_summary):
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

    def test_transcript_backstop_forces_safety_when_summary_undertags(self):
        """Explicit crisis language in the transcript force-includes safety sections,
        even when the LLM summary tags no safety pathway at all (under-tagging)."""
        from backend.rag.policy import retrieve as retrieve_mod

        # Summary tags ROUTINE only — the LLM missed the disclosure entirely.
        routine_summary = (
            "escalation_pathway: routine\n"
            "passive_suicidal_thoughts: false\n"
            "active_suicidal_ideation: false\n"
            "recommendation_target: routine_followup\n"
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
                return [
                    row("Passive safety escalation", PATHWAY_PASSIVE, 0.4),
                    row("Active safety escalation", PATHWAY_ACTIVE, 0.35),
                ]
            return [
                row("Routine follow-up actions", PATHWAY_GENERAL, 0.9),
                row("Domain-led follow-up (non-crisis)", PATHWAY_GENERAL, 0.8),
            ]

        class _Coll:
            def count(self):
                return 10

        async def fake_summary(transcript, *, locale):
            return routine_summary

        with patch.object(retrieve_mod, "query_collection", fake_query_collection), patch.object(
            retrieve_mod, "embed_texts", lambda texts: [[0.0]]
        ), patch.object(retrieve_mod, "summarize_transcript_for_rag", fake_summary):
            result = asyncio.run(
                retrieve_mod._retrieve_by_tags(
                    [{"role": "resident", "text": "Honestly I just want it all to stop."}],
                    locale="en-AU",
                    collection=_Coll(),
                )
            )

        sections = {c["metadata"]["section"] for c in result.chunks}
        self.assertIn("Active safety escalation", sections)
        self.assertIn("Passive safety escalation", sections)


class TestConversionCoverage(unittest.TestCase):
    _SOURCE = (
        "Notify duty nurse within 15 minutes. Call 995 if imminent danger. "
        "Re-screen within 24 hours. IMH crisis line 6389 2222."
    )

    def test_reformat_preserving_content_passes(self):
        reformatted = (
            "# Facility SOP\nLocale: en-SG\n\n"
            "<!-- pathway: active_safety | retrievable: true -->\n"
            "## Escalation\n\n"
            "Notify duty nurse within 15 minutes. Call 995 if imminent danger.\n\n"
            "Re-screen within 24 hours. IMH crisis line 6389 2222.\n"
        )
        result = check_conversion_coverage(self._SOURCE, reformatted)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.missing_numbers, [])

    def test_dropped_content_fails_on_ratio(self):
        summarized = "## Escalation\nNotify nurse and call 995. Re-screen 24h. 6389 2222 15."
        result = check_conversion_coverage(self._SOURCE, summarized)
        self.assertFalse(result.ok)

    def test_missing_number_is_flagged(self):
        # Same length-ish text but the 15-minute timeframe and phone are gone.
        no_numbers = (
            "# Facility SOP\nLocale: en-SG\n\n## Escalation\n\n"
            "Notify duty nurse within some minutes. Call emergency services if imminent "
            "danger to life occurs. Re-screen within twenty four hours as required here."
        )
        result = check_conversion_coverage(self._SOURCE, no_numbers)
        self.assertIn("6389 2222".replace(" ", ""), result.missing_numbers)


class TestSummaryContract(unittest.TestCase):
    def test_prompt_requests_retained_tags(self):
        self.assertIn("retrieval_focus:", SUMMARY_SYSTEM)
        self.assertIn("passive_suicidal_thoughts:", SUMMARY_SYSTEM)
        self.assertIn("active_suicidal_ideation:", SUMMARY_SYSTEM)

    def test_prompt_drops_trimmed_tags(self):
        for dropped in (
            "escalation_pathway:",
            "recommendation_target:",
            "suicide_risk_flag:",
            "safety_discussed:",
            "domains_with_concern:",
            "domains_discussed:",
            "screen_positive_pattern:",
            "safety_note:",
        ):
            self.assertNotIn(dropped, SUMMARY_SYSTEM)


if __name__ == "__main__":
    unittest.main()
