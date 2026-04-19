# Task 06: API Endpoints (Styles)

## 1. Judul Task
Pembuatan Routing Service JSON API untuk Styles

## 2. Deskripsi
Membuat Endpoint Web FastAPI di Backend yang menangani konektor logic pembacaan disk storage JSON (melalui `StyleManager`) memformat HTTP response.

## 3. Tujuan Teknis
Mendeklarasikan sekumpulan route path `/api/v1/styles/` dengan skema Model input Output fastapi valid yang menerima dan mengirim payloads Pydantic TORStyle.

## 4. Scope
* **Yang dikerjakan**: Pembuatan route fastapi `app/api/routes/styles.py`. Penambahan namespace router router file utama.
* **Yang tidak dikerjakan**: Extraction Flow.

## 5. Langkah Implementasi
1. Buat `app/api/routes/styles.py`.
2. Deklarasi API router dengan awalan path namespace `/api/v1/styles`.
3. Panggil dependency injection yang meload module instance class `StyleManager`.
4. Definisikan endpoint GET `/`, endpoint GET `/active`.
5. Definisikan endpoint GET `/{id}`.
6. Definisikan endpoint PUT `/{id}` dan DELETE `/{id}` (dengan proteksi raise 400 bad request error throw apabila Style Manager me-return error permission default hapus).
7. Definisikan POST `/` dan `/{id}/activate`, dan `/{id}/duplicate`.
8. Import module route ini ke file gateway `app/api/router.py`.

## 6. Output yang Diharapkan
Tersedianya endpoint JSON http port backend agar FrontEnd Streamlit UI (requests) dapat mengubah tata kelola style.

## 7. Dependencies
- [task01-data-model-torstyle.md]
- [task03-style-manager-crud.md]

## 8. Acceptance Criteria
- [ ] `GET /api/v1/styles` menampilkan list (termasuk default) tanpa error Internal.
- [ ] Method `DELETE` gagal untuk string ID `_default`.
- [ ] API routes connect proper FastAPI Swagger docs terpopulasi (bisa dicek secara runtime app path /docs).

## 9. Estimasi
Medium
