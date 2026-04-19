# Task 04: Extraction Prompt

## 1. Judul Task
Penyusunan Ekstraksi Prompt (Gemini extraction instruction)

## 2. Deskripsi
Membuat baris instruksi Prompt statis yang secara spesifik menugaskan algoritma LLM (Gemini) untuk melakukan konversi "Plain Text PDF TOR" menuju struktur format JSON Schema yang divalidasi.

## 3. Tujuan Teknis
Mendefinisikan konstan template string Prompt `STYLE_EXTRACTION_PROMPT` yang secara teknis memandu tata bahasa LLM untuk melempar output JSON only.

## 4. Scope
* **Yang dikerjakan**: Membuat konstanta text Prompt pada layer prompt (backend prompt).
* **Yang tidak dikerjakan**: Menerapkan prompting ke call API Gemini API endpoint.

## 5. Langkah Implementasi
1. Buka/buat file `app/ai/prompts/extract_style.py`.
2. Buat konstanta string multi baris bernama `STYLE_EXTRACTION_PROMPT`.
3. Tuliskan teks panjang sesuai panduan model. Menyebutkan bahwa AI bertugas menganalisis struktur dan gaya ke dalam JSON schema spesifik `sections`, `config`, dsb.
4. Yakinkan instruksi final di prompt melarang markdown atau tag (hanya output JSON curly braces `{ ... }`).

## 6. Output yang Diharapkan
Sebuah string konstan yang memiliki injeksi placeholder seperti `{DOCUMENT_TEXT}`.

## 7. Dependencies
- Module knowledge document dari plan beta0.1.9.

## 8. Acceptance Criteria
- [ ] Field `{DOCUMENT_TEXT}` ready.
- [ ] Format JSON struktur yang dijelaskan pada prompt benar dan cocok mapping-nya dengan field di Task 01 (id, title, req, desc).

## 9. Estimasi
Low
