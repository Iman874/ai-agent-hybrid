# Task 6: Testing, Edge Cases & Polish

## Deskripsi

Verifikasi end-to-end streaming chat, handle edge cases, dan pastikan semua komponen bekerja bersama tanpa regresi.

## Tujuan Teknis

- End-to-end test: user ketik → token muncul real-time → done
- Edge case: timeout, disconnect, provider switch, empty response
- Build verification: `npm run build` dan `uvicorn` clean
- Update plan-design checklist

## Scope

**Dikerjakan:**
- End-to-end testing manual
- Fix bug yang ditemukan saat testing
- Timeout & disconnect handling
- Provider switching test (Ollama ↔ Gemini)
- Build verification

**Tidak dikerjakan:**
- Fitur baru di luar scope streaming chat
- Perubahan UI layout

## Langkah Implementasi

### Step 1: Backend verification

1. **Start server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

2. **Test SSE endpoint dengan curl:**
   ```bash
   curl -X POST http://localhost:8000/hybrid/stream \
     -H "Content-Type: application/json" \
     -d '{"message": "Saya ingin membuat TOR untuk proyek AI"}' \
     --no-buffer
   ```

3. **Verifikasi output:**
   - Event `status` dengan `session_id` muncul pertama
   - Event `thinking` muncul (jika Ollama model support)
   - Event `token` muncul satu per satu (BUKAN sekaligus)
   - Event `done` muncul terakhir dengan data lengkap
   - Tidak ada fake `.split(" ")`

4. **Test error handling:**
   ```bash
   # Kirim request saat Ollama mati
   curl -X POST http://localhost:8000/hybrid/stream \
     -H "Content-Type: application/json" \
     -d '{"message": "Test error"}' \
     --no-buffer
   ```
   Expected: event `error` dengan pesan OllamaConnectionError

5. **Test disconnect:**
   - Start curl request → Ctrl+C di tengah streaming
   - Server TIDAK boleh crash
   - Log menunjukkan "Client disconnected"

### Step 2: Frontend verification

1. **Build check:**
   ```bash
   cd app_frontend && npm run build
   ```
   Harus clean tanpa error.

2. **Dev server:**
   ```bash
   npm run dev
   ```

3. **Test di browser:**
   - Buka chat → ketik pesan → Enter
   - ThinkingIndicator harus muncul (jika Ollama support thinking)
   - Token harus muncul satu per satu di bubble (bukan muncul sekaligus)
   - Bubble status: `sending` → `streaming` → `done`
   - Session sidebar ter-update setelah done

### Step 3: Edge case testing

| Test Case | Prosedur | Expected |
|-----------|----------|----------|
| **Timeout** | Set timeout sangat pendek (5s), kirim pesan panjang | Error event "timeout", UI menampilkan error |
| **Empty message** | Kirim `""` | Validasi error (bukan crash) |
| **Rapid messages** | Kirim 3 pesan berturut-turut cepat | Tidak crash, semua diproses |
| **Provider switch** | Chat di Ollama → switch model ke Gemini → chat lagi | Token tetap streaming |
| **WS fallback** | Disable SSE endpoint → kirim pesan | Fallback ke WebSocket |
| **HTTP fallback** | Disable SSE + WS → kirim pesan | Fallback ke HTTP blocking |
| **New session** | Kirim pesan tanpa session_id | Session baru dibuat, ID di-sync |
| **Existing session** | Kirim pesan dengan session_id valid | Session dilanjutkan |
| **Cancel stream** | Abort di tengah streaming (jika ada tombol stop) | Stream berhenti, partial content tetap |

### Step 4: Regresi check

Pastikan fungsi existing tidak rusak:
- [ ] Generate TOR dari dokumen (streaming) masih berfungsi
- [ ] Generate history masih bisa dilihat
- [ ] Retry/continue generate masih berfungsi
- [ ] Session list di sidebar masih ter-load
- [ ] Settings masih bisa diakses
- [ ] Export (DOCX/PDF/MD) masih berfungsi

### Step 5: Update validation checklist di plan-design

File: `plan-design-beta0.2.6.md`

Update semua checkbox menjadi ✅:

```markdown
- [x] Tidak ada fake streaming
- [x] Tidak ada blocking response di path SSE
- [x] SSE adalah primary
- [x] Token real-time
- [x] Thinking → streaming transisi mulus
- [x] WebSocket masih ada sebagai fallback
- [x] Provider interface standar
- [x] Disconnect handled
- [x] Build clean
```

## Output yang Diharapkan

- Semua test case passed
- Build clean
- Validation checklist completed
- Tidak ada regresi di fitur existing

## Dependencies

- Task 1-5 semua harus sudah selesai

## Acceptance Criteria

- [ ] `curl` test SSE endpoint → token real-time
- [ ] Browser test → thinking → streaming → done transisi mulus
- [ ] `npm run build` clean
- [ ] `uvicorn --reload` tanpa error
- [ ] Timeout handling benar
- [ ] Disconnect handling tidak crash server
- [ ] Provider switching (Ollama ↔ Gemini) berfungsi
- [ ] Fallback chain (SSE → WS → HTTP) berfungsi
- [ ] Tidak ada regresi di fitur Generate TOR
- [ ] Validation checklist di plan-design semua ✅

## Estimasi

Medium (2-3 jam)
