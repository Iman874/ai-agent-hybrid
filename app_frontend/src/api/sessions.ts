import { apiGet, apiDelete } from "./client";
import type { SessionListItem, SessionDetailResponse } from "@/types/session";

export async function listSessions(limit = 50): Promise<SessionListItem[]> {
  return apiGet<SessionListItem[]>(`/sessions?limit=${limit}`);
}

export async function getSession(sessionId: string): Promise<SessionDetailResponse> {
  return apiGet<SessionDetailResponse>(`/session/${sessionId}`);
}

export async function deleteSession(sessionId: string): Promise<{ status: string }> {
  return apiDelete<{ status: string }>(`/sessions/${sessionId}`);
}
