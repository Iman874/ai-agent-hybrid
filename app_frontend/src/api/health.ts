import { apiGet } from "./client";
import type { HealthResponse } from "@/types/api";

export async function checkHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}
