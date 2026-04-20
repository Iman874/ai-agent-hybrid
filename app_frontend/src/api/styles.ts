import { apiGet, apiPost, apiDelete, apiPut, apiPostFormData } from "./client";
import type { TORStyle } from "@/types/api";

export async function listStyles(): Promise<TORStyle[]> {
  return apiGet<TORStyle[]>("/styles/");
}

export async function getActiveStyle(): Promise<TORStyle> {
  return apiGet<TORStyle>("/styles/active");
}

export async function activateStyle(styleId: string): Promise<void> {
  await apiPost(`/styles/${styleId}/activate`, {});
}

export async function deleteStyle(styleId: string): Promise<void> {
  await apiDelete(`/styles/${styleId}`);
}

export async function duplicateStyle(styleId: string, newName: string): Promise<TORStyle> {
  return apiPost<TORStyle>(`/styles/${styleId}/duplicate`, { new_name: newName });
}

export async function updateStyle(styleId: string, updates: Record<string, unknown>): Promise<TORStyle> {
  return apiPut<TORStyle>(`/styles/${styleId}`, updates);
}

export async function createStyle(data: Record<string, unknown>): Promise<TORStyle> {
  return apiPost<TORStyle>(`/styles/`, data);
}

export async function extractStyle(file: File): Promise<Record<string, unknown>> {
  const formData = new FormData();
  formData.append("file", file);
  return apiPostFormData<Record<string, unknown>>(`/styles/extract`, formData);
}
