import { Button } from "@/components/ui/button";
import { FileText } from "lucide-react";
import { useGenerateStore } from "@/stores/generate-store";
import { useModelStore } from "@/stores/model-store";
import { useTranslation } from "@/i18n";

interface ChatGeneratePromptProps {
  sessionId: string;
  status: string;
  completenessScore?: number;
}

export function ChatGeneratePrompt({
  sessionId,
  status,
  completenessScore,
}: ChatGeneratePromptProps) {
  const { t } = useTranslation();
  const isStreaming = useGenerateStore(s => s.isStreaming);

  const handleGenerate = () => {
    const _ = completenessScore;
    const __ = status;
    const mode = "standard";

    // Gunakan chatMode untuk menentukan generator TOR
    // local → ollama, gemini → gemini, zen → zen
    const chatMode = useModelStore.getState().chatMode;
    const generator = chatMode === "gemini" ? "gemini" : chatMode === "zen" ? "zen" : "ollama";

    // Mulai streaming dengan generator sesuai chatMode
    useGenerateStore.getState().generateFromChatStream(sessionId, mode, generator);
  };

  if (isStreaming) return null; // Jangan tampilkan jika sudah streaming

  return (
    <div className="flex justify-center py-3">
      <Button
        variant="default"
        size="sm"
        onClick={handleGenerate}
        className="gap-2"
      >
        <FileText className="w-4 h-4" />
        {t("chat.generate_now") || "Buat TOR Sekarang"}
      </Button>
    </div>
  );
}
