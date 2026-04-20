import { apiPost } from "./client";
import type { HybridRequest, HybridResponse } from "@/types/api";

export async function sendMessage(req: HybridRequest): Promise<HybridResponse> {
  return apiPost<HybridResponse>("/hybrid", req);
}
