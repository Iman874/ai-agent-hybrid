import { useState } from "react";
import { UploadForm } from "./UploadForm";
import { GenerateResult } from "./GenerateResult";
import type { GenerateResponse } from "@/types/api";

export function GenerateContainer() {
  const [result, setResult] = useState<GenerateResponse | null>(null);

  if (result) {
    return <GenerateResult result={result} onBack={() => setResult(null)} />;
  }

  return <UploadForm onResult={setResult} />;
}
