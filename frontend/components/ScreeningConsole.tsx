"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Health, Resident, Session } from "@/lib/types";

type Tab = "room" | "nurse";

export default function ScreeningConsole() {
  const [tab, setTab] = useState<Tab>("room");
  const [health, setHealth] = useState<Health | null>(null);
  const [residents, setResidents] = useState<Resident[]>([]);
  const [session, setSession] = useState<Session | null>(null);
  const [residentId, setResidentId] = useState("R-001");
  const [locale, setLocale] = useState("en-SG");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Awaited<ReturnType<typeof api.sessions>>>([]);

  useEffect(() => {
    Promise.all([api.health(), api.residents(), api.sessions()])
      .then(([h, r, s]) => {
        setHealth(h);
        setResidents(r);
        setSessions(s);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  async function startSession() {
    setLoading(true);
    setError(null);
    try {
      const created = await api.entry({
        resident_id: residentId,
        locale,
      });
      setSession(created);
      const list = await api.sessions();
      setSessions(list);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage() {
    if (!session || !input.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await api.message(session.id, input.trim());
      setSession(updated);
      setInput("");
      if (updated.status === "ended") {
        const list = await api.sessions();
        setSessions(list);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function leaveRoom() {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await api.exit(session.id);
      setSession(updated);
      const list = await api.sessions();
      setSessions(list);
      setTab("nurse");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function loadSession(id: string) {
    setLoading(true);
    setError(null);
    try {
      const detail = await api.session(id);
      setSession(detail);
      setTab("nurse");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header>
        <div>
          <h1>Screening Console</h1>
          <p style={{ margin: "0.25rem 0 0", color: "var(--muted)" }}>
            Simulates UWB room entry, voice turns, exit, and nurse analyst report.
          </p>
        </div>
        {health && (
          <span className="badge">
            LLM: {health.llm_configured ? health.model ?? "configured" : "not configured"}
          </span>
        )}
      </header>

      <div className="tabs">
        <button type="button" className={tab === "room" ? "active" : ""} onClick={() => setTab("room")}>
          Screening room
        </button>
        <button type="button" className={tab === "nurse" ? "active" : ""} onClick={() => setTab("nurse")}>
          Nurse dashboard
        </button>
      </div>

      {error && <div className="errors">{error}</div>}

      {tab === "room" ? (
        <div className="grid">
          <div className="panel panel-setup">
            <h2>Session setup (uwb.entry)</h2>
            <label htmlFor="resident">Resident</label>
            <select
              id="resident"
              value={residentId}
              onChange={(e) => {
                const id = e.target.value;
                setResidentId(id);
                const r = residents.find((x) => x.resident_id === id);
                if (r) setLocale(r.locale);
              }}
              disabled={!!session && session.status === "active"}
            >
              {residents.map((r) => (
                <option key={r.resident_id} value={r.resident_id}>
                  {r.resident_id} — {r.preferred_name ?? "No name"} ({r.locale})
                </option>
              ))}
            </select>

            <label htmlFor="locale">Locale</label>
            <select
              id="locale"
              value={locale}
              onChange={(e) => setLocale(e.target.value)}
              disabled={!!session && session.status === "active"}
            >
              <option value="en-SG">en-SG</option>
              <option value="en-AU">en-AU</option>
            </select>

            <button
              type="button"
              className="primary"
              onClick={startSession}
              disabled={loading || (!!session && session.status === "active")}
            >
              Start session
            </button>
          </div>

          <div className="panel">
            <h2>Live transcript {session ? `· ${session.status}` : ""}</h2>
            <div className="transcript">
              {session?.transcript.map((turn, i) => (
                <div key={i} className={`bubble ${turn.role}`}>
                  <div className="role">
                    {turn.role === "companion" ? "Companion (speaker)" : "Resident (STT)"}
                  </div>
                  <div>{turn.text}</div>
                </div>
              ))}
              {!session && <p style={{ color: "var(--muted)" }}>Start a session to simulate room entry.</p>}
            </div>

            <div className="compose">
              <input
                placeholder="Type resident reply (simulated STT)…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                disabled={!session || session.status !== "active" || loading}
              />
              <button
                type="button"
                className="primary"
                onClick={sendMessage}
                disabled={!session || session.status !== "active" || loading}
              >
                Send
              </button>
              <button
                type="button"
                className="secondary"
                onClick={leaveRoom}
                disabled={!session || session.status !== "active" || loading}
              >
                Leave room
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid">
          <div className="panel">
            <h2>Past sessions</h2>
            <ul className="session-list">
              {sessions.map((s) => (
                <li
                  key={s.id}
                  className={session?.id === s.id ? "active" : ""}
                  onClick={() => loadSession(s.id)}
                >
                  <strong>{s.preferred_name ?? s.resident_id}</strong>
                  <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                    {s.status} · {s.turn_count} turns · {new Date(s.created_at).toLocaleString()}
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="panel">
            <h2>Nurse report</h2>
            {!session?.report && (
              <p style={{ color: "var(--muted)" }}>Select a session with a completed analyst run.</p>
            )}

            {session?.validation_errors?.length ? (
              <div className="errors">
                <strong>Validation warnings</strong>
                <ul>
                  {session.validation_errors.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {session?.report && (
              <>
                <div className="report-grid">
                  <div className="metric">
                    <strong>Confidence</strong>
                    {session.report.estimate_confidence}
                  </div>
                  <div className="metric">
                    <strong>Recommendation</strong>
                    <span className={`recommendation ${session.report.recommendation}`}>
                      {session.report.recommendation}
                    </span>
                  </div>
                  <div className="metric">
                    <strong>Suicide risk flag</strong>
                    {session.report.suicide_risk_flag ? "true" : "false"}
                  </div>
                  <div className="metric">
                    <strong>Safety flags</strong>
                    passive: {String(session.report.passive_suicidal_thoughts)} · active:{" "}
                    {String(session.report.active_suicidal_ideation)}
                  </div>
                </div>

                <p style={{ marginTop: "1rem" }}>{session.report.explanation}</p>

                <h3>Domains</h3>
                <table className="topics">
                  <thead>
                    <tr>
                      <th>Domain</th>
                      <th>Discussed</th>
                      <th>Concern</th>
                      <th>Evidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {session.report.transcript_topics.map((t) => (
                      <tr key={t.topic_id}>
                        <td>{t.label}</td>
                        <td>{t.discussed ? "yes" : "no"}</td>
                        <td>{t.concern ? "yes" : "no"}</td>
                        <td>{t.evidence || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
