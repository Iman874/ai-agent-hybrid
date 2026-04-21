# Task 9: Testing & Polish

## Deskripsi

Verifikasi end-to-end seluruh fitur model capability system, test edge cases, dan pastikan tidak ada regresi.

## Tujuan Teknis

- E2E test: capability check → UI adaptif → image upload → chat vision → response
- Edge case: unknown model, model switch, large images, text-only model + image
- Build verification
- Regresi check fitur existing

## Scope

**Dikerjakan:**
- End-to-end testing manual
- Fix bug yang ditemukan
- Build verification
- Update validation checklist di plan design

**Tidak dikerjakan:**
- Fitur baru di luar scope capability system

## Langkah Implementasi

### Step 1: Backend verification

1. **Test `GET /models` capabilities:**
   ```bash
   curl http://localhost:8000/models | python -m json.tool
   ```
   - Pastikan setiap model punya field `capabilities`
   - Gemini → `supports_image_input: true`
   - Ollama text → `supports_image_input: false`

2. **Test validasi image + text-only model:**
   ```bash
   curl -X POST http://localhost:8000/hybrid \
     -H "Content-Type: application/json" \
     -d '{"message": "Apa ini?", "images": ["iVBORw0KGgo..."], "options": {"chat_mode": "local"}}'
   ```
   Expected: HTTP 400 — "Model ini tidak mendukung input gambar..."

3. **Test image + Gemini:**
   ```bash
   curl -X POST http://localhost:8000/hybrid \
     -H "Content-Type: application/json" \
     -d '{"message": "Jelaskan gambar ini", "images": ["base64data"], "options": {"chat_mode": "gemini"}}'
   ```
   Expected: HTTP 200 — response relevan dengan gambar

### Step 2: Frontend verification

1. **Build check:**
   ```bash
   cd app_frontend && npm run build
   ```
   Harus clean.

2. **Model switch test:**
   - Pilih model Ollama text → tombol upload **TIDAK muncul**
   - Switch ke Gemini → tombol upload **MUNCUL**
   - Switch kembali ke Ollama → tombol upload **HILANG** + images di antrian ter-clear

3. **Image upload flow:**
   - (Pilih Gemini) Klik tombol 📎 → file picker muncul
   - Pilih 1 gambar → preview thumbnail muncul
   - Pilih 3 gambar lagi → total 4, tombol disabled (max)
   - Hapus 1 gambar via ✕ → tombol enabled kembali
   - Ketik teks + Enter → pesan terkirim

4. **MessageBubble rendering:**
   - Bubble user menampilkan gambar + teks
   - Bubble assistant menampilkan response teks (tanpa gambar)
   - 1 gambar → fluid layout
   - 2+ gambar → grid 2 kolom

5. **ModelSelector badges:**
   - Buka dropdown model
   - Gemini punya badge [Vision] hijau
   - Ollama text punya badge [Text] muted
   - Hover badge → tooltip muncul

### Step 3: Edge case testing

| Test Case | Prosedur | Expected |
|-----------|----------|----------|
| **Unknown model** | Tambah model dengan nama aneh di Ollama | `supports_image_input: false` (fail-safe) |
| **Besar gambar** | Upload gambar 5MB+ | Terkirim (mungkin slow) — tidak crash |
| **Format gambar** | Upload PNG, JPEG, WEBP, GIF | Semua diproses (minimal JPEG + PNG) |
| **Image-only** | Kirim hanya gambar tanpa teks | Bubble render gambar saja, AI merespons |
| **Model switch mid-queue** | Pilih gambar → switch model ke text-only | Images ter-clear atau warning muncul |
| **Rapid switch** | Switch model cepat 5x | UI tidak flicker, capabilities selalu benar |
| **Offline model** | Ollama mati, Gemini available | Capabilities tetap ter-display dari cache |

### Step 4: Regresi check

Pastikan fitur existing tidak rusak:
- [ ] Chat teks biasa (tanpa gambar) masih berfungsi
- [ ] Streaming chat (dari beta 0.2.6) masih berfungsi
- [ ] Generate TOR masih berfungsi
- [ ] Generate history masih bisa dilihat
- [ ] Session list di sidebar berfungsi
- [ ] Settings page berfungsi
- [ ] Export (DOCX/PDF/MD) berfungsi

### Step 5: Update validation checklist

File: `plan-design-beta0.2.7.md`

Update semua checkbox menjadi ✅.

## Output yang Diharapkan

- Semua test case passed
- Build clean
- Tidak ada regresi
- Validation checklist completed

## Dependencies

- Task 1-8 semua harus sudah selesai

## Acceptance Criteria

- [ ] `curl GET /models` → capabilities per model benar
- [ ] `curl POST /hybrid` + image + text-only → error 400
- [ ] `curl POST /hybrid` + image + Gemini → success
- [ ] UI: tombol upload muncul/hilang sesuai model
- [ ] UI: preview strip berfungsi (add, remove, send)
- [ ] UI: MessageBubble render gambar
- [ ] UI: ModelSelector badges benar
- [ ] `npm run build` clean
- [ ] `uvicorn --reload` clean
- [ ] Tidak ada regresi di fitur existing

## Estimasi

Medium (2-3 jam)
