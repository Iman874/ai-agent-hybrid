import { apiPostFormData } from "./client";
import type { GenerateResponse } from "@/types/api";

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
