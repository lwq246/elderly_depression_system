#!/usr/bin/env python3
"""Run one research round for screening-conversation / elderly-depression-detection skills.

Uses DuckDuckGo search (ddgs) when available; falls back to curated query logging.
Appends findings to research log and updates state. Stops after MAX_ROUNDS (30).
"""

from __future__ import annotations

import json
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOPICS_PATH = Path(__file__).parent / "topics.json"
STATE_PATH = ROOT / "research" / "state.json"
LOG_DIR = ROOT / "research" / "rounds"
MAX_ROUNDS = 30


def load_json(path: Path) -> dict | list:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def search_web(query: str, max_results: int = 5) -> list[dict]:
    try:
        from ddgs import DDGS  # type: ignore

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", r.get("link", "")),
                        "snippet": r.get("body", r.get("snippet", "")),
                    }
                )
        return results
    except Exception as exc:  # noqa: BLE001
        return [{"title": "search_error", "url": "", "snippet": str(exc)}]


def format_round_markdown(round_num: int, topic: dict, results: list[dict]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Research Round {round_num}",
        "",
        f"- **Completed:** {ts}",
        f"- **Topic ID:** {topic['id']}",
        f"- **Query:** {topic['topic']}",
        f"- **Target skill:** {topic['skill']}",
        "",
        "## Search results",
        "",
    ]
    for i, r in enumerate(results, 1):
        lines.extend(
            [
                f"### {i}. {r.get('title', 'Untitled')}",
                "",
                f"- **URL:** {r.get('url', 'n/a')}",
                "",
                textwrap.fill(r.get("snippet", ""), width=100),
                "",
            ]
        )
    lines.extend(
        [
            "## Skill implications (draft)",
            "",
            "- Review snippets above for evidence to add to communication-guide.md or reference.md.",
            "- Cross-check claims against primary sources before updating SKILL.md.",
            "",
        ]
    )
    return "\n".join(lines)


def run_round(force: bool = False) -> int:
    topics: list[dict] = load_json(TOPICS_PATH)  # type: ignore[assignment]
    state: dict = load_json(STATE_PATH) or {"completed_rounds": 0, "last_round_at": None}

    completed = int(state.get("completed_rounds", 0))
    if completed >= MAX_ROUNDS and not force:
        print(f"All {MAX_ROUNDS} rounds complete. Use --force to re-run.")
        return 0

    round_num = completed + 1
    topic = topics[completed % len(topics)]
    query = topic["topic"]

    print(f"Round {round_num}/{MAX_ROUNDS}: {query}")
    results = search_web(query)

    md = format_round_markdown(round_num, topic, results)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"round-{round_num:02d}.md"
    log_path.write_text(md, encoding="utf-8")

    state["completed_rounds"] = round_num
    state["last_round_at"] = datetime.now(timezone.utc).isoformat()
    state["last_topic_id"] = topic["id"]
    state.setdefault("schedule", {"interval_minutes": 30, "target_rounds": MAX_ROUNDS, "mode": "one_per_tick"})
    save_json(STATE_PATH, state)

    print(f"Wrote {log_path}")
    return round_num


def run_all_remaining() -> None:
    state: dict = load_json(STATE_PATH) or {"completed_rounds": 0}
    while int(state.get("completed_rounds", 0)) < MAX_ROUNDS:
        run_round()
        state = load_json(STATE_PATH) or state


def main() -> None:
    if "--all" in sys.argv:
        run_all_remaining()
        return
    force = "--force" in sys.argv
    run_round(force=force)


if __name__ == "__main__":
    main()
