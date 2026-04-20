# Task 5: State Event Guard dan Performance State

## 1. Judul Task

Tambahkan state wajib untuk event guard dan instrumentation performa.

## 2. Deskripsi

Task ini membuat fondasi kontrol action agar idempotent, anti re-entrant, dan siap mengukur latency antar aksi UI.

## 3. Tujuan Teknis

- State wajib tersedia:
  - _ui_action_seq
  - _ui_last_action
  - _ui_busy
  - _perf_enabled
  - _perf_samples
- Tersedia helper guard yang bisa dipakai komponen.
- Aksi duplikat dapat ditolak secara konsisten.

## 4. Scope

Yang dikerjakan:
- Update streamlit_app/state.py untuk default state baru.
- Tambah helper state guard (begin action, finish action, is duplicate, mark sample).

Yang tidak dikerjakan:
- Integrasi penuh ke semua komponen (dikerjakan task harmonisasi).
- Perubahan UI.

## 5. Langkah Implementasi

1. Tambahkan key default baru ke init_session_state().
2. Buat helper di state.py, contoh:
   - next_ui_action_id() -> str
   - should_process_action(action_id: str) -> bool
   - begin_ui_action(action_id: str) -> bool
   - end_ui_action(action_id: str) -> None
   - record_perf_sample(name: str, ms: float) -> None
3. Terapkan aturan:
   - jika _ui_busy True, action baru ditolak (kecuali whitelist di caller),
   - _ui_last_action dipakai untuk dedupe.
4. Update reset_session() agar state guard kembali aman.
5. Pastikan typing hints ketat pada helper baru.

## 6. Output yang Diharapkan

- Semua key _ui_* dan _perf_* tersedia sejak startup.
- Tersedia API helper internal untuk mencegah double trigger.
- Perf sample bisa disimpan sebagai buffer list di state.

## 7. Dependencies

- Task 4 selesai.

## 8. Acceptance Criteria

- [ ] Key _ui_action_seq, _ui_last_action, _ui_busy ada di default state.
- [ ] Key _perf_enabled dan _perf_samples ada di default state.
- [ ] Helper guard bekerja dan idempotent.
- [ ] reset_session tidak meninggalkan state guard dalam kondisi busy.
- [ ] Semua helper baru menggunakan typing hints.

## 9. Estimasi

Medium (2-3 jam)
