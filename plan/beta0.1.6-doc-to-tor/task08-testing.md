# Task 08 — Manual Testing: Semua Flow Document-to-TOR

## 1. Judul Task

Manual testing seluruh fitur Document-to-TOR: upload berbagai format, error handling, dan edge cases.

## 2. Deskripsi

Jalankan semua skenario penggunaan untuk memastikan fitur document-to-TOR berfungsi end-to-end di Streamlit UI dan juga via API langsung.

## 3. Tujuan Teknis

- Verifikasi upload file TXT → TOR generated
- Verifikasi upload file PDF → TOR generated
- Verifikasi upload file DOCX → TOR generated
- Verifikasi konteks tambahan ter-include di TOR
- Verifikasi error handling: format salah, file kosong, file besar
- Verifikasi download .md berfungsi
- Verifikasi tab Hybrid dan Gemini Direct masih berfungsi

## 4. Scope

### Yang dikerjakan
- Manual testing di browser (Streamlit)
- Manual testing via curl (API)
- Bug fix jika ditemukan

### Yang tidak dikerjakan
- Automated testing

## 5. Langkah Implementasi

### Test Scenario 1: TXT Upload

```
1. Buat file test.txt:
   "Kegiatan workshop AI untuk 30 ASN selama 3 hari di bulan Juli 2026.
    Tujuan meningkatkan literasi AI. Budget 50 juta. Output: sertifikat."
2. Buka http://localhost:8501 → tab "📄 From Document"
3. Upload test.txt
4. Klik "🚀 Generate TOR dari Dokumen"
5. ✅ Verify: TOR preview muncul, metadata ada, download berfungsi
```

### Test Scenario 2: PDF Upload

```
1. Gunakan PDF contoh (laporan/proposal)
2. Upload di tab "📄 From Document"
3. ✅ Verify: TOR generated sesuai isi PDF
```

### Test Scenario 3: Konteks Tambahan

```
1. Upload file TXT
2. Isi konteks: "Ini lanjutan kegiatan tahun lalu, tingkatkan ke advanced"
3. Klik Generate
4. ✅ Verify: TOR merefleksikan konteks tambahan
```

### Test Scenario 4: Format Tidak Didukung

```
1. Rename file jadi .exe → coba upload
2. ✅ Verify: file uploader menolak (filtered by type)
```

### Test Scenario 5: File Kosong

```
1. Buat file kosong test_empty.txt
2. Upload → Generate
3. ✅ Verify: error "Dokumen terlalu pendek" muncul
```

### Test Scenario 6: API Direct (curl)

```bash
# TXT
curl -X POST http://localhost:8000/api/v1/generate/from-document \
  -F "file=@test.txt" \
  -F "context=Buat TOR lanjutan" | python -m json.tool

# Verify: JSON response dengan tor_document
```

### Test Scenario 7: Tab Lain Masih Berfungsi

```
1. Tab "💬 Hybrid Chat" → chat → berfungsi
2. Tab "🚀 Gemini Direct" → form → berfungsi
3. Tab "📄 From Document" → upload → berfungsi
4. ✅ Verify: semua tab independen, tidak saling ganggu
```

## 6. Output yang Diharapkan

Semua 7 skenario PASSED.

## 7. Dependencies

- **Task 01-07** selesai

## 8. Acceptance Criteria

- [ ] TXT upload → TOR generated ✅
- [ ] PDF upload → TOR generated ✅
- [ ] Konteks tambahan → reflected in TOR ✅
- [ ] Format salah → ditolak ✅
- [ ] File kosong → error ✅
- [ ] API curl → response JSON valid ✅
- [ ] Semua 3 tab berfungsi independen ✅
- [ ] Download .md berfungsi ✅

## 9. Estimasi

**Medium** — ~1 jam (termasuk bug fix)
