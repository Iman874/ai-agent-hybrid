# Task 02: Default Style JSON

## 1. Judul Task
Pembuatan Default Style JSON yang Locked

## 2. Deskripsi
Menyalain format TOR statik/hardcoded saat ini ke dalam representasi format JSON berdasarkan skema `TORStyle` terbaru, lalu menjadikannya file statis yang digunakan sebagai acuan dasar (fallback).

## 3. Tujuan Teknis
Membentuk file base `_default.json` di dalam folder persistent (`data/tor_styles/`) yang memuat format presisi seperti standard operasional awal saat ini agar tidak terjadi breaking change format bagi end-user yang tidak ingin custom.

## 4. Scope
* **Yang dikerjakan**: Mapping prompt format lama (7 seksi) ke file `_default.json`. Menentukan environment loading point file JSON-nya.
* **Yang tidak dikerjakan**: Logic untuk membaca dan menulis dari aplikasi.

## 5. Langkah Implementasi
1. Pastikan struktur/folder `data/tor_styles/` dibuat.
2. Buat file `data/tor_styles/_default.json`.
3. Format file berisikan field lengkap dari TORStyle di task 01.
    * Atribut ID: `_default`
    * Atribut: `is_default: true`
    * Masukkan 7 seksi: Latar Belakang, Tujuan, Ruang Lingkup, Output, Timeline, Estimasi Biaya, Penutup.
    * Konfigurasi bahasa `id`, dsb.
4. Pastikan file JSON formatnya fully valid (menggunakan `"` (double quotes) dsb).

## 6. Output yang Diharapkan
Sebuah file `data/tor_styles/_default.json` yang jika di-parse menggunakan pydantic model dari Task 01 tidak memunculkan ValueError/KeyError. 

## 7. Dependencies
- [task01-data-model-torstyle.md]

## 8. Acceptance Criteria
- [ ] Tersedia directory `data/tor_styles`
- [ ] Didalamnya ada file `_default.json` proper.
- [ ] Memiliki semua ke-7 section TOR.

## 9. Estimasi
Low
