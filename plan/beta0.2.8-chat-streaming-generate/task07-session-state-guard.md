# Task 07 — Backend: Update Session State `GENERATING` Guard

## 1. Judul Task

Menambahkan proteksi state `GENERATING` pada endpoint streaming baru dan memperbaiki rollback state saat cancel/error.

## 2. Deskripsi

Endpoint blocking lama (`POST /generate`) langsung memanggil `GenerateService` yang mengurus state secara atomik. Endpoint streaming baru (`POST /generate/chat/stream`) memerlukan proteksi tambahan karena prosesnya bertahap dan bisa di-cancel di tengah jalan. Task ini memastikan:
1. Session di-set ke state `GENERATING` sebelum stream dimulai.
2. Guard: jika session sudah `GENERATING`, tolak request kedua (mencegah duplikat).
3. Rollback: jika stream gagal/cancel, state dikembalikan ke `READY` (bukan tetap `GENERATING` selamanya).

## 3. Tujuan Teknis

- Menambahkan guard check di awal `generate_tor_from_chat_stream()`.
- Memastikan rollback state di `except` dan `finally` block.
- Menjaga konsistensi: state hanya berpindah ke `COMPLETED` jika stream selesai lengkap + post-processing berhasil.

## 4. Scope

### Yang dikerjakan
- Modifikasi endpoint `generate_tor_from_chat_stream()` di `app/api/routes/generate.py` (yang dibuat di task 01).

### Yang tidak dikerjakan
- Perubahan model Session atau migrasi DB (state `GENERATING` sudah valid di DB, lihat `001_initial.sql` line 8).
- Perubahan endpoint lain.

## 5. Langkah Implementasi

### Step 1: Tambahkan guard di awal `event_stream()` generator

Sebelum Phase 1 (Load session data), tambahkan:

```python
# Guard: cek apakah session sedang dalam proses generate
session_check = await session_mgr.get(body.session_id)
if session_check.state == "GENERATING":
    yield sse_event("error", {
        "msg": "Sesi ini sedang dalam proses generate. Tunggu hingga selesai."
    })
    return

if session_check.state == "COMPLETED" and session_check.generated_tor:
    yield sse_event("error", {
        "msg": "TOR sudah dibuat sebelumnya. Gunakan session baru untuk membuat ulang."
    })
    return
```

### Step 2: Pastikan `state="GENERATING"` di-set sebelum stream loop

Ini sudah ditambahkan di task 01. Verifikasikan bahwa sebelum `async for chunk in gemini.generate_stream(prompt):`, ada:
```python
await session_mgr.update(body.session_id, state="GENERATING")
```

### Step 3: Pastikan rollback ada di setiap jalur error

Verifikasi di task 01 bahwa:
- `except GeminiTimeoutError` → `await session_mgr.update(body.session_id, state="READY")`
- `except Exception` → `await session_mgr.update(body.session_id, state="READY")`
- `finally` (cancelled) → `await session_mgr.update(body.session_id, state="READY")`

### Step 4: Tambahkan logging untuk audit trail

```python
logger.info(f"Generate chat stream started: session={body.session_id}, mode={body.mode}")
# ... di finally:
if cancelled:
    logger.info(f"Generate chat stream cancelled: session={body.session_id}, partial={len(full_text)} chars")
```

## 6. Output yang Diharapkan

### Kasus: Request kedua saat masih generating
```
Request 1: POST /generate/chat/stream (session=abc) → mulai streaming
Request 2: POST /generate/chat/stream (session=abc)
  → SSE: {"type": "error", "msg": "Sesi ini sedang dalam proses generate..."}
  → Stream tutup
```

### Kasus: Error mid-stream
```
Session state: CHATTING → GENERATING → (error) → READY
```
(Bukan stuck di `GENERATING` selamanya)

## 7. Dependencies

- **Task 01** harus selesai (endpoint harus sudah ada; task ini memperkuatnya).

## 8. Acceptance Criteria

- [ ] Guard: jika `session.state == "GENERATING"`, emit error event dan return.
- [ ] Guard: jika `session.state == "COMPLETED"` dan `generated_tor` ada, emit error event dan return.
- [ ] State transition: `CHATTING/READY` → `GENERATING` → `COMPLETED` (happy path).
- [ ] State rollback: `GENERATING` → `READY` (error/cancel/timeout).
- [ ] Tidak pernah ada session yang stuck di state `GENERATING` permanen.
- [ ] Logging lengkap: start, cancel, error, complete.
- [ ] Backend startup tanpa error.

## 9. Estimasi

**Low** — ~30 menit kerja (penambahan guard + verifikasi rollback).
