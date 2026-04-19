---
description: Alur standar untuk merencanakan module, folder, dan task sebelum eksekusi.
---

# Workflow Perencanaan Fitur (Planning)

Ketika diperintahkan untuk memulai modul/fitur versi baru, Agen AI harus mematuhi alur berikut:

1. **Buat Folder Versi**:
   - Buat folder di `plan/` dengan format versi (contoh: `plan/beta0.1.10-nama-fitur/`).
2. **Buat Dokumen Rencana (Plan Design)**:
   - Selalu inisialisasi dokumen desain di dalam folder versi tersebut, misalnya `plan-design-beta0.1.10.md`.
   - Dokumen desain harus memuat: Latar Belakang Fitur, Arsitektur, Skema Endpoint/Dependency, dan Flow Data.
3. **Minta Konfirmasi (Wait for Approval)**:
   - Berhenti dan tunggulah ulasan dan instruksi ("Lanjutkan") dari User.
4. **Generate Spesifikasi Task Detail**:
   - Setelah disetujui, barulah pecah rencana tersebut menjadi puluhan task berurutan (misal: `task01-model.md`, `task02-service.md`).
5. **Eksekusi Bertahap / Checklist**:
   - Ketika pengerjaannya dimulai, Agen harus mencentang `[x]` pada riwayat setiap task markdown yang diselesaikan agar statusnya transparan.
