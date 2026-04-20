# Task 08: Hapus Sesi — API Endpoint + Client + UI Button

## 1. Judul Task

Implementasi fitur hapus sesi: API endpoint, client function, dan tombol material icon di sidebar

## 2. Deskripsi

Menambahkan kemampuan menghapus sesi langsung dari sidebar. Setiap item riwayat mendapat tombol `[×]` (Material Design icon `close`) di samping kanan. Sesi aktif tidak bisa dihapus.

## 3. Tujuan Teknis

- **Backend**: Endpoint `DELETE /api/v1/sessions/{session_id}`
- **Client**: Function `delete_session(session_id)` di `api/client.py`
- **UI**: Tombol icon `close` per session item (layout columns: `[5, 1]`)
- Sesi aktif → tombol hapus tidak muncul

## 4. Scope

**Yang dikerjakan:**
- `app/routes/session.py` — endpoint DELETE
- `app/services/session_manager.py` — logic delete dari DB
- `streamlit_app/api/client.py` — `delete_session()` function
- `streamlit_app/components/sidebar.py` — tombol hapus per session

**Yang tidak dikerjakan:**
- Bulk delete (hapus semua sekaligus)
- Konfirmasi dialog sebelum hapus (langsung hapus, karena ringan)
- Session rename

## 5. Langkah Implementasi

### 5.1 Backend — Endpoint DELETE

```python
# app/routes/session.py

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Hapus session beserta semua message-nya."""
    manager = SessionManager()
    success = await manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")
    return {"status": "deleted", "session_id": session_id}
```

### 5.2 Backend — Service Logic

```python
# app/services/session_manager.py

async def delete_session(self, session_id: str) -> bool:
    """Hapus session dan semua data terkait dari database."""
    conn = self._get_connection()
    try:
        # Hapus messages dulu (foreign key)
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        # Hapus session
        result = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return result.rowcount > 0
    except Exception as e:
        logging.error(f"Gagal hapus sesi {session_id}: {e}")
        return False
```

### 5.3 Client — Function

```python
# streamlit_app/api/client.py

def delete_session(session_id: str) -> bool:
    """Hapus session via API."""
    try:
        resp = requests.delete(f"{API_BASE}/sessions/{session_id}")
        return resp.status_code == 200
    except Exception:
        return False
```

### 5.4 UI — Tombol Hapus di Sidebar

Di `_render_session_list()`, setiap item session di-render dalam 2 kolom:

```python
# Layout 2 kolom: [title] [hapus]
col_title, col_del = st.columns([5, 1])

with col_title:
    if st.button(
        title,
        key=f"s_{s['id']}",
        use_container_width=True,
        type="primary" if (is_active or is_viewing) else "secondary",
        disabled=is_active,
    ):
        # ... load session logic ...
        pass

with col_del:
    if not is_active:  # Tidak bisa hapus sesi aktif
        if st.button(
            "",
            icon=":material/close:",
            key=f"del_{s['id']}",
        ):
            delete_session(s["id"])
            st.rerun()
```

**Aturan:**
- Sesi aktif → tombol hapus TIDAK muncul (mencegah hapus sesi yang sedang dipakai)
- Klik hapus → langsung hapus (tanpa konfirmasi, karena session bisa dipulihkan dari riwayat chat)
- Setelah hapus → `st.rerun()` untuk refresh list

## 6. Output yang Diharapkan

```
RIWAYAT
  Pengadaan laptop    [×]
  Workshop AI         [×]
  Training DevOps     [×]
▌ Sesi aktif saat ini
```

- `[×]` = icon `close` via `icon=":material/close:"`
- Sesi aktif tidak punya tombol hapus

## 7. Dependencies

- Task 02 (sidebar session list sudah pakai button list)
- Database session table sudah ada (dari beta 0.1.11)

## 8. Acceptance Criteria

- [ ] Endpoint `DELETE /api/v1/sessions/{session_id}` berfungsi
- [ ] `delete_session()` di client mengembalikan `True/False`
- [ ] Tombol hapus muncul untuk setiap sesi KECUALI sesi aktif
- [ ] Klik tombol hapus → sesi hilang dari list
- [ ] Tombol hapus pakai `icon=":material/close:"` — BUKAN emoji
- [ ] Session yang dihapus juga menghapus messages terkait di database
- [ ] Jika sesi yang sedang dilihat (viewing history) dihapus → kembali ke sesi aktif
- [ ] Server tidak crash jika session_id tidak ditemukan (return 404)

## 9. Estimasi

Medium (1–2 jam)
