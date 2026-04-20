import { Bot } from "lucide-react";

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-5">
      <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center">
        <Bot className="w-8 h-8 opacity-50" />
      </div>
      <div className="text-center space-y-1.5 max-w-sm">
        <h2 className="text-lg font-medium text-foreground">Ceritakan kebutuhan TOR Anda</h2>
        <p className="text-sm">
          Saya dapat membantu menyusun Term of Reference untuk kegiatan Anda dengan lebih cepat dan terstruktur.
        </p>
      </div>
    </div>
  );
}
