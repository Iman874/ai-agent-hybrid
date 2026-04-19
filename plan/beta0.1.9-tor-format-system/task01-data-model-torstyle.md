# Task 01: Data Model TORStyle

## 1. Judul Task
Pembuatan Data Model TORStyle (Pydantic)

## 2. Deskripsi
Membuat struktur data inti yang mendefinisikan sebuah gaya penulisan (style) dokumen TOR, termasuk pengaturan per seksi dan konfigurasi umum.

## 3. Tujuan Teknis
Membangun hierarki Pydantic base models (`TORSection`, `TORStyleConfig`, `TORStyle`) yang memastikan setiap operasi pengelolaan style memiliki validasi data yang kuat (type safety). Method `to_prompt_spec()` juga disiapkan untuk nanti di-inject ke prompt.

## 4. Scope
* **Yang dikerjakan**: Membuat model `TORSection`, `TORStyleConfig`, dan `TORStyle` beserta propertinya. Menambahkan method `to_prompt_spec()` pada `TORStyle` untuk merender spesifikasi menjadi string.
* **Yang tidak dikerjakan**: Implementasi penyimpanan JSON ke disk (CRUD file) atau logic ekstraksi.

## 5. Langkah Implementasi
1. Buat file baru di `app/models/tor_style.py`.
2. Import `BaseModel` dari Pydantic.
3. Buat class `TORSection`:
    * `id`: str
    * `title`: str
    * `heading_level`: int (default: 2)
    * `required`: bool (default: True)
    * `description`: str
    * `min_paragraphs`: int (default: 1)
    * `subsections`: list[str] (default: [])
    * `format_hint`: str (default: "")
4. Buat class `TORStyleConfig`:
    * `language`: str (default: "id")
    * `formality`: str (default: "formal")
    * `voice`: str (default: "active")
    * `perspective`: str (default: "third_person")
    * `min_word_count`: int (default: 500)
    * `max_word_count`: int (default: 3000)
    * `numbering_style`: str (default: "numeric")
    * `custom_instructions`: str (default: "")
5. Buat class `TORStyle`:
    * `id`: str
    * `name`: str
    * `description`: str (default: "")
    * `is_default`: bool (default: False)
    * `is_active`: bool (default: False)
    * `created_at`: str
    * `updated_at`: str
    * `source`: str (default: "manual")
    * `source_filename`: str | None (default: None)
    * `sections`: list[TORSection]
    * `config`: TORStyleConfig
6. Lengkapi method `TORStyle.to_prompt_spec()` yang akan mengiterasi sections dan config untuk menggenerate string text yang rapi untuk di-inject ke prompt AI.

## 6. Output yang Diharapkan
Sebuah file `app/models/tor_style.py` yang bisa diimport ke model lain tanpa error. Mampu mengubah object pydantic dari dan ke JSON via `model_dump_json()`. Pemanggilan `to_prompt_spec()` mengeluarkan list metadata urut secara string.

## 7. Dependencies
- Pydantic package

## 8. Acceptance Criteria
- [ ] Pydantic models terdefinisi sesuai skema.
- [ ] Validasi error jika field wajib kosong tidak terpenuhi.
- [ ] Method `to_prompt_spec()` mem-formatting semua field text secara readable.

## 9. Estimasi
Low
