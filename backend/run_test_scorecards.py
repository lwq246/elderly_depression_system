"""Run each API test case and emit transcript + scorecard."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.run_api_test_cases import SCENARIOS, run_scenario

BASE = os.environ.get("TEST_API_BASE", "http://127.0.0.1:8001")
TIMEOUT = 180.0


def format_transcript(transcript: list[dict]) -> str:
    lines = []
    for i, turn in enumerate(transcript, 1):
        role = "Companion" if turn.get("role") == "companion" else "Resident"
        lines.append(f"{i}. **{role}:** {turn.get('text', '')}")
    return "\n".join(lines)


def format_scorecard(result: dict) -> str:
    report = result.get("report") or {}
    summary = result.get("summary") or {}
    lines = [
        f"| Field | Value |",
        f"|-------|-------|",
        f"| **Pass** | {'YES' if result.get('pass') else 'NO'} |",
        f"| **Recommendation** | `{summary.get('recommendation', '-')}` |",
        f"| **Confidence** | `{summary.get('estimate_confidence', '-')}` |",
        f"| **Concern domains** | {summary.get('concern_count', '-')} |",
        f"| **Passive suicidal** | {summary.get('passive_suicidal_thoughts', '-')} |",
        f"| **Active ideation** | {summary.get('active_suicidal_ideation', '-')} |",
        f"| **Suicide risk flag** | {summary.get('suicide_risk_flag', '-')} |",
        f"| **Validation errors** | {len(result.get('validation_errors') or [])} |",
    ]
    if result.get("failures"):
        lines.append(f"| **Failures** | {'; '.join(result['failures'])} |")

    lines.append("\n**Checks:**")
    for c in result.get("checks") or []:
        mark = "PASS" if c.get("pass") else "FAIL"
        lines.append(f"- [{mark}] `{c.get('check')}` — {c.get('detail')}")

    topics = report.get("transcript_topics") or []
    concerns = [t for t in topics if isinstance(t, dict) and t.get("concern")]
    if concerns:
        lines.append("\n**Domains with concern:**")
        for t in concerns:
            lines.append(f"- `{t.get('topic_id')}`: \"{t.get('evidence', '')}\"")

    if report.get("explanation"):
        lines.append(f"\n**Explanation:** {report['explanation']}")

    return "\n".join(lines)


def main() -> int:
    with httpx.Client() as client:
        health = client.get(f"{BASE}/api/health", timeout=10).json()

        output: dict = {
            "health": health,
            "base_url": BASE,
            "cases": [],
        }

        for spec in SCENARIOS:
            print(f"Running {spec['case_id']}...", flush=True)
            result = run_scenario(client, **spec)
            session = client.get(f"{BASE}/api/sessions/{result['session_id']}", timeout=TIMEOUT).json()
            transcript = session.get("transcript") or []

            case_out = {
                "case_id": spec["case_id"],
                "title": spec["title"],
                "resident_id": spec["resident_id"],
                "pass": result.get("pass"),
                "transcript_markdown": format_transcript(transcript),
                "transcript": transcript,
                "scorecard_markdown": format_scorecard(result),
                "report": result.get("report"),
                "validation_errors": result.get("validation_errors"),
                "checks": result.get("checks"),
                "failures": result.get("failures"),
            }
            output["cases"].append(case_out)

    passed = sum(1 for c in output["cases"] if c["pass"])
    output["passed"] = passed
    output["total"] = len(output["cases"])

    out_path = ROOT / "data" / "test_scorecards.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"passed": passed, "total": output["total"], "saved": str(out_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
