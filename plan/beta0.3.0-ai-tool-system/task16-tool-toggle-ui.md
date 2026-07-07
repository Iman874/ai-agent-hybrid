# Task 16 — Tool Toggle UI & ChatContainer Integration

## Deskripsi

Menambahkan toggle switch di frontend settings yang memungkinkan user mengaktifkan atau menonaktifkan tool calling, dan mengintegrasikan `ToolCallIndicator` ke `ChatContainer` agar tool status muncul di chat area.

---

## Tujuan Teknis

- User bisa mengaktifkan/menonaktifkan tool calling dari settings panel
- `ToolCallIndicator` muncul di chat area saat tool sedang digunakan
- Pilihan user tersimpan di `tool-store` dan dikirim ke backend via request options
- Tool indicator muncul di antara pesan user dan response AI (sebelum streaming content)
- Toggle disabled jika tidak ada tool yang terdaftar (tool-store.tools kosong)

---

## Scope

### Termasuk

- Modifikasi `ChatContainer.tsx` (cari file yang sudah ada):
  - Import `ToolCallIndicator` dan `useToolStore`
  - Render `ToolCallIndicator` di atas area streaming response:
    ```tsx
    // Di dalam ChatContainer, sebelum render streaming content
    {activeToolCalls.length > 0 && (
      <div className="px-4 py-2">
        <ToolCallIndicator toolCalls={activeToolCalls} />
      </div>
    )}
    ```
  - Tool indicator hanya muncul saat ada `activeToolCalls`

- Modifikasi settings panel (cari file settings yang sudah ada, misal `SettingsPanel.tsx` atau `ChatSettings.tsx`):
  - Tambah toggle switch:
    ```tsx
    <div className="flex items-center justify-between py-3">
      <div className="space-y-0.5">
        <Label className="text-sm font-medium">
          Izinkan AI mencari informasi di internet
        </Label>
        <p className="text-xs text-muted-foreground">
          AI bisa mencari data real-time dari web jika diperlukan
        </p>
      </div>
      <Switch
        checked={toolsEnabled}
        onCheckedChange={(value) => setToolsEnabled(value)}
        disabled={tools.length === 0}
        aria-label="Toggle internet search"
      />
    </div>
    ```
  - Toggle terhubung ke `toolStore.toolsEnabled`
  - Tampilkan status: "Aktif" / "Nonaktif" di samping toggle
  - Jika tools tidak tersedia (toolStore.tools kosong), toggle disabled + tooltip "Tidak ada tool yang tersedia"

- Update `chat-store.ts`:
  - `sendMessage()` sudah membaca `toolsEnabled` dari tool-store (Task 15)

### Tidak Termasuk

- ToolCallIndicator component (Task 14)
- ChatStore tool events (Task 15)
- i18n translations (Task 17)

---

## Langkah Implementasi

### Langkah 1: Cari file settings panel

Cari file settings di `app_frontend/src/components/` — kemungkinan `SettingsPanel.tsx`, `ChatSettings.tsx`, atau di dalam `ChatContainer.tsx` sendiri.

### Langkah 2: Tambah toggle di settings panel

```tsx
// Contoh implementasi di SettingsPanel.tsx
import { Switch } from "@/components/ui/switch";  // atau komponen switch yang sudah ada
import { Label } from "@/components/ui/label";
import { useToolStore } from "@/stores/tool-store";

export function SettingsPanel() {
  const { tools, toolsEnabled, setToolsEnabled } = useToolStore();
  const hasTools = tools.length > 0;

  return (
    <div className="space-y-4">
      {/* ... existing settings ... */}
      
      {/* Tool Toggle */}
      <div className="flex items-center justify-between py-3 border-b">
        <div className="space-y-0.5">
          <Label className="text-sm font-medium">
            Izinkan AI mencari informasi di internet
          </Label>
          <p className="text-xs text-muted-foreground">
            {hasTools
              ? "AI bisa mencari data real-time dari web jika diperlukan"
              : "Tidak ada tool yang tersedia"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {toolsEnabled ? "Aktif" : "Nonaktif"}
          </span>
          <Switch
            checked={toolsEnabled}
            onCheckedChange={setToolsEnabled}
            disabled={!hasTools}
          />
        </div>
      </div>
      
      {/* ... existing settings ... */}
    </div>
  );
}
```

### Langkah 3: Update ChatContainer

```tsx
// Di ChatContainer.tsx
import { ToolCallIndicator } from "@/components/chat/ToolCallIndicator";
import { useToolStore } from "@/stores/tool-store";

export function ChatContainer() {
  const { activeToolCalls } = useToolStore();

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {/* ... existing message list ... */}
        
        {/* Tool indicator — muncul sebelum streaming content */}
        {activeToolCalls.length > 0 && (
          <div className="px-4 py-2">
            <ToolCallIndicator toolCalls={activeToolCalls} />
          </div>
        )}
        
        {/* Streaming content */}
        {/* ... existing streaming render ... */}
      </div>
      
      {/* Input area */}
      {/* ... existing input ... */}
    </div>
  );
}
```

### Langkah 4: Validasi

```typescript
// Test toggle behavior
import { useToolStore } from "@/stores/tool-store";

// Initial state
console.log(useToolStore.getState().toolsEnabled); // true

// Toggle off
useToolStore.getState().setToolsEnabled(false);
console.log(useToolStore.getState().toolsEnabled); // false

// Toggle on
useToolStore.getState().setToolsEnabled(true);
console.log(useToolStore.getState().toolsEnabled); // true

// Test disabled state (no tools)
// Jika tools.length === 0, Switch harus disabled
```

---

## Output yang Diharapkan

- Settings panel memiliki toggle "Izinkan AI mencari informasi di internet"
- `ToolCallIndicator` muncul di `ChatContainer` saat tool aktif
- Pilihan user dikirim ke backend via `tools_enabled`

---

## Dependencies

- **Task 12 (Frontend Tool Types)** — tool-store
- **Task 14 (ToolCallIndicator)** — komponen indicator
- **Task 15 (ChatStore Tool Events)** — integrasi store

---

## Acceptance Criteria

### Settings Toggle
- [ ] Settings panel memiliki toggle "Izinkan AI mencari informasi di internet"
- [ ] Toggle terhubung ke `toolStore.toolsEnabled`
- [ ] Status "Aktif"/"Nonaktif" ditampilkan di samping toggle
- [ ] Toggle disabled jika `tools.length === 0`
- [ ] Tooltip/deskripsi berubah jika tidak ada tool tersedia

### ChatContainer Integration
- [ ] `ToolCallIndicator` dirender di ChatContainer
- [ ] Tool indicator hanya muncul saat `activeToolCalls.length > 0`
- [ ] Tool indicator muncul di antara pesan dan streaming content
- [ ] Posisi indicator konsisten di semua layout

### Data Flow
- [ ] `toolsEnabled` dari tool-store dikirim ke backend via request options
- [ ] Toggle off → backend tidak mengirim tool specs ke LLM

---

## Estimasi

**Low** (~1 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Cari & identifikasi file settings | 10 menit |
| Implementasi toggle di settings | 25 menit |
| Update ChatContainer | 15 menit |
| Validasi & testing | 10 menit |
