import json

import sqlite3

import uuid

from contextlib import contextmanager

from datetime import datetime, timezone

from typing import Any



from .config import settings





def _utc_now() -> str:

    return datetime.now(timezone.utc).isoformat()





def _drop_legacy_speech_register_column(conn: sqlite3.Connection) -> None:
    cols = [row[1] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()]
    if "speech_register" in cols:
        conn.execute("ALTER TABLE sessions DROP COLUMN speech_register")


def init_db() -> None:

    with get_conn() as conn:

        conn.executescript(

            """

            CREATE TABLE IF NOT EXISTS sessions (

                id TEXT PRIMARY KEY,

                resident_id TEXT NOT NULL,

                preferred_name TEXT,

                locale TEXT NOT NULL,

                room_id TEXT,

                status TEXT NOT NULL,

                transcript_json TEXT NOT NULL DEFAULT '[]',

                report_json TEXT,

                validation_errors_json TEXT,

                created_at TEXT NOT NULL,

                ended_at TEXT

            );

            """

        )

        _drop_legacy_speech_register_column(conn)





@contextmanager

def get_conn():

    conn = sqlite3.connect(settings.database_path)

    conn.row_factory = sqlite3.Row

    try:

        yield conn

        conn.commit()

    finally:

        conn.close()





def create_session(

    *,

    resident_id: str,

    preferred_name: str | None,

    locale: str,

    room_id: str | None,

    opening_message: str,

) -> dict[str, Any]:

    session_id = str(uuid.uuid4())

    transcript = [{"role": "companion", "text": opening_message, "at": _utc_now()}]

    with get_conn() as conn:

        conn.execute(

            """

            INSERT INTO sessions (

                id, resident_id, preferred_name, locale,

                room_id, status, transcript_json, created_at

            ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)

            """,

            (

                session_id,

                resident_id,

                preferred_name,

                locale,

                room_id,

                json.dumps(transcript),

                _utc_now(),

            ),

        )

    return get_session(session_id)





def get_session(session_id: str) -> dict[str, Any] | None:

    with get_conn() as conn:

        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()

    if not row:

        return None

    return _row_to_session(row)





def list_sessions(limit: int = 50) -> list[dict[str, Any]]:

    with get_conn() as conn:

        rows = conn.execute(

            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?",

            (limit,),

        ).fetchall()

    return [_row_to_session(r) for r in rows]





def append_turn(
    session_id: str,
    role: str,
    text: str,
    *,
    text_normalized: str | None = None,
) -> dict[str, Any] | None:

    session = get_session(session_id)

    if not session or session["status"] != "active":

        return None

    transcript = session["transcript"]

    turn: dict[str, Any] = {"role": role, "text": text, "at": _utc_now()}
    if text_normalized is not None:
        turn["text_normalized"] = text_normalized
    transcript.append(turn)

    with get_conn() as conn:

        conn.execute(

            "UPDATE sessions SET transcript_json = ? WHERE id = ?",

            (json.dumps(transcript), session_id),

        )

    return get_session(session_id)





def end_session(

    session_id: str,

    *,

    closing_message: str | None,

    report: dict[str, Any] | None,

    validation_errors: list[str],

) -> dict[str, Any] | None:

    session = get_session(session_id)

    if not session:

        return None

    transcript = session["transcript"]

    if closing_message:

        transcript.append({"role": "companion", "text": closing_message, "at": _utc_now()})

    with get_conn() as conn:

        conn.execute(

            """

            UPDATE sessions

            SET status = 'ended',

                transcript_json = ?,

                report_json = ?,

                validation_errors_json = ?,

                ended_at = ?

            WHERE id = ?

            """,

            (

                json.dumps(transcript),

                json.dumps(report) if report else None,

                json.dumps(validation_errors),

                _utc_now(),

                session_id,

            ),

        )

    return get_session(session_id)





def save_report(session_id: str, report: dict[str, Any], validation_errors: list[str]) -> None:

    with get_conn() as conn:

        conn.execute(

            """

            UPDATE sessions

            SET report_json = ?, validation_errors_json = ?

            WHERE id = ?

            """,

            (json.dumps(report), json.dumps(validation_errors), session_id),

        )





def _row_to_session(row: sqlite3.Row) -> dict[str, Any]:

    return {

        "id": row["id"],

        "resident_id": row["resident_id"],

        "preferred_name": row["preferred_name"],

        "locale": row["locale"],

        "room_id": row["room_id"],

        "status": row["status"],

        "transcript": json.loads(row["transcript_json"]),

        "report": json.loads(row["report_json"]) if row["report_json"] else None,

        "validation_errors": json.loads(row["validation_errors_json"])

        if row["validation_errors_json"]

        else [],

        "created_at": row["created_at"],

        "ended_at": row["ended_at"],

    }


