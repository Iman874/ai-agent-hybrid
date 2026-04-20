export interface SessionListItem {
  id: string;
  title: string | null;
  state: string;
  turn_count: number;
  created_at: string;
  updated_at: string;
  has_tor: boolean;
}

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
  parsed_status: string | null;
  timestamp: string;
}

export interface SessionDetailResponse {
  id: string;
  created_at: string;
  updated_at: string;
  state: string;
  turn_count: number;
  completeness_score: number;
  extracted_data: import("./api").TORData;
  chat_history: ChatHistoryMessage[];
  generated_tor: string | null;
  metadata: {
    gemini_calls_count: number;
    total_tokens_local: number;
    total_tokens_gemini: number;
  };
}
