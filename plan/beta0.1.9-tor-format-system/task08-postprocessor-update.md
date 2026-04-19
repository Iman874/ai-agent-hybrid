# Task 08: PostProcessor Update

## 1. Judul Task
Update Logika Check Validasi Seksi Hasil Render Output TOR

## 2. Deskripsi
Dinamisasi array parameter variabel pada modul PostProcessor sehingga pengecekan error kelupaan bagian format yang diperbuat LLM merujuk kepada list struktur konfigurasi per file.

## 3. Tujuan Teknis
Memodifikasi struktur Class `PostProcessor` yg menyimpan global variabels EXPECTED_SECTIONS dan merubahnya pada block filter text missing element menggunakan dynamic object style argument jika object dikirimkan (bila None fallback standard list lama).

## 4. Scope
* **Yang dikerjakan**: Merubah fungsi logic text parsing check property post-processing di `post_processor.py`.
* **Yang tidak dikerjakan**: Inject dynamic system param ke file generate (task 09).

## 5. Langkah Implementasi
1. Buka `app/core/post_processor.py`.
2. Pada argument list filter function method class `process` ubah def argumentnya memberikan `style : TORStyle | None = None`. 
3. Di blok internal logic kode validation missing list, bangun loop penentu: jika ada `style` terlampir check missing content based on `style.sections` mapping parameter list seksi title yang Required, serta parameter properties integer batas minimal wordcount (`style.config.min_word_count`).
4. Apply filter dinamis ke checking function internal. 

## 6. Output yang Diharapkan
Fungsi post-processing akan men-throw warning/menandakan atribut meta parameter JSON response final missing sections string dari property nama sections style custom (bukan text bawaan Latar Belakang dsbnya hardcoded lama).

## 7. Dependencies
- Tidak ada. Module pure class python utility modification check.

## 8. Acceptance Criteria
- [ ] Post process tidak crash saat call missing argument parameter (tidak supply parameter style tetap berjalan using default expectation static attribute).
- [ ] Support dynamic required condition (jika custom `required = False`, maka section title tidak di-match dengan regex warning missing list error output return post processing properties metadata list output missing sections meta_data array).

## 9. Estimasi
Low
