import { apiGet, apiPost, apiDelete } from "./client";
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
