# Task 07: StyleReadonlyView Component — Tabel Seksi + Metrik Config

## 1. Judul Task

Membuat komponen read-only yang menampilkan detail style: tabel struktur seksi dan metrik gaya penulisan

## 2. Deskripsi

Setelah user memilih style di `StyleSelector`, komponen ini menampilkan detail lengkap style tersebut: tabel seksi (No, Nama, Tipe, Format, Min Paragraf) dan grid metrik konfigurasi (Bahasa, Formalitas, Voice, Min/Max Kata, Penomoran). Untuk style default, ditampilkan label "read-only".

## 3. Tujuan Teknis

- `src/components/settings/StyleReadonlyView.tsx`
- Tabel seksi menggunakan HTML table sederhana (styled Tailwind)
- Grid metrik menggunakan card kecil (mirip `st.metric` di Streamlit)
- Collapsible instruksi kustom

## 4. Scope

**Yang dikerjakan:**
- `StyleReadonlyView.tsx` — tabel + metrik + instruksi kustom

**Yang tidak dikerjakan:**
- Edit form (task 09)
- Action buttons (task 08)

## 5. Langkah Implementasi

### 5.1 Buat `src/components/settings/StyleReadonlyView.tsx`

```tsx
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "@/i18n";
import type { TORStyle } from "@/types/api";

interface Props {
  style: TORStyle;
}

export function StyleReadonlyView({ style }: Props) {
  const { t } = useTranslation();
  const [showInstructions, setShowInstructions] = useState(false);
  const config = style.config;
  const sections = style.sections;

  return (
    <div className="space-y-6">
      {/* Default badge */}
      {style.is_default && (
        <p className="text-xs text-muted-foreground italic">
          {t("format.default_readonly")}
        </p>
      )}

      {/* Section Table */}
      <div>
        <h4 className="text-sm font-semibold mb-2">{t("format.sections_title")}</h4>
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left px-3 py-2 font-medium">No.</th>
                <th className="text-left px-3 py-2 font-medium">Nama Seksi</th>
                <th className="text-left px-3 py-2 font-medium">Tipe</th>
                <th className="text-left px-3 py-2 font-medium">Format</th>
                <th className="text-left px-3 py-2 font-medium">Min. Paragraf</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {sections.map((sec, i) => (
                <tr key={i}>
                  <td className="px-3 py-2">{i + 1}</td>
                  <td className="px-3 py-2 font-medium">{sec.title}</td>
                  <td className="px-3 py-2">
                    <span className={sec.required ? "text-primary" : "text-muted-foreground"}>
                      {sec.required ? t("format.required") : t("format.optional")}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">{sec.format_hint || "-"}</td>
                  <td className="px-3 py-2">{sec.min_paragraphs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Config Metrics Grid */}
      <div>
        <h4 className="text-sm font-semibold mb-2">{t("format.writing_style")}</h4>
        <div className="grid grid-cols-3 gap-3">
          <MetricCard label={t("format.metric_language")} value={config.language?.toUpperCase()} />
          <MetricCard label={t("format.metric_formality")} value={config.formality?.replace("_", " ")} />
          <MetricCard label={t("format.metric_voice")} value={config.voice} />
          <MetricCard label={t("format.metric_min_words")} value={String(config.min_word_count)} />
          <MetricCard label={t("format.metric_max_words")} value={String(config.max_word_count)} />
          <MetricCard label={t("format.metric_numbering")} value={config.numbering_style} />
        </div>
      </div>

      {/* Custom Instructions collapsible */}
      <div>
        <button
          className="text-sm text-muted-foreground flex items-center gap-1 hover:text-foreground transition"
          onClick={() => setShowInstructions(!showInstructions)}
        >
          {showInstructions ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          {t("format.custom_instruction_view")}
        </button>
        {showInstructions && (
          <div className="mt-2 text-sm bg-muted/30 rounded-md p-3 whitespace-pre-wrap">
            {config.custom_instructions || t("format.custom_instruction_empty")}
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-muted/40 rounded-lg p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-semibold capitalize mt-0.5">{value || "-"}</p>
    </div>
  );
}
```

## 6. Output yang Diharapkan

Style detail view menampilkan:
1. Tabel seksi yang rapi (header grey, rows bordered)
2. Grid 3col metrik: Bahasa=ID, Formalitas=Formal, Voice=Active, dll.
3. Collapsible "Lihat Instruksi Kustom"

## 7. Dependencies

- Task 01 (i18n)
- Task 05 (TORStyleSection, TORStyleConfig types)

## 8. Acceptance Criteria

- [ ] Tabel seksi menampilkan semua sections dari style
- [ ] Metrik grid menampilkan 6 config properties
- [ ] Instruksi kustom bisa di-expand/collapse
- [ ] Style default menampilkan label "read-only"
- [ ] Dark mode kompatibel

## 9. Estimasi

Medium (1.5 jam)
