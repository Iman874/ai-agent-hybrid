import { Button } from "@/components/ui/button";
import { FileText } from "lucide-react";
import { useGenerateStore } from "@/stores/generate-store";
import { useUIStore } from "@/stores/ui-store";
import { useTranslation } from "@/i18n";

interface ChatGeneratePromptProps {
  sessionId: string;
  status: string; // "READY_TO_GENERATE" | "ESCALATE_TO_GEMINI" | "READY"
}

export function ChatGeneratePrompt({ sessionId, status }: ChatGeneratePromptProps) {
  const { t } = useTranslation();
  const isStreaming = useGenerateStore(s => s.isStreaming);

  const handleGenerate = () => {
    const mode = status === "ESCALATE_TO_GEMINI" ? "escalation" : "standard";

    // Switch tab ke generate
    useUIStore.getState().setActiveTool("generate_doc");

    // Mulai streaming
    setTimeout(() => {
      useGenerateStore.getState().generateFromChatStream(sessionId, mode);
    }, 100);
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
