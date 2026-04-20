import { API_BASE_URL } from "@/lib/constants";

export async function exportDocument(
  sessionId: string,
  format: "docx" | "pdf" | "md" = "docx",
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/export/${sessionId}?format=${format}`,
  );
  if (!response.ok) throw new Error(`Export failed: ${response.statusText}`);
  return response.blob();
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
