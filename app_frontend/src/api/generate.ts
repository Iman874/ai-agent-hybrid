import { apiPostFormData, apiGet, apiDelete } from "./client";
import type { GenerateResponse } from "@/types/api";
import type { DocGenListItem, DocGenDetail } from "@/types/generate";

export async function generateFromDocument(
  file: File,
  context?: string,
  styleId?: string,
): Promise<GenerateResponse> {
  const formData = new FormData();
  formData.append("file", file);

  if (context) formData.append("context", context);
  if (styleId) formData.append("style_id", styleId);

  return apiPostFormData<GenerateResponse>("/generate/from-document", formData);
}

export async function listGenerations(limit = 30): Promise<DocGenListItem[]> {
  return apiGet<DocGenListItem[]>(`/generate/history?limit=${limit}`);
}

export async function getGeneration(id: string): Promise<DocGenDetail> {
  return apiGet<DocGenDetail>(`/generate/${id}`);
}

export async function deleteGeneration(id: string): Promise<void> {
  await apiDelete(`/generate/${id}`);
}
