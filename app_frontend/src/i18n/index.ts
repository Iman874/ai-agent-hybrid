import { useUIStore } from "@/stores/ui-store";
import type { Language } from "./types";
import id from "./locales/id";
import en from "./locales/en";

const locales: Record<Language, Record<string, string>> = { id, en };

export function useTranslation() {
  const language = useUIStore(s => s.language);
  const setLanguage = useUIStore(s => s.setLanguage);

  function t(key: string, params?: Record<string, string | number>): string {
    let text = locales[language]?.[key] ?? locales.id[key] ?? key;
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        text = text.replace(`{${k}}`, String(v));
      });
    }
    return text;
  }

  return { t, language, setLanguage };
}
