# Task 14 — ToolCallIndicator Component

## Deskripsi

Membuat komponen React `ToolCallIndicator` yang menampilkan status real-time saat AI sedang menggunakan tool. User bisa melihat tool apa yang dipanggil, arguments-nya, status eksekusi, dan hasilnya — semuanya secara real-time selama streaming.

---

## Tujuan Teknis

- Menampilkan indikator visual saat tool sedang running (dengan animasi)
- Menampilkan nama tool dan arguments yang dipanggil
- Menampilkan status: running (spinner), success (centang + jumlah hasil), error (silang + pesan)
- Multiple tool calls dalam satu turn — ditampilkan sebagai list
- Animasi smooth untuk transisi status (running → success/error)
- Empty state: tidak render apa pun jika tidak ada tool calls

---

## Scope

### Termasuk

- Membuat `app_frontend/src/components/chat/ToolCallIndicator.tsx`
- Props:
  ```typescript
  interface ToolCallIndicatorProps {
    toolCalls: ToolCallEvent[];
  }
  ```

- Struktur komponen:
  ```
  ToolCallIndicator (container)
  ├── [Jika toolCalls kosong] → return null
  └── [Jika ada toolCalls]
      └── List of ToolCallItem
          ├── Icon (🔍 untuk web_search)
          ├── Tool name + args
          ├── Status badge
          └── [Jika success] Result count
  ```

- Setiap `ToolCallItem` menampilkan:
  - **Icon**: berdasarkan nama tool (🔍 web_search, ⚙️ default)
  - **Nama tool**: `web_search`
  - **Arguments**: ditampilkan sebagai tag ringkas (contoh: `query: "AI Indonesia"`)
  - **Status badge**:
    - `running`: Spinner animasi + text "Mencari informasi..."
    - `success`: ✅ Centang hijau + "Mendapatkan N hasil"
    - `error`: ❌ Silang merah + pesan error
  - Animasi: fade-in saat muncul, spinner untuk running

- Styling dengan Tailwind CSS (mengikuti theme yang sudah ada):
  - Container: background muted (`bg-muted/50`), rounded (`rounded-lg`), padding (`p-3`), border left accent (`border-l-4 border-blue-500`)
  - Running: border blue, spinner animation
  - Success: border green
  - Error: border red

### Tidak Termasuk

- Integrasi ke ChatContainer (Task 16)
- Tool toggle settings UI (Task 16)
- i18n translations (Task 17)

---

## Langkah Implementasi

### Langkah 1: Buat `ToolCallIndicator.tsx`

```tsx
import React from "react";
import type { ToolCallEvent } from "@/types/api";

interface ToolCallIndicatorProps {
  toolCalls: ToolCallEvent[];
}

export function ToolCallIndicator({ toolCalls }: ToolCallIndicatorProps) {
  if (toolCalls.length === 0) return null;

  return (
    <div className="space-y-2 my-3">
      {toolCalls.map((call, index) => (
        <ToolCallItem key={`${call.tool}-${index}`} call={call} />
      ))}
    </div>
  );
}

// ========== ToolCallItem ==========

interface ToolCallItemProps {
  call: ToolCallEvent;
}

function getToolIcon(tool: string): string {
  const icons: Record<string, string> = {
    web_search: "🔍",
    web_scrape: "🌐",
    calculator: "🧮",
    current_datetime: "🕐",
    weather: "🌤️",
  };
  return icons[tool] || "⚙️";
}

function getStatusConfig(status: ToolCallEvent["status"]) {
  switch (status) {
    case "running":
      return {
        borderColor: "border-l-blue-500",
        bgColor: "bg-blue-50 dark:bg-blue-950/30",
        icon: <Spinner />,
        text: "Mencari informasi...",
        textColor: "text-blue-600 dark:text-blue-400",
      };
    case "success":
      return {
        borderColor: "border-l-green-500",
        bgColor: "bg-green-50 dark:bg-green-950/30",
        icon: <span>✅</span>,
        text: `Mendapatkan ${call.resultCount ?? 0} hasil`,
        textColor: "text-green-600 dark:text-green-400",
      };
    case "error":
      return {
        borderColor: "border-l-red-500",
        bgColor: "bg-red-50 dark:bg-red-950/30",
        icon: <span>❌</span>,
        text: call.error || "Pencarian gagal",
        textColor: "text-red-600 dark:text-red-400",
      };
  }
}

function ToolCallItem({ call }: ToolCallItemProps) {
  const config = getStatusConfig(call.status);

  // Format args untuk display
  const argsEntries = Object.entries(call.args || {});
  const argsText = argsEntries
    .map(([key, val]) => `${key}: "${val}"`)
    .join(", ");

  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg border-l-4 ${config.borderColor} ${config.bgColor} transition-all duration-300`}
    >
      {/* Icon */}
      <span className="text-lg mt-0.5">{getToolIcon(call.tool)}</span>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Tool name + args */}
        <div className="text-sm font-medium text-foreground">
          <span className="font-mono text-xs">{call.tool}</span>
          {argsText && (
            <span className="text-muted-foreground ml-2 text-xs">
              ({argsText})
            </span>
          )}
        </div>

        {/* Status */}
        <div className={`flex items-center gap-1.5 mt-1 text-sm ${config.textColor}`}>
          {config.icon}
          <span>{config.text}</span>
        </div>
      </div>
    </div>
  );
}

// ========== Spinner Component ==========

function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4 text-blue-500"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
```

### Langkah 2: Validasi

```tsx
// Test render berbagai status
const testCases = [
  { tool: "web_search", args: { query: "AI Indonesia" }, status: "running" },
  { tool: "web_search", args: { query: "AI Indonesia" }, status: "success", resultCount: 5 },
  { tool: "web_search", args: { query: "AI Indonesia" }, status: "error", error: "Timeout" },
];

// Test empty
<ToolCallIndicator toolCalls={[]} />  // → null (tidak render)

// Test with calls
<ToolCallIndicator toolCalls={testCases} />
// → Render 3 items dengan status berbeda
```

---

## Output yang Diharapkan

```
app_frontend/src/components/chat/
├── ToolCallIndicator.tsx   # Baru
└── ... (existing)
```

- Komponen `ToolCallIndicator` siap digunakan
- Tool calls ditampilkan dengan status real-time dan animasi
- Empty state: tidak render apa pun

---

## Dependencies

- **Task 12 (Frontend Tool Types)** — `ToolCallEvent` type

---

## Acceptance Criteria

### Functional
- [ ] Komponen tidak render apa pun jika `toolCalls` kosong
- [ ] Setiap tool call menampilkan icon yang sesuai (🔍 untuk web_search)
- [ ] Setiap tool call menampilkan nama tool (font-mono)
- [ ] Setiap tool call menampilkan arguments sebagai tag ringkas
- [ ] Status "running" menampilkan animasi spinner + text "Mencari informasi..."
- [ ] Status "success" menampilkan ✅ + "Mendapatkan N hasil"
- [ ] Status "error" menampilkan ❌ + pesan error

### Styling
- [ ] Container memiliki border-left accent (blue untuk running, green untuk success, red untuk error)
- [ ] Background berbeda per status (blue/green/red dengan opacity rendah)
- [ ] Animasi spinner untuk status running
- [ ] Transisi smooth saat status berubah
- [ ] Dark mode support (menggunakan dark: prefix)

### Edge Cases
- [ ] Tool tanpa arguments → args tidak ditampilkan
- [ ] Tool dengan banyak arguments → semua ditampilkan
- [ ] Multiple tool calls → ditampilkan sebagai list vertikal
- [ ] resultCount = 0 → "Mendapatkan 0 hasil"

---

## Estimasi

**Medium** (~1.5 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Implementasi ToolCallIndicator container | 15 menit |
| Implementasi ToolCallItem | 30 menit |
| Implementasi Spinner component | 10 menit |
| Styling & dark mode | 20 menit |
| Validasi & testing | 15 menit |
