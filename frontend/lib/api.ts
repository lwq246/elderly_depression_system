import type { Health, Resident, Session, SessionSummary } from "@/lib/types";

// Dev: talk to FastAPI directly. Next.js rewrites time out at ~30s, and the analyst
// (RAG summary + report) often takes longer — the proxy then surfaces as a 500.
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ??
  (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/api/health"),
  residents: () => request<Resident[]>("/api/residents"),
  sessions: () => request<SessionSummary[]>("/api/sessions"),
  session: (id: string) => request<Session>(`/api/sessions/${id}`),
  entry: (body: {
    resident_id: string;
    locale?: string;
    room_id?: string;
  }) =>
    request<Session>("/api/sessions/entry", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  message: (sessionId: string, text: string) =>
    request<Session>(`/api/sessions/${sessionId}/message`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  exit: (sessionId: string) =>
    request<Session>(`/api/sessions/${sessionId}/exit`, { method: "POST" }),
  analyze: (sessionId: string) =>
    request<Session>(`/api/sessions/${sessionId}/analyze`, { method: "POST" }),
};
