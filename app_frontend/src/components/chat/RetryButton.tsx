import { RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/i18n";

interface Props {
  onClick: () => void;
}

export function RetryButton({ onClick }: Props) {
  const { t } = useTranslation();
  return (
    <Button
      variant="ghost"
      size="sm"
      className="text-destructive hover:text-destructive h-7 text-xs px-2"
      onClick={onClick}
    >
      <RotateCcw className="w-3 h-3 mr-1" />
      {t("chat.retry")}
    </Button>
  );
}
