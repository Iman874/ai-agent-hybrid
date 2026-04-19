# Task 09: Testing End-to-End

## Deskripsi
Testing menyeluruh untuk memastikan semua fitur Beta 0.1.7 berfungsi: model switching, Gemini chat mode, UI layout, tools integration, dan backward compatibility.

## Tujuan Teknis
1. Test backend API: `/models`, `/hybrid` dengan `chat_mode`
2. Test UI: model selector, chat flow, tools, TOR preview
3. Test edge cases: Ollama offline, switch mid-session, error handling

## Scope
- **Dikerjakan**:
  - API testing via curl (backend saja)
  - Manual UI testing (user)
  - Error scenario testing
- **Tidak dikerjakan**:
  - Unit tests otomatis (future scope)

## Skenario Testing

### Skenario 1: GET /models (API)
```bash
curl http://localhost:8000/api/v1/models
```
**Expected**: JSON list models dengan status

### Skenario 2: Chat via Gemini Mode (API)
```bash
curl -X POST http://localhost:8000/api/v1/hybrid \
  -H "Content-Type: application/json" \
  -d '{"message": "Saya mau buat TOR workshop AI untuk 30 peserta", "options": {"chat_mode": "gemini"}}'
```
**Expected**: Response valid dengan chat dari Gemini (bukan Ollama)

### Skenario 3: Chat via Local Mode — Backward Compatible (API)
```bash
curl -X POST http://localhost:8000/api/v1/hybrid \
  -H "Content-Type: application/json" \
  -d '{"message": "Halo, saya mau buat TOR", "options": {"chat_mode": "local"}}'
```
**Expected**: Response identik dengan behavior lama (via Ollama)

### Skenario 4: Chat tanpa options — Default (API)
```bash
curl -X POST http://localhost:8000/api/v1/hybrid \
  -H "Content-Type: application/json" \
  -d '{"message": "Halo"}'
```
**Expected**: Default ke local LLM, response normal

### Skenario 5: UI — Model Selector (USER)
1. Buka Streamlit
2. Lihat sidebar: model selector harus ada
3. Pilih "Gemini API"
4. Mulai chat → verifikasi response dari Gemini
5. Switch ke "Local LLM" → warning muncul
6. Confirm → session reset

### Skenario 6: UI — From Document via Sidebar (USER)
1. Buka sidebar → Tools → "📄 Generate dari Dokumen"
2. Upload file TXT
3. Klik Generate
4. TOR preview muncul di main area
5. Download MD dan PDF berfungsi

### Skenario 7: UI — Theme & Layout (USER)
1. Dark theme aktif
2. Chat bubbles rounded, warna berbeda user/assistant
3. Sidebar bersih, semua kontrol accessible
4. No broken elements

### Skenario 8: Ollama Offline (API/UI)
1. Stop Ollama
2. GET /models → Local LLM status "offline"
3. UI → Local LLM tidak bisa dipilih / disabled
4. Gemini masih berfungsi normal

## Dependencies
- Semua task sebelumnya (01-08)

## Acceptance Criteria
- [ ] Skenario 1-4: API responses sesuai expected
- [ ] Skenario 5: Model selector berfungsi, switch = reset
- [ ] Skenario 6: From Document berfungsi via sidebar
- [ ] Skenario 7: Dark theme, layout modern, no broken UI
- [ ] Skenario 8: Ollama offline gracefully handled
- [ ] Tidak ada regresi dari fitur lama

## Estimasi
Medium

## Catatan
- Skenario 1-4 & 8 dikerjakan developer (via curl/API test)
- Skenario 5-7 dikerjakan oleh user (manual UI testing)
