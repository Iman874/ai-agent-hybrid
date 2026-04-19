# Task 05: Prompt Injector — Dynamic Format

## 1. Judul Task
Update Modul Rendering Prompt ke Inject Format Dinamis

## 2. Deskripsi
Mengganti teks hardcoded yang menjelaskan "Seksi Latar Belakang... 1. 2. 3." pada existing prompt generator dengan pola placeholder dynamic `{FORMAT_SPEC}` sehingga spesifikasinya bisa mengikuti data string yang diproduksi modul format style aktif.

## 3. Tujuan Teknis
Memodifikasi struktur konstanta prompt (`GEMINI_STANDARD_PROMPT`, dsb.) dengan menghapus blok deskripsi list angka hardcode format TOR lama. Menambah logika parameter tambahan `format_spec` di dalam argumen pemanggilan builder.

## 4. Scope
* **Yang dikerjakan**: Update `app/core/gemini_prompt_builder.py` dan `app/ai/prompts/(generate_tor.py, escalation.py, document_tor.py)`.
* **Yang tidak dikerjakan**: Melakukan integrasi injection variable di GenerateService (dilakukan di task lain).

## 5. Langkah Implementasi
1. Ubah file `app/ai/prompts/generate_tor.py`, `escalation.py`, dan `document_tor.py`.
2. Hapus teks statis bagian struktur bab (seksi 1 s/d 7 dan aturannya).
3. Ganti dengan teks placeholder balok `{FORMAT_SPEC}` di lokasi tempat rules seksi tersebut dulunya berada.
4. Buka file `app/core/gemini_prompt_builder.py`.
5. Ubah setiap argumen fungsi class methods `build_standard`, `build_escalation`, dan `build_from_document` menjadi membutuhkan opsi parameter argumen `format_spec: str | None = None`.
6. Tulis pengkondisian `.replace("{FORMAT_SPEC}", format_spec)` jika dilemparkan, jika tidak diganti fallback (konstanta DEFAULT text yang aman agar backwards-compatible jika terjadi bug pass-parameter string kosong).

## 6. Output yang Diharapkan
Class static Method pada `GeminiPromptBuilder` siap mengambil parameter ke-3 string panjang dan membaurkannya dengan system instructions sebelum hit ke Provider Model API.

## 7. Dependencies
- Tidak ada yang terblocking task logic object custom baru.

## 8. Acceptance Criteria
- [ ] Penggantian string berhasil divalidasi dengan test case test string (jika ada unit test module tersebut).
- [ ] Placeholder `{FORMAT_SPEC}` eksis di prompt files.

## 9. Estimasi
Medium
