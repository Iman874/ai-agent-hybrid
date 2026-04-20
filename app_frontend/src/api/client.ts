import { API_BASE_URL } from "@/lib/constants";
import type { ErrorResponse } from "@/types/api";

export class ApiError extends Error {
  code: string;
  details?: string;
  retryAfterSeconds?: number;

  constructor(error: ErrorResponse["error"]) {
    super(error.message);
    this.code = error.code;
    this.details = error.details ?? undefined;
    this.retryAfterSeconds = error.retry_after_seconds ?? undefined;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    try {
      const body = await response.json() as ErrorResponse;
      throw new ApiError(body.error);
    } catch (e) {
      if (e instanceof ApiError) throw e;
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }
  return response.json() as Promise<T>;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  return handleResponse<T>(response);
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response);
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
  });
  return handleResponse<T>(response);
}

export async function apiPostFormData<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<T>(response);
}
