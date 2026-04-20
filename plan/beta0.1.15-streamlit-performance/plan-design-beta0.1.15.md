# Plan Design - Beta 0.1.15
# Streamlit Performance Stabilization (Anti-Rerun)

> Codename: streamlit-performance-stabilization
> Versi: Beta 0.1.15
> Tanggal: 2026-04-20
> Status: Final Draft - Keputusan Locked (Ready for Implementation)
> Prasyarat: Beta 0.1.14 selesai

---

## 1. Ringkasan Eksekutif

Beta 0.1.15 fokus pada satu hal: membuat UX Streamlit terasa responsif dan tidak "reload terus" untuk interaksi kecil.

Masalah utama bukan hanya lambat backend, tetapi kombinasi:
- terlalu banyak `st.rerun()` eksplisit,
- rerun full script untuk aksi kecil,
- beberapa network call dieksekusi saat render (bukan saat user action),
- cache policy yang belum konsisten,
- boundary render antar komponen belum ketat.

Hasil akhir yang ditargetkan:
- interaksi lokal (switch tool, buka settings, pilih session, nav settings) terasa instan,
- rerun full script hanya untuk event yang memang butuh,
- API call berulang saat render ditekan seminimal mungkin,
- ada observability sederhana agar performa bisa diukur terus, bukan dirasa-rasa.

---

## 2. Latar Belakang dan Baseline Masalah

### 2.1 Keluhan User

Keluhan yang konsisten: "dikit-dikit reload", UI terasa tidak responsif saat:
- klik tombol sidebar,
- pindah section settings,
- interaksi mode/history,
- update style dan action kecil lainnya.

### 2.2 Baseline Teknis Saat Ini

Temuan dari codebase saat ini:
- Terdapat `21` pemanggilan `st.rerun()` di folder `streamlit_app`.
- `app.py` merender shell global setiap kali script rerun (sidebar, header, tool content).
- Beberapa aksi kecil menggunakan full rerun padahal bisa di-scope atau callback.
- `tor_preview.py` memanggil export API `3x` (`docx/pdf/md`) setiap render preview.
- `get_active_style()` di `form_document.py` dipanggil tiap render dan belum di-cache.
- `settings_dialog.py` sudah mencoba fragment scope pada rerun, tetapi pola event belum seragam.
- `inject_styles()` membaca file CSS tiap rerun.

### 2.3 Dampak UX

Dampak yang user rasakan:
- UI flicker atau terasa berat saat klik,
- notifikasi dan state visual terkesan lompat-lompat,
- latency interaksi kecil mendekati interaksi besar,
- persepsi kualitas turun walau backend sebenarnya sehat.

---

## 3. Tujuan Beta 0.1.15

### 3.1 Tujuan Utama

1. Kurangi rerun full-script yang tidak perlu.
2. Pisahkan render boundary per area UI.
3. Jadikan network call terjadi saat aksi user (event-driven), bukan saat render pasif.
4. Terapkan cache policy yang konsisten dan terukur.
5. Tambahkan instrumentation ringan untuk memantau performa UI.

### 3.2 KPI dan Target Terukur

| KPI | Baseline | Target Beta 0.1.15 |
|---|---:|---:|
| Jumlah titik `st.rerun()` | 21 | <= 8 |
| Aksi UI kecil yang memicu full rerun | Banyak | <= 30% dari total aksi |
| API call saat render preview TOR | 3 call/render | 0 call/render (default) |
| Latency klik lokal (switch tool, nav settings) | tidak terukur, terasa lambat | p50 < 120ms |
| Latency aksi sidebar ke update UI | tidak terukur | p50 < 180ms |
| Flicker saat buka session/settings | sering | minim, tidak mengganggu |

Catatan: angka target adalah target UX lokal dev machine. Nanti disesuaikan setelah baseline profiling real.

### 3.3 Keputusan Final (Locked - Tidak Boleh Diubah)

1. Gunakan hybrid rerun strategy:
  - scoped rerun (fragment/dialog) jika tersedia,
  - fallback global rerun wajib ada,
  - global rerun wajib dilindungi event guard,
  - dilarang rerun tanpa perubahan state.
2. Lazy export wajib:
  - preview tidak boleh melakukan API call,
  - export hanya saat klik tombol "Siapkan",
  - hasil export disimpan di `session_state`,
  - download harus dari data lokal tanpa fetch ulang.
3. Event guard system wajib dengan state:
  - `_ui_action_seq`
  - `_ui_last_action`
  - `_ui_busy`
  - semua action idempotent dan anti re-entrant.
4. Cache policy matrix wajib:
  - TTL sesuai matrix,
  - invalidasi cache terpusat: `invalidate_session_cache()` dan `invalidate_style_cache()`,
  - dilarang network call berulang saat render pasif.
5. Fragment/scoped rerun adalah optimasi opsional, bukan core.
6. Boot optimization wajib:
  - CSS loader di-cache,
  - theme apply hanya sekali dengan guard.
7. Performance instrumentation wajib dengan state:
  - `_perf_enabled`
  - `_perf_samples`
  - dipakai untuk pengukuran latency, bukan asumsi.

---

## 4. Non-Goals (Batasan Scope)

Tidak termasuk di Beta 0.1.15:
- redesign visual besar,
- perubahan UI/UX yang sudah ada,
- refactor backend besar di luar kebutuhan performa UI,
- menambah fitur bisnis baru,
- optimisasi model inference (LLM latency),
- mobile-first redesign.

---

## 5. Akar Masalah Teknis

### 5.1 Rerun Digunakan Sebagai Mekanisme Default

Saat ini banyak event mengandalkan pola:
1) mutate state,
2) `st.rerun()`,
3) render ulang penuh.

Pola ini aman secara correctness, tetapi mahal untuk UX jika dipakai di hampir semua interaksi.

### 5.2 Render-Time Side Effects

Contoh side effect saat render:
- export docx/pdf/md dipanggil saat preview ditampilkan,
- fetch data style aktif dipanggil di body render,
- inject CSS dari disk dibaca ulang per rerun.

Ini membuat aksi kecil ikut membawa beban I/O.

### 5.3 Event Scope Belum Konsisten

Ada event yang bisa local update, tetapi tetap memicu global rerun.
Akibatnya, area yang tidak relevan ikut re-render.

### 5.4 Cache Belum Memiliki Strategi Invalidasi Terpusat

Sebagian data sudah di-cache (`fetch_models`, `check_health`, `fetch_session_list`), tetapi:
- belum semua query penting di-cache,
- invalidasi cache belum seragam,
- belum ada mapping cache key -> event invalidasi.

---

## 6. Arsitektur Solusi yang Diusulkan

## 6.1 Layer A - Render Boundary dan Fragment Strategy

### Konsep

Pisahkan UI menjadi boundary yang jelas:
- App shell
- Sidebar controls
- Main content per tool
- Settings dialog content

Gunakan fragment/dialog-scoped rerun jika versi Streamlit mendukung. Jika tidak, fallback ke rerun global dengan event guard.

Scoped rerun diperlakukan sebagai akselerator. Core strategy tetap controlled rerun + guard.

### Prinsip

- Aksi nav internal dialog tidak boleh me-refresh seluruh app jika tidak perlu.
- Aksi yang hanya ubah state lokal sebaiknya tidak memaksa rerun global.
- Full rerun hanya untuk perubahan besar (misal reset session penuh, switch tema).
- Global rerun hanya boleh terjadi setelah ada perubahan state yang valid.

### Desain Runtime

```text
User Action
   -> Action Dispatcher
   -> Update session_state (minimal)
  -> Optional scoped rerun (fragment/dialog, jika kompatibel)
  -> Fallback global rerun (dengan event guard)
   -> Re-render boundary terkait saja
```

---

## 6.2 Layer B - Event Dispatch dan State Guard

Event guard system bersifat wajib agar rerun tidak duplikat dan tidak re-entrant.

State key yang wajib ada:
- `_ui_action_seq`: counter aksi user,
- `_ui_last_action`: id aksi terakhir yang sudah diproses,
- `_ui_busy`: lock sementara untuk aksi async,
- `_perf_enabled`: toggle debug perf,
- `_perf_samples`: buffer metrik ringan.

Pola wajib:
- setiap action diberi id,
- action handler idempotent,
- ignore duplicate action pada rerun berikutnya,
- tolak action baru jika `_ui_busy = True` (kecuali whitelist action yang aman),
- global rerun hanya dipicu setelah guard meloloskan action.

---

## 6.3 Layer C - Data Fetch and Cache Policy

### Cache Policy Matrix

| Data | Fungsi | TTL | Trigger Invalidation |
|---|---|---:|---|
| Models | `fetch_models()` | 30s | Model switch manual / refresh button |
| Health | `check_health()` | 15s | Manual refresh |
| Session list | `fetch_session_list()` | 10s | new chat, delete session, load session detail |
| Active style | `get_active_style()` | 20s | set active style, create/update/delete style |
| Styles list | `get_styles()` | 20s | create/update/delete/duplicate/extract style |
| Session detail | `fetch_session_detail()` | 15s | message sent, force generate, clear session |

### Implementasi

- Semua fungsi pada cache matrix wajib memakai TTL sesuai tabel.
- Wajib ada helper invalidasi terpusat:
  - `invalidate_style_cache()`
  - `invalidate_session_cache()`
- Tidak boleh ada `notify()` dari function cache untuk mencegah side effect saat cache hit/miss.
- Tidak boleh ada network call berulang saat render pasif.

---

## 6.4 Layer D - Lazy Network Strategy (Render Without Fetch)

### Masalah Kritis Saat Ini

`tor_preview.py` melakukan call export API 3 format setiap render.

### Solusi (Wajib)

Ubah pola menjadi lazy prepare:
1. Tampilkan tombol "Siapkan DOCX/PDF/MD".
2. Fetch bytes hanya saat user klik prepare.
3. Simpan bytes ke `st.session_state`.
4. Tampilkan `st.download_button` dari cache lokal state (tanpa fetch ulang).

Aturan wajib:
- preview tidak boleh melakukan API call,
- export hanya saat user action,
- download selalu dari data lokal di state.

Manfaat:
- render preview tidak lagi memicu network,
- rerun kecil tidak lagi memicu 3 request export,
- perceived performance naik signifikan.

---

## 6.5 Layer E - Boot Pipeline Optimization

### CSS Loader (Wajib)

Masalah: `inject_styles()` membaca file CSS tiap rerun.

Solusi:
- pindahkan read file CSS ke `@st.cache_resource` atau `@st.cache_data` tanpa parameter,
- hanya inject string CSS final yang sudah di-cache.

### Theme Apply (Wajib)

Masalah: `apply_saved_theme()` dipanggil setiap startup script run.

Solusi:
- guard `_theme_applied_once` untuk mencegah operasi tema berulang saat mode tidak berubah,
- `switch_theme()` tetap boleh full rerun (memang perubahan global),
- rerun tema tetap harus lewat event guard agar tidak double trigger.

---

## 6.6 Layer F - Component-Level Optimization

### Sidebar

- Ganti event tertentu ke callback berbasis `on_click` jika cocok.
- Batasi rerun setelah aksi hanya saat state benar-benar berubah.
- Session list tetap limit kecil (4 default), dengan dialog untuk full list.

### Settings Dialog

- Navigasi section cukup update `_settings_section`.
- Gunakan scoped rerun jika kompatibel.
- Jika tidak kompatibel, fallback aman tanpa loop.

### Format Settings

- Pertahankan penggunaan `st.form` untuk batch submit.
- Hindari rerun beruntun di dalam satu submit flow.
- Invalidasi cache style dilakukan eksplisit setelah mutasi berhasil.

### Chat

- Pertahankan rerun setelah respons baru (butuh refresh chat area),
- Tambahkan guard agar action repeat tidak double-send.

---

## 7. Endpoint dan Dependency Scheme

## 7.1 Endpoint yang Digunakan (Wajib)

Tidak ada endpoint backend baru yang mandatory untuk Beta 0.1.15.
Optimisasi fokus di frontend orchestration.

Endpoint existing yang relevan:
- `GET /api/v1/models`
- `GET /api/v1/health`
- `GET /api/v1/sessions`
- `GET /api/v1/session/{session_id}`
- `DELETE /api/v1/sessions/{session_id}`
- `GET /api/v1/styles`
- `GET /api/v1/styles/active`
- `POST /api/v1/styles/{id}/activate`
- `POST /api/v1/hybrid`
- `GET /api/v1/export/{session_id}?format=...`

## 7.2 Optional Endpoint (Jika Nanti Dibutuhkan)

Opsional untuk fase lanjut (bukan wajib beta ini):
- endpoint summary session ringan jika payload detail menjadi bottleneck,
- endpoint signed-url export agar download lebih efisien.

---

## 8. Flow Data Utama Setelah Optimisasi

## 8.1 Flow A - Switch Tool

```text
User pilih tool radio
 -> update st.session_state.active_tool
 -> scoped rerender main content (jika kompatibel)
 -> jika tidak kompatibel: global rerun + event guard
 -> sidebar dan data lain tidak fetch ulang yang tidak perlu
```

## 8.2 Flow B - Buka Settings Section

```text
User klik nav settings
 -> update _settings_section
 -> scoped rerender dialog content (jika kompatibel)
 -> jika tidak kompatibel: global rerun + event guard
 -> tidak trigger refresh session list / health / model list
```

## 8.3 Flow C - Hapus Session

```text
User klik icon close
 -> call DELETE /sessions/{id}
 -> invalidate session list cache
 -> rerender sidebar list
 -> jika sedang view history id tsb, fallback ke active chat
```

## 8.4 Flow D - Preview dan Download TOR

```text
Render preview
 -> tampilkan content + tombol prepare
 -> NO export API call otomatis
User klik prepare format tertentu
 -> fetch export bytes satu kali
 -> simpan bytes ke session_state
 -> tampilkan download button dari data lokal (tanpa fetch ulang)
```

---

## 9. Rencana Perubahan File (Target)

| File | Perubahan Utama |
|---|---|
| `streamlit_app/app.py` | tambah boundary policy, minimalkan rerender global |
| `streamlit_app/state.py` | tambah key event/perf guard |
| `streamlit_app/components/sidebar.py` | event callback + rerun guard + cache invalidation hook |
| `streamlit_app/components/settings_dialog.py` | stable scoped rerender policy |
| `streamlit_app/components/chat.py` | dedupe action + safe rerender |
| `streamlit_app/components/form_document.py` | cache-aware style active fetch |
| `streamlit_app/components/format_tab.py` | invalidasi cache style tersentralisasi |
| `streamlit_app/components/tor_preview.py` | lazy export prepare/download |
| `streamlit_app/api/client.py` | cache policy lengkap + invalidation helper |
| `streamlit_app/styles/loader.py` | cache CSS load |
| `streamlit_app/theme.py` | guard apply theme agar tidak repetitive |
| `streamlit_app/utils/perf.py` (baru) | perf trace helper sederhana |

---

## 10. Breakdown Task Implementasi (Urutan Wajib)

Urutan eksekusi wajib sesuai keputusan final:

1. Task01 - `tor_preview.py` lazy export (paling kritis)
2. Task02 - `sidebar.py` minimasi rerun + event guard
3. Task03 - `settings_dialog.py` scoped update stabil + fallback global guard
4. Task04 - `api/client.py` cache policy matrix + invalidasi terpusat
5. Task05 - `state.py` event guard state (`_ui_*`) + perf instrumentation
6. Task06 - `styles/loader.py` dan `theme.py` boot optimization

Setelah 6 task wajib selesai:
- Task07 - harmonisasi komponen pendukung (`form_document.py`, `format_tab.py`, `chat.py`)
- Task08 - regression test + perf checklist + tuning TTL
- Task10 - bugfix visibilitas edit style pada Settings > Format TOR (style non-default tetap editable)
- Task11 - integrasi bahasa English (i18n runtime) agar pilihan bahasa di Settings benar-benar fungsional
- Task12 - perbaikan kontras hover button di mode terang agar teks tetap terbaca dan tidak menyilaukan

---

## 11. Risiko dan Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Scoped rerun tidak kompatibel versi Streamlit tertentu | error runtime atau no effect | fallback ke rerun global + guard; cek versi saat startup |
| Cache stale setelah mutasi data | data UI tidak sinkron | invalidasi cache terpusat per domain |
| Refactor event flow memicu bug state | UX regression | incremental rollout per komponen + test skenario kritis |
| Lazy export menambah 1 langkah user | friction kecil | copy UX jelas: "Siapkan file" lalu download |
| Terlalu banyak key state baru | kompleksitas maintain | naming convention `_ui_*` dan dokumentasi state |

---

## 12. Verifikasi dan Acceptance Test

## 12.1 Automated

- Unit test helper cache invalidation.
- Unit test action guard (dedupe event).
- Regression test API client function behavior.

## 12.2 Manual Developer Test (fokus UX)

Skenario utama:
1. Switch tool bolak-balik 10x -> tidak terasa berat.
2. Buka settings, pindah section 20x -> tidak ada full flicker.
3. Klik session list berurutan -> load stabil tanpa loop.
4. Preview TOR tampil -> tidak ada call export sebelum user prepare.
5. Delete session saat viewing history -> kembali ke active mode secara aman.

## 12.3 Perf Acceptance Criteria

Plan dianggap sukses jika:
- jumlah titik `st.rerun()` turun signifikan (target <= 8),
- aksi lokal punya p50 latency sesuai target,
- tidak ada bug state mayor baru,
- tidak ada API spam saat rerender pasif.

---

## 13. Rollout Strategy

### Phase 1 - Hotspot Wajib

1) `tor_preview.py`,
2) `sidebar.py`,
3) `settings_dialog.py`.

### Phase 2 - Core Stabilizer Wajib

4) `api/client.py` cache policy + invalidasi,
5) `state.py` event guard + perf state,
6) `styles/loader.py` dan `theme.py` boot optimization.

### Phase 3 - Harmonization

Rapikan semua komponen pendukung agar patuh cache/event policy.

### Phase 4 - Stabilization

Regression test + perf checklist + tuning TTL + dokumentasi final.

---

## 14. Definition of Done (DoD)

- Plan task terimplementasi sesuai scope.
- KPI performa minimal tercapai pada local dev setup.
- Tidak ada regression kritis pada flow chat, document, settings, session history.
- Dokumentasi cache/event policy ditambahkan.
- Checklist task markdown ter-update transparan.

---

## 15. Prinsip Eksekusi yang Tidak Boleh Dilanggar

- Rerun tidak dilarang, tetapi wajib terkontrol.
- Network call hanya boleh terjadi saat user action.
- Render tidak boleh memiliki side effect.
- Semua aksi wajib aman dari double trigger.
- Tidak mengubah UI/UX yang sudah ada.
- Fokus hanya pada performa dan stabilitas.

## 16. Output Implementasi yang Diharapkan

- Refactor code sesuai keputusan final di dokumen ini.
- Tidak ada perubahan perilaku UI/UX yang tidak terkait performa.
- Semua keputusan mandatory (hybrid rerun, lazy export, event guard, cache matrix, boot optimization, instrumentation) terpasang.
