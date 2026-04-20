import { apiGet } from "./client";
import type { ModelsResponse } from "@/types/api";

export async function listModels(): Promise<ModelsResponse> {
  return apiGet<ModelsResponse>("/models");
}
