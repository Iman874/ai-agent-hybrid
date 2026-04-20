export interface SessionState {
  status: string;
  turn_count: number;
  completeness_score: number;
  filled_fields: string[];
  missing_fields: string[];
}

export interface TORMetadata {
  generated_by: string;
  mode: string;
  word_count: number;
  generation_time_ms: number;
  has_assumptions: boolean;
  prompt_tokens: number;
  completion_tokens: number;
}

export interface TORDocument {
  content: string;
  metadata: TORMetadata;
}

export interface EscalationInfo {
  reason: string;
  trigger: string;
  auto_escalated: boolean;
}

export interface TORData {
  judul_kegiatan: string | null;
  latar_belakang: string | null;
  tujuan: string | null;
  sasaran: string | null;
  target_peserta: string | null;
  waktu_pelaksanaan: string | null;
  tempat: string | null;
  anggaran: string | null;
  penanggung_jawab: string | null;
  narasumber: string | null;
  metode: string | null;
  output_kegiatan: string | null;
}

export interface HybridRequest {
  session_id: string | null;
  message: string;
  options?: {
    force_generate?: boolean;
    model_preference?: string;
  };
}

export interface HybridResponse {
  session_id: string;
  type: "chat" | "generate";
  message: string;
  state: SessionState;
  extracted_data?: TORData | null;
  tor_document?: TORDocument | null;
  escalation_info?: EscalationInfo | null;
  cached?: boolean;
}

export interface ComponentHealth {
  status: "up" | "down" | "degraded";
  details?: Record<string, unknown>;
  latency_ms?: number;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  uptime_seconds: number;
  components: Record<string, ComponentHealth>;
}

export interface ModelInfo {
  id: string;
  type: "local" | "gemini";
  provider: string;
  status: "available" | "offline";
}

export interface ModelsResponse {
  models: ModelInfo[];
  default_chat_mode: string;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: string | null;
  retry_after_seconds?: number | null;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

export interface TORStyle {
  id: string;
  name: string;
  description: string;
  is_default: boolean;
  is_active: boolean;
  sections: Record<string, unknown>[];
  config: Record<string, unknown>;
}

export interface GenerateDocRequest {
  file: File;
  context?: string;
  style_id?: string;
}

export interface GenerateResponse {
  session_id: string;
  message: string;
  tor_document: TORDocument;
  cached: boolean;
}
