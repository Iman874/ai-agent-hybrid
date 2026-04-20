import { useGenerateStore } from "@/stores/generate-store";
import { UploadForm } from "./UploadForm";
import { GenerateResult } from "./GenerateResult";
import { GenerateHistory } from "./GenerateHistory";
import { Loader2 } from "lucide-react";
import { useTranslation } from "@/i18n";

export function GenerateContainer() {
  const { t } = useTranslation();
  const isGenerating = useGenerateStore(s => s.isGenerating);
  const lastResponse = useGenerateStore(s => s.lastGenerateResponse);
  const activeResult = useGenerateStore(s => s.activeResult);
  const isLoadingResult = useGenerateStore(s => s.isLoadingResult);
  const clearActiveResult = useGenerateStore(s => s.clearActiveResult);
  const clearLastResponse = useGenerateStore(s => s.clearLastResponse);

  // View: Loading detail from history
  if (isLoadingResult) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  // View: Showing result from history click
  if (activeResult) {
    return (
      <GenerateResult
        resultFromHistory={activeResult}
        onBack={clearActiveResult}
      />
    );
  }

  // View: Showing immediate generate result
  if (lastResponse) {
    return (
      <GenerateResult
        result={lastResponse}
        onBack={clearLastResponse}
      />
    );
  }

  // View: Generating spinner
  if (isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-sm">{t("generate.processing")}</p>
      </div>
    );
  }

  // View: Idle — upload form + history
  return (
    <div className="space-y-8 pb-8">
      <UploadForm />
      <div className="max-w-3xl mx-auto px-4 sm:px-8">
        <GenerateHistory />
      </div>
    </div>
  );
}
