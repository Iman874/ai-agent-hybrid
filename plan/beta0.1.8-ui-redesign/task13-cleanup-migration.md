# Task 13: Cleanup & Migration — Delete Monolith, Update Docs

## Status: 🔲 Pending

---

## 1. Judul Task

Hapus file monolitik, update dokumentasi, dan finalisasi migrasi.

## 2. Deskripsi

Setelah semua komponen terintegrasi dan berfungsi, hapus `streamlit_app.py`
(monolit lama), update `how_to_run.md` dan `config.toml`, serta pastikan
`.gitignore` mencakup file-file baru.

## 3. Tujuan Teknis

- Hapus `streamlit_app.py` (monolit — sudah digantikan oleh `streamlit_app/app.py`)
- Update `how_to_run.md` — command Streamlit berubah
- Update `.streamlit/config.toml` — pastikan minimal
- Tambahkan `.streamlit/.current_theme` ke `.gitignore`
- Update `plan-design-beta0.1.8.md` — tandai semua task sebagai Done

## 4. Scope

**Yang dikerjakan:**
- Delete `streamlit_app.py` (root)
- Update docs: `how_to_run.md`
- Update `.gitignore`
- Final QA pass

**Yang TIDAK dikerjakan:**
- Kode baru — hanya cleanup
- Backend — tidak ada perubahan

## 5. Langkah Implementasi

### Step 1: Delete monolit

```powershell
# PENTING: pastikan streamlit_app/app.py sudah 100% berfungsi sebelum ini!
rm streamlit_app.py
```

### Step 2: Update `how_to_run.md`

Update command Streamlit:

```markdown
### 2. Jalankan Streamlit (Frontend)

Buka terminal kedua:

```bash
# Dari root project:
streamlit run streamlit_app/app.py --server.port 8501
```

Akses di browser: http://localhost:8501
```

### Step 3: Update `.streamlit/config.toml`

Pastikan hanya berisi:

```toml
[server]
headless = true
```

Tidak ada `[theme]` section — theme dikelola oleh `theme.py` saat runtime.

### Step 4: Update `.gitignore`

Tambahkan:

```
# Theme preference (per-user, jangan di-commit)
.streamlit/.current_theme
```

### Step 5: Final QA

Jalankan full flow test:

```
1. ✅ streamlit run streamlit_app/app.py → halaman muncul
2. ✅ Sidebar: brand, model selector, progress, fields, system
3. ✅ Header: title + theme toggle
4. ✅ Tab Chat: empty state → chat → TOR preview
5. ✅ Tab Gemini Direct: form → validate → generate
6. ✅ Tab Dari Dokumen: upload → generate
7. ✅ Theme: dark ↔ light tanpa crash
8. ✅ Semua Material Icons render
9. ✅ Tidak ada emoji tersisa
10. ✅ File monolithic `streamlit_app.py` sudah terhapus
```

### Step 6: Update plan

Tandai semua task di `plan-design-beta0.1.8.md` sebagai ✅ Done.

## 6. Output yang Diharapkan

Setelah task ini:

```
ai-agent-hybrid/
├── streamlit_app/        ← BARU (modular)
│   ├── app.py
│   ├── config.py
│   ├── state.py
│   ├── theme.py
│   ├── api/
│   ├── components/
│   ├── utils/
│   └── styles/
├── .streamlit/
│   ├── config.toml       ← minimal (server only)
│   └── .current_theme    ← di-gitignore
├── how_to_run.md         ← updated
├── .gitignore            ← updated
└── (streamlit_app.py)    ← DIHAPUS
```

## 7. Dependencies

- **Task 12** — `app.py` harus 100% berfungsi sebelum delete monolit

## 8. Acceptance Criteria

- [ ] `streamlit_app.py` (root, monolitik) sudah dihapus
- [ ] `streamlit run streamlit_app/app.py` berjalan sukses
- [ ] `how_to_run.md` merefleksikan command baru
- [ ] `.gitignore` mencakup `.streamlit/.current_theme`
- [ ] `.streamlit/config.toml` minimal (hanya `[server]`)
- [ ] Semua task di plan ditandai Done
- [ ] Full QA pass (10 test cases di atas)

## 9. Estimasi

**Low** — Hanya delete, update docs, dan QA.
