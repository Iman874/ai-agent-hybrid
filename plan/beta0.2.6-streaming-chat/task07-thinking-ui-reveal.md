# Task 7: Chat UI Reasoning Panel — Hide/Show + Expand/Collapse

## Deskripsi

Menambahkan kemampuan di UI chat agar reasoning (thinking output) tidak hanya tampil sementara saat streaming, tetapi juga bisa:
- disembunyikan (hide/show), dan
- diperluas/diciutkan (expand/collapse),

pada pesan assistant yang sudah selesai.

Tujuan utamanya: user tetap melihat jawaban final seperti biasa, tetapi punya opsi untuk membuka reasoning jika dibutuhkan.

## Tujuan Teknis

- Reasoning tetap direkam selama stream berjalan
- Reasoning disimpan ke message assistant setelah stream selesai
- Reasoning default dalam keadaan tersembunyi atau collapsed (sesuai UX)
- User bisa toggle `Tampilkan reasoning` / `Sembunyikan reasoning`
- User bisa toggle `Perluas` / `Ciutkan` saat reasoning panjang
- Tidak mengubah kontrak event SSE yang sudah ada (`thinking_start`, `thinking`, `thinking_end`, `token`, `done`)

## Scope

**Dikerjakan:**
- Frontend chat store: persist reasoning text per message assistant
- UI message bubble: panel reasoning yang bisa hide/show + expand/collapse
- Streaming UX: reasoning tetap bisa di-hide saat stream berjalan
- Backward compatible untuk provider tanpa thinking (Gemini)

**Tidak dikerjakan:**
- Perubahan format API backend
- Redaksi/filtrasi reasoning di backend
- Perubahan alur generate document

## File Target

- `app_frontend/src/types/chat.ts`
- `app_frontend/src/stores/chat-store.ts`
- `app_frontend/src/components/chat/MessageBubble.tsx`
- `app_frontend/src/components/chat/ThinkingIndicator.tsx`
- `app_frontend/src/components/chat/ChatArea.tsx`
- `app_frontend/src/i18n/locales/id.ts`
- `app_frontend/src/i18n/locales/en.ts`

## Langkah Implementasi

### Step 1: Persist reasoning ke message assistant

Di store chat, reasoning saat stream (`stream.thinkingText`) saat ini bersifat sementara. Tambahkan mekanisme agar pada event `done`, reasoning dipindahkan/tersimpan ke message assistant final.

Contoh atribut message assistant:

```ts
thinkingContent?: string;
thinkingVisible?: boolean;   // default false
thinkingExpanded?: boolean;  // default false
```

### Step 2: Tambah actions untuk toggle reasoning UI

Tambahkan actions di store, misalnya:

```ts
toggleThinkingVisible: (messageId: string) => void;
toggleThinkingExpanded: (messageId: string) => void;
```

Behavior:
- `toggleThinkingVisible` mengatur panel tampil/sembunyi
- `toggleThinkingExpanded` mengatur mode ringkas/penuh

### Step 3: Reasoning panel di MessageBubble

Di `MessageBubble` (khusus role assistant), render panel reasoning jika message memiliki `thinkingContent`.

UI minimal:
- Tombol `Lihat reasoning` saat hidden
- Tombol `Sembunyikan reasoning` saat visible
- Tombol `Perluas` / `Ciutkan` saat visible
- Mode collapsed pakai max height + fade gradient

### Step 4: Integrasi dengan streaming indicator

Selama stream berjalan:
- `ThinkingIndicator` tetap dipakai untuk live feedback
- user tetap bisa menyembunyikan tampilan reasoning live (opsional via toggle global stream)
- meskipun disembunyikan, token reasoning tetap dikumpulkan di state

Setelah stream `done`:
- reasoning live dipindahkan ke message final assistant
- stream state di-reset seperti sekarang

### Step 5: Compatibility provider

- Jika provider tidak kirim thinking (`Gemini`):
  - `thinkingContent` kosong
  - tombol reasoning tidak ditampilkan
- Jika provider kirim thinking (`Ollama`):
  - panel reasoning tersedia

### Step 6: i18n

Tambahkan key teks:
- `chat.reasoning_show`
- `chat.reasoning_hide`
- `chat.reasoning_expand`
- `chat.reasoning_collapse`
- `chat.reasoning_title`

## Output yang Diharapkan

Contoh flow:

1. User kirim pesan
2. Assistant masuk fase thinking (bisa tampil/sembunyi)
3. Assistant streaming jawaban final
4. Setelah done, bubble assistant final tetap tampil seperti biasa
5. User bisa klik `Lihat reasoning` untuk membuka reasoning panel
6. User bisa `Perluas`/`Ciutkan` reasoning

## Acceptance Criteria

- [ ] Reasoning bisa di-hide/show pada message assistant final
- [ ] Reasoning bisa di-expand/collapse pada konten panjang
- [ ] Jawaban final tetap jadi fokus utama (tidak terganggu)
- [ ] Reasoning tetap terekam walau panel sedang disembunyikan
- [ ] Tidak ada error untuk provider tanpa thinking (Gemini)
- [ ] TypeScript build tetap clean
- [ ] UX mobile dan desktop tetap rapi

## Estimasi

Medium (2-4 jam)

## Dependencies

- Task 1-6 (streaming chat SSE) sudah selesai
