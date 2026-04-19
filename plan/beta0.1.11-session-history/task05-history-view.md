# Task 05: Read-Only History View — Chat + TOR Preview

> **Status**: [ ] Belum Dikerjakan
> **Estimasi**: Medium (1–2 jam)
> **Dependency**: Task 03 + Task 04 (state + sidebar harus sudah ada)

## 1. Deskripsi

Mengimplementasikan tampilan read-only ketika user membuka session lama dari riwayat. Chat history ditampilkan tanpa input box, dengan banner info bahwa session ini arsip. Jika session memiliki TOR, tetap tampilkan preview + download buttons.

## 2. Tujuan Teknis

- `render_chat_tab()` mendeteksi `is_viewing_history` dan render mode berbeda
- Chat history ditampilkan read-only (tanpa `st.chat_input`)
- Banner info "Anda melihat arsip session" ditampilkan
- Tombol "Kembali ke Obrolan Aktif" tersedia
- TOR preview + download tetap berfungsi untuk session lama

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/components/chat.py` — tambah history view mode
- `streamlit_app/components/tor_preview.py` — pastikan kompatibel dengan history session

**Yang tidak dikerjakan:**
- Resume chat (out of scope)
- Edit TOR lama (out of scope)

## 4. Langkah Implementasi

### 4.1 Modifikasi `render_chat_tab()` di `chat.py`

- [ ] Tambahkan import di bagian atas:

```diff
 from state import reset_session
+from state import back_to_active
```

- [ ] Tambahkan guard clause di awal `render_chat_tab()`:

```python
def render_chat_tab():
    """Render tab Chat: empty state / messages / TOR preview / input."""

    # === HISTORY VIEW MODE ===
    if st.session_state.is_viewing_history:
        _render_history_view()
        return

    # ... kode existing (empty state, messages, TOR preview, chat input) ...
```

### 4.2 Buat Fungsi `_render_history_view()`

- [ ] Tambahkan fungsi baru `_render_history_view()` di `chat.py`:

```python
def _render_history_view():
    """Tampilkan session lama dalam mode read-only."""
    hist = st.session_state.history_session

    if not hist:
        st.warning("Data session tidak tersedia.")
        if st.button("← Kembali"):
            back_to_active()
            st.rerun()
        return

    # --- Banner Info ---
    session_title = hist.get("extracted_data", {}).get("judul") or f"Session {hist['id'][:8]}..."
    session_state = hist.get("state", "—")
    session_turns = hist.get("turn_count", 0)

    st.info(
        f"📋 **Arsip Session** — {session_title}\n\n"
        f"Status: `{session_state}` · {session_turns} Turn · "
        f"Mode read-only, tidak bisa mengirim pesan baru."
    )

    # --- Tombol Kembali ---
    if st.button("← Kembali ke Obrolan Aktif", type="primary"):
        back_to_active()
        st.rerun()

    st.divider()

    # --- Render Chat History (read-only) ---
    chat_history = hist.get("chat_history", [])

    if not chat_history:
        st.caption("_Session ini tidak memiliki riwayat chat._")
    else:
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            with st.chat_message(role):
                st.markdown(content)

    # --- TOR Preview (jika ada) ---
    generated_tor = hist.get("generated_tor")
    if generated_tor:
        st.divider()
        # Bangun tor dict yang kompatibel dengan render_tor_preview()
        tor_dict = {
            "content": generated_tor,
            "metadata": hist.get("metadata", {}),
        }
        render_tor_preview(
            tor=tor_dict,
            session_id=hist["id"],
            key_suffix="_history",
        )
```

### 4.3 Pastikan `tor_preview.py` Kompatibel

File `tor_preview.py` sudah menerima `session_id` (direfactor di beta 0.1.10). Tapi perlu dipastikan bahwa ketika session lama diakses, export endpoint bisa menemukan TOR-nya di cache.

**Potensi issue**: TOR dari session lama sudah tersimpan via `TORCache` (untuk chat flow) atau belum tersimpan (untuk session lama yang dibuat sebelum beta 0.1.10).

- [ ] Tambahkan fallback handling jika export gagal:

Di `_render_history_view()`, jika `generated_tor` ada tapi export gagal (karena belum di-cache), tampilkan fallback download dari data yang sudah ada di history:

```python
    # --- Fallback: Download langsung dari data history (tanpa API export) ---
    if generated_tor:
        st.divider()
        st.caption("💡 Jika download tidak berfungsi, gunakan fallback di bawah:")
        fb1, fb2 = st.columns(2)
        with fb1:
            st.download_button(
                "📝 Download .md (fallback)",
                data=generated_tor,
                file_name=f"tor_history.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_history_md_fb",
            )
```

> **Catatan**: Fallback ini hanya untuk backward compatibility. Session baru setelah beta 0.1.10 sudah menyimpan TOR ke cache.

### 4.4 Pastikan Tab Lain Tidak Terpengaruh

- [ ] Pastikan tab "Gemini Direct" dan "Dari Dokumen" **tidak** tampil dalam history view mode. Opsi:
  - Menambahkan `disabled` pada tab header (Streamlit tidak support ini langsung)
  - Alternatif: tambahkan guard di `render_direct_tab()` dan `render_document_tab()`:

```python
# Di awal render_direct_tab() dan render_document_tab():
if st.session_state.is_viewing_history:
    st.info("📋 Anda sedang melihat arsip session. Kembali ke obrolan aktif untuk menggunakan fitur ini.")
    return
```

## 5. Output yang Diharapkan

### History View Mode — Chat Tab:
```
┌─────────────────────────────────────────────┐
│ ℹ️  📋 Arsip Session — Workshop AI           │
│ Status: COMPLETED · 8 Turn                  │
│ Mode read-only, tidak bisa mengirim baru.   │
└─────────────────────────────────────────────┘

[← Kembali ke Obrolan Aktif]

────────────────────────────────────────────────

👤 Saya ingin membuat TOR workshop AI untuk ASN

🤖 Baik! Bisa ceritakan tujuan utama workshop ini?

👤 Meningkatkan kompetensi digital ASN

🤖 Siap. Berapa lama workshop ini direncanakan?

...

────────────────────────────────────────────────

✅ TOR Berhasil Dibuat!
[📄 Download .docx] [📕 Download .pdf] [📝 Download .md]
```

### Tampilan Tab Lain saat History View:
```
ℹ️ Anda sedang melihat arsip session.
   Kembali ke obrolan aktif untuk menggunakan fitur ini.
```

## 6. Acceptance Criteria

- [ ] Membuka session lama → tab Chat berubah ke mode read-only.
- [ ] Banner info menampilkan judul session, status, dan jumlah turn.
- [ ] Chat history ditampilkan lengkap dengan role icon (user/assistant).
- [ ] **Tidak ada** `st.chat_input()` dalam history view.
- [ ] Tombol "Kembali ke Obrolan Aktif" berfungsi → kembali ke session aktif.
- [ ] Jika session punya TOR → TOR preview muncul dengan download buttons.
- [ ] Tab "Gemini Direct" dan "Dari Dokumen" menampilkan pesan info saat history view aktif.
- [ ] Kembali ke mode normal → semua tab berfungsi seperti biasa.
