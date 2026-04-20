# Task 15: Polish & Testing — Dark Mode, Responsive, Keyboard, QA

## 1. Judul Task

Polish akhir: dark mode, responsive mobile, keyboard shortcuts, final QA

## 2. Deskripsi

Task terakhir: memastikan dark/light mode konsisten, sidebar collapse di mobile, keyboard shortcuts berfungsi, dan semua fitur terintegrasi tanpa bug.

## 3. Tujuan Teknis

- Dark mode: semua komponen konsisten
- Responsive: sidebar auto-hide di < 768px, hamburger menu
- Keyboard: Enter=kirim, Shift+Enter=newline, Esc=close dialog
- QA: semua flow tested end-to-end

## 4. Scope

**Yang dikerjakan:**
- Dark mode audit (semua components)
- Responsive breakpoints
- `src/hooks/useKeyboard.ts`
- Final QA checklist

**Yang tidak dikerjakan:**
- Mobile app (hanya web responsive)
- PWA / Service Worker

## 5. Langkah Implementasi

### 5.1 Dark Mode Audit

Pastikan SEMUA komponen menggunakan Tailwind dark mode classes:
- `bg-background`, `text-foreground` (bukan hardcoded colors)
- `bg-muted`, `text-muted-foreground`
- `border-border`
- `prose dark:prose-invert` pada markdown

Check list:
- [ ] AppLayout
- [ ] Sidebar
- [ ] Header
- [ ] ChatArea + MessageBubble
- [ ] SettingsDialog
- [ ] UploadForm + GenerateResult
- [ ] TORPreview

### 5.2 Responsive

```tsx
// AppLayout.tsx — auto-collapse sidebar on mobile
import { useEffect } from "react";

useEffect(() => {
  const mq = window.matchMedia("(max-width: 768px)");
  const handler = (e: MediaQueryListEvent) => {
    if (e.matches) useUIStore.getState().toggleSidebar(); // close
  };
  mq.addEventListener("change", handler);
  // Initial check
  if (mq.matches) useUIStore.setState({ sidebarOpen: false });
  return () => mq.removeEventListener("change", handler);
}, []);
```

Mobile: sidebar → Sheet (overlay from left):
```tsx
// For mobile: use Shadcn Sheet component
{isMobile ? (
  <Sheet open={sidebarOpen} onOpenChange={toggleSidebar}>
    <SheetContent side="left" className="w-64 p-0">
      <Sidebar />
    </SheetContent>
  </Sheet>
) : (
  <aside className={cn(...)}>
    <Sidebar />
  </aside>
)}
```

### 5.3 `src/hooks/useKeyboard.ts`

```tsx
import { useEffect } from "react";
import { useUIStore } from "@/stores/ui-store";

export function useKeyboard() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Esc = close settings
      if (e.key === "Escape") {
        useUIStore.getState().closeSettings();
      }
      // Ctrl+Shift+N = new chat
      if (e.key === "N" && e.ctrlKey && e.shiftKey) {
        e.preventDefault();
        // trigger new chat
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
}
```

### 5.4 Final QA Checklist

**Chat Flow:**
- [ ] Empty state → kirim pesan → user bubble → thinking → streaming → assistant bubble
- [ ] Multi-turn conversation berfungsi
- [ ] Markdown rendering: bold, italic, lists, code blocks
- [ ] Auto-scroll saat pesan baru

**Streaming:**
- [ ] Thinking indicator muncul/hilang
- [ ] Token-by-token text rendering
- [ ] Cursor blink selama streaming

**Retry:**
- [ ] Simulate error → error state muncul → klik retry → berhasil

**Session:**
- [ ] New chat → reset messages
- [ ] Klik session → load history
- [ ] Delete session → hilang dari list
- [ ] Session list maks 4

**Model:**
- [ ] Switch model berfungsi
- [ ] Format: `nama · provider`

**Generate:**
- [ ] Upload file → submit → result tampil
- [ ] Export DOCX/PDF/MD download berfungsi

**Settings:**
- [ ] Dialog buka/tutup
- [ ] Navigation antar section
- [ ] Theme switch (dark/light/system) berfungsi

**WebSocket:**
- [ ] Connect → streaming works
- [ ] Disconnect → reconnect otomatis
- [ ] Fallback ke HTTP jika WS gagal

**Responsive:**
- [ ] Desktop: sidebar tetap
- [ ] Mobile (< 768px): sidebar overlay
- [ ] Toggle sidebar berfungsi

**Performance:**
- [ ] `npm run build` sukses — zero errors
- [ ] Bundle size reasonable (< 500KB gzipped)
- [ ] No memory leaks (check WS cleanup)

## 6. Output yang Diharapkan

Aplikasi React fully functional yang bisa menggantikan Streamlit frontend:
- Modern, responsive, dark mode
- Streaming real-time
- Retry mechanism
- SPA behavior (zero reload)

## 7. Dependencies

- Task 01-14 (semua task sebelumnya)

## 8. Acceptance Criteria

- [ ] Semua QA checklist items ✅
- [ ] `npm run build` → zero errors
- [ ] Dark/light mode konsisten di semua halaman
- [ ] Mobile responsive berfungsi
- [ ] Keyboard shortcuts berfungsi
- [ ] No console errors di production build

## 9. Estimasi

Medium (2-3 jam)
