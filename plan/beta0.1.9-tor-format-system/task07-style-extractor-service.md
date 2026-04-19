# Task 07: Style Extractor Service

## 1. Judul Task
Service AI Pengubah Dokumen ke JSON Style (Ekstraksi)

## 2. Deskripsi
Pembuatan service spesifik (mirip PostProcessor pipeline) yang menggabungkan kemampuan parser file yang ada (`DocumentParser`) ditambah parsing output Gemini Model untuk menghasilkan Object valid TORStyle.

## 3. Tujuan Teknis
Menambahkan route file service khusus endpoint `app/core/style_extractor.py` untuk mengolah prompt Task 04. Ini akan mengambil argumen string "full plain text PDF/DOC", meminta Gemini memparse instruksi gaya, lalu men-return data JSON. Menambahkan juga Endpoint integrasi file upload pada route Task 06.

## 4. Scope
* **Yang dikerjakan**: Logic Service class `StyleExtractor`, integrasinya ke `GeminiProvider`, Error fallback handling & reparsing. Tambah integrasi Extraction ke route FastAPI `POST /api/v1/styles/extract`.
* **Yang tidak dikerjakan**: Ekstraksi text PDF/Doc itu sendiri (asumsinya logic `DocumentParser` milik RAG document loader bisa kita pakai ulang/telah support).

## 5. Langkah Implementasi
1. Buat file `app/core/style_extractor.py`.
2. Tulis Class Method `.extract_from_text(document_text: str)` yang memanggil Provider `gemini.generate()` di mana prompt template nya adalah inject text yang tersedia di Prompt statis Task 04.
3. Parse reponse property teks `.text` menggunakan module python `json.loads` (dengan pembersihan escape string markdown `"""json` block prefix buangan bawaan model agar bersih).
4. Return `TORStyle` object instansiasi validation pydantic.
5. Tambahkan Endpoint `POST /api/v1/styles/extract` di `routes/styles.py` menggunakan object API form-data tipe payload `UploadFile` fastapi yang mengubah byte stream menjadi text (memanggil Document Parser), selanjutnya throw ke `extract_from_text()`. 

## 6. Output yang Diharapkan
Model AI meretrieve analisis file dengan struktur seksi JSON lalu kembali ke HTTP Response.

## 7. Dependencies
- [task04-extraction-prompt.md]
- [task06-api-endpoints.md]

## 8. Acceptance Criteria
- [ ] Model Gemini meresponse dan dikonversi via pydantic TANPA kegagalan parse.
- [ ] Form data parameter file terproses properly menjadi string plaintext sebelum dikirim.
- [ ] Service mampu melakukan self handling (contoh 1x retry jika token result output malformed bracket JSON error parsing exception) atau throw HTTPException 400 Bad Request jika failur 2x.

## 9. Estimasi
Medium
