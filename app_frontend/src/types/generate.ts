import type { TORMetadata } from "./api";

export interface DocGenListItem {
  id: string;
  filename: string;
  file_size: number;
  style_name: string | null;
  status: "completed" | "failed" | "processing";
  word_count: number | null;
  created_at: string;
}

export interface DocGenDetail {
  id: string;
  filename: string;
  file_size: number;
  context: string;
  style_name: string | null;
  status: string;
  tor_content: string | null;
  metadata: TORMetadata | null;
  error_message: string | null;
  created_at: string;
}

export interface StreamDoneData {
  session_id: string;
  metadata: {
    generated_by: string;
    mode: string;
    word_count: number;
    has_assumptions: boolean;
  };
}
