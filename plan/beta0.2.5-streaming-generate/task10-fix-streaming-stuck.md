# Task 10: Fix Streaming Stuck Bug

## 1. Deskripsi
Tombol "Generate TOR" tidak memberikan feedback atau transisi UI, hanya terlihat "stuck" di halaman form upload. Hal ini disebabkan oleh kesalahan fatal pada fetch URL yang memunculkan respons 404 Not Found secara instan, namun mekanisme error di `UploadForm.tsx` tidak menangani UI state dari *store* secara tepat.

## 2. Analisis Masalah
- **Double Path (404 Error)**: Di `src/api/generate.ts`, URL dipanggil dengan `${API_BASE_URL}/api/v1/generate/from-document/stream`. Karena `API_BASE_URL` sendiri sudah bernilai `/api/v1`, hasil akhirnya menjadi `/api/v1/api/v1/generate/...` yang pasti menyebabkan 404.
- **Silent Fail di UploadForm**: Saat streaming API client membuang Exception atau respons 404, ia hanya memanggil callback `onError()`. Ini menyebabkan `useGenerateStore` diset status `isStreaming = false` dan `streamError = "HTTP 404: Not Found"`. Masalahnya, `UploadForm.tsx` hanya merender State Error lokal dari blok try/catch, bukan `streamError` milik Store. Karena try/catch form ini sukses memanggil fungsi set state asinkronus (yang fire-and-forget exceptions ke onError), maka state error lokal tetap kosong `" "`.
- Mengingat `streamingContent` kosong dan `streamError` memiliki isi, kondisi rendering di `GenerateContainer.tsx` yang berbunyi `if (isStreaming || (streamError && streamingContent))` bernilai salah, sehingga komponen langsung me-routing kembali ke tampilan awal (Idle View) secara diam-diam.

## 3. Scope Perubahan (Fixes)

### 3.1. Perbaiki Path URL Endpoint Streaming
- **File:** `app_frontend/src/api/generate.ts`
- **Tindakan:** Edit string template fetch dari:
  `${API_BASE_URL}/api/v1/generate/from-document/stream`
  Menjadi:
  `${API_BASE_URL}/generate/from-document/stream`

### 3.2. Sinkronisasi UI Error di UploadForm
- **File:** `app_frontend/src/components/generate/UploadForm.tsx`
- **Tindakan:** Form ini harus memprioritaskan peringatan dari backend bila `streamError` mucul tetapi stream batal jalan.
- Tampilkan `streamError` pada komponen `<UploadForm>` ketika form kembali idle dengan `streamError` yang tertinggal namun dengan `streamingContent` kosong.

### 3.3. Mengubah Logika Render Partial Error di Container (Opsional & Preventif)
- **File:** `app_frontend/src/components/generate/GenerateContainer.tsx`
- Tidak harus dirubah jika perbaikan 3.2 di atas sudah menangani tampilnya gagal start, karena partial error khusus ditujukan pada `<StreamingResult>` jika progres sempat berjalan jauh.

## 4. Acceptance Criteria
- [ ] Tombol Generate tidak mandek (404 terselesaikan).
- [ ] Kursor berkedip dan streaming progress terlihat mulus.
- [ ] Jika URL salah/Network error, user menerima notifikasi teks merah di layar upload.
