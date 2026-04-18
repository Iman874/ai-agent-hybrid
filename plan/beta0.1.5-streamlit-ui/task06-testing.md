# Task 06 — Manual Testing: Semua Flow Scenarios

## 1. Judul Task

Manual testing seluruh Streamlit UI: happy path, escalation, force generate, error states, dan edge cases.

## 2. Deskripsi

Jalankan semua skenario penggunaan untuk memastikan UI berfungsi end-to-end. Dokumentasikan hasil test dan perbaiki bug yang ditemukan.

## 3. Tujuan Teknis

- Verifikasi happy path: chat → auto generate → TOR preview → download
- Verifikasi escalation: lazy user → warning muncul
- Verifikasi force generate: button → TOR generated
- Verifikasi error handling: backend down, timeout
- Verifikasi new session: state reset
- Verifikasi sidebar updates real-time

## 4. Scope

### Yang dikerjakan
- Manual testing di browser
- Bug fix jika ditemukan
- Validasi semua acceptance criteria dari task sebelumnya

### Yang tidak dikerjakan
- Automated UI testing
- Load testing

## 5. Langkah Implementasi

### Test Scenario 1: Happy Path

```
1. Buka http://localhost:8501
2. Ketik: "Saya ingin buat TOR untuk workshop AI di kantor pemerintah"
3. ✅ Verify: assistant merespons, sidebar: progress update, turn 1
4. Ketik: "3 hari, 30 peserta ASN, budget 50 juta, bulan Juli 2026, 
   tujuan meningkatkan literasi AI, output sertifikat dan laporan"
5. ✅ Verify: TOR generated, preview muncul, download button ada
6. Klik download → file .md ter-download
```

### Test Scenario 2: Escalation (Lazy User)

```
1. Klik "Percakapan Baru"
2. Ketik: "buat TOR AI"
3. Ketik: "terserah aja"
4. Ketik: "gak tau"
5. ✅ Verify: escalation triggered, TOR preview + warning ⚠️
```

### Test Scenario 3: Force Generate

```
1. Klik "Percakapan Baru"
2. Ketik: "TOR workshop data science 2 hari"
3. Sebelum data lengkap, klik "🚀 Force Generate TOR" di sidebar
4. ✅ Verify: TOR generated (mungkin dengan asumsi)
```

### Test Scenario 4: New Session

```
1. Setelah chat beberapa turn, klik "🔄 Percakapan Baru"
2. ✅ Verify: chat kosong, sidebar reset, session_id None
```

### Test Scenario 5: Backend Down

```
1. Stop backend (kill uvicorn)
2. Ketik pesan di Streamlit
3. ✅ Verify: error message muncul, sidebar: API 🔴 Offline
4. Start backend kembali
5. Ketik pesan → berfungsi normal
```

### Test Scenario 6: Empty Message Prevention

```
1. Coba kirim pesan kosong via chat_input
2. ✅ Verify: Streamlit native validation (min_length=1 di API)
```

## 6. Output yang Diharapkan

Semua 6 skenario PASSED tanpa error.

## 7. Dependencies

- **Task 01-05** selesai

## 8. Acceptance Criteria

- [ ] Happy path: chat → generate → preview → download ✅
- [ ] Escalation: lazy pattern → warning ✅
- [ ] Force generate: button → TOR generated ✅
- [ ] New session: state reset ✅
- [ ] Backend down: error handling ✅
- [ ] Sidebar: progress, fields, health update real-time ✅

## 9. Estimasi

**Medium** — ~1 jam (termasuk bug fix)
