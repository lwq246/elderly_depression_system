export interface Resident {
  resident_id: string;
  preferred_name: string | null;
  locale: string;
  notes: string;
}

export interface TranscriptTurn {
  role: "companion" | "resident";
  text: string;
  /** Glossary term/meaning pairs matched on this resident turn (for analyst). */
  vocab_matches?: Array<{ term: string; meaning: string }>;
  at: string;
}

export interface TopicRow {
  topic_id: string;
  label: string;
  concern: boolean;
  evidence: string;
  discussed: boolean;
}

export interface AnalystReport {
  estimate_confidence: "low" | "medium" | "high";
  suicide_risk_flag: boolean;
  passive_suicidal_thoughts: boolean;
  active_suicidal_ideation: boolean;
  transcript_topics: TopicRow[];
  indicators: Array<{
    domain: string;
    indicator: string;
    present: boolean;
    observation: string;
    severity: string;
  }>;
  explanation: string;
  recommendation: "none" | "check_in" | "visit_soon" | "urgent";
}

export interface Session {
  id: string;
  resident_id: string;
  preferred_name: string | null;
  locale: string;
  room_id: string | null;
  status: string;
  transcript: TranscriptTurn[];
  report: AnalystReport | null;
  validation_errors: string[];
  llm_inputs?: Array<{
    call: string;
    attempt?: number;
    turn_index?: number;
    model?: string;
    temperature?: number;
    json_mode?: boolean;
    messages: Array<{ role: string; content: string }>;
  }>;
  created_at: string;
  ended_at: string | null;
}

export interface SessionSummary {
  id: string;
  resident_id: string;
  preferred_name: string | null;
  locale: string;
  room_id: string | null;
  status: string;
  created_at: string;
  ended_at: string | null;
  turn_count: number;
  has_report: boolean;
  validation_error_count: number;
}

export interface Health {
  status: string;
  llm_configured: boolean;
  model: string | null;
}
