# Task 3: Restore TOR Document di loadSession

## 1. Judul Task
Pulihkan `torDocument` saat user membuka session lama yang sudah memiliki hasil generate TOR.

## 2. Deskripsi
Saat user klik session di sidebar yang sudah menghasilkan TOR, `loadSession()` memuat chat history tetapi **tidak memulihkan** `torDocument`. `SessionDetailResponse` sudah memiliki field `generated_tor: string | null`, tapi tidak pernah di-mapping ke `chat-store.torDocument`. Akibatnya `TORPreview` tidak tampil saat membuka session lama.

## 3. Tujuan Teknis
- Tambahkan action `setTorDocument()` dan `clearTorDocument()` di `chat-store`
- Di `loadSession()`, baca `detail.generated_tor` dan pulihkan ke `chat-store.torDocument`
- Jika session tidak punya TOR, pastikan `torDocument` di-clear

## 4. Scope
### Yang dikerjakan
- Tambah 2 action baru di `src/stores/chat-store.ts`
- Modifikasi `loadSession()` di `src/stores/session-store.ts`

### Yang tidak dikerjakan
- Tidak mengubah backend atau API
- Tidak mengubah `TORPreview.tsx` (sudah berfungsi jika data ada)
- Tidak mengubah `ChatArea.tsx` (sudah render `TORPreview` jika `torDocument && activeSessionId`)

## 5. Langkah Implementasi

### Step 1: Tambah actions di `src/stores/chat-store.ts`

Tambah ke interface `ChatStore`:
```typescript
setTorDocument: (doc: TORDocument) => void;
clearTorDocument: () => void;
```

Tambah implementasi:
```typescript
setTorDocument: (doc) => set({ torDocument: doc }),
clearTorDocument: () => set({ torDocument: null }),
```

### Step 2: Modifikasi `loadSession()` di `src/stores/session-store.ts`

Setelah `useChatStore.getState().loadMessages(messages)`, tambahkan:

```typescript
// Restore TOR document jika session sudah punya hasil generate
if (detail.generated_tor) {
  useChatStore.getState().setTorDocument({
    content: detail.generated_tor,
    metadata: {
      generated_by: "restored",
      mode: "restored",
      word_count: detail.generated_tor.split(/\s+/).length,
      generation_time_ms: 0,
      has_assumptions: false,
      prompt_tokens: 0,
      completion_tokens: 0,
    },
  });
} else {
  useChatStore.getState().clearTorDocument();
}
```

### Step 3: Pastikan `clearMessages()` juga clear TOR
Verifikasi bahwa `clearMessages()` sudah men-set `torDocument: null`. Ini sudah benar di kode existing:

```typescript
clearMessages: () => set({
  messages: [],
  torDocument: null,  // ← sudah ada
  // ...
}),
```

### Step 4: Verifikasi
1. Buat session baru → jalankan wawancara hingga generate TOR
2. Klik session lain → `TORPreview` harus hilang
3. Kembali ke session TOR → `TORPreview` harus muncul kembali dengan konten yang benar
4. Buat session baru (tanpa TOR) → `TORPreview` harus tidak ada

## 6. Output yang Diharapkan

**Saat user klik session yang punya TOR:**
```
loadSession("abc") 
  → fetch detail → generated_tor: "# TOR Kegiatan ..."
  → setTorDocument({ content: "# TOR Kegiatan ...", metadata: {...} })
  → ChatArea render: torDocument ✓ + activeSessionId ✓ → TORPreview tampil! ✓
```

**Saat user klik session tanpa TOR:**
```
loadSession("def")
  → fetch detail → generated_tor: null
  → clearTorDocument()
  → ChatArea render: torDocument null → TORPreview tidak tampil ✓
```

## 7. Dependencies
- Task 1 (session sync — `activeSessionId` harus sudah benar agar `TORPreview` ter-render)

## 8. Acceptance Criteria
- [ ] `chat-store` memiliki action `setTorDocument(doc)` dan `clearTorDocument()`
- [ ] `loadSession()` memanggil `setTorDocument()` jika `detail.generated_tor` ada
- [ ] `loadSession()` memanggil `clearTorDocument()` jika `detail.generated_tor` null
- [ ] Buka session dengan TOR → `TORPreview` tampil dengan konten yang benar
- [ ] Buka session tanpa TOR → `TORPreview` tidak tampil
- [ ] Buat session baru → `TORPreview` tidak tampil (clear state)
- [ ] `npm run build` sukses tanpa error

## 9. Estimasi
**Low** (~45 menit)
