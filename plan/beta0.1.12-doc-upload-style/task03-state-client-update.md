# Task 03: Frontend — State Keys + Update `generate_from_document()` di Client

> **Status**: [x] Selesai
> **Estimasi**: Low (30 menit)
> **Dependency**: Task 02 (endpoint harus sudah menerima `style_id`)

## 1. Deskripsi

Menambahkan state keys baru di `state.py` untuk mendukung style selection di tab "Dari Dokumen", dan memperbarui fungsi `generate_from_document()` di `client.py` agar bisa mengirim `style_id`.

## 2. Tujuan Teknis

- State `doc_style_mode` dan `doc_selected_style_id` tersedia
- `generate_from_document()` bisa mengirim `style_id` ke backend
- State di-reset saat `reset_session()`

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/state.py` — tambah 2 state keys + reset
- `streamlit_app/api/client.py` — update `generate_from_document()` signature

**Yang tidak dikerjakan:**
- UI perubahan (task04-05)
- Auto-detect state (task05)

## 4. Langkah Implementasi

### 4.1 Update `state.py` — Tambah Default Keys

- [x] Tambahkan 2 key baru di dict `defaults` dalam `init_session_state()` (setelah `"session_list": []`):

```python
        "session_list": [],
        # Document style selection (Beta 0.1.12)
        "doc_style_mode": "active",        # "active" | "auto_detect"
        "doc_selected_style_id": None,     # ID style spesifik jika dipilih
```

### 4.2 Update `state.py` — Reset Keys

- [x] Tambahkan reset di `reset_session()` (setelah `st.session_state.history_session = None`):

```python
    st.session_state.history_session = None
    # Reset doc style selection
    st.session_state.doc_style_mode = "active"
    st.session_state.doc_selected_style_id = None
```

### 4.3 Update `client.py` — Tambah `style_id` Parameter

- [x] Ubah fungsi `generate_from_document()` (line 110-142):

```python
def generate_from_document(
    file_bytes: bytes,
    filename: str,
    context: str = "",
    style_id: str | None = None,  # ← BARU
) -> dict:
    """Generate TOR dari uploaded document.

    Args:
        file_bytes: Binary content of uploaded file
        filename: Original filename
        context: Optional additional context
        style_id: Optional style ID spesifik (default=aktif)

    Returns:
        dict: Response dengan TOR document
    """
    try:
        form_data = {"context": context}
        if style_id:
            form_data["style_id"] = style_id

        resp = requests.post(
            f"{API_URL}/generate/from-document",
            files={"file": (filename, file_bytes)},
            data=form_data,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Backend tidak bisa dihubungi."}
    except requests.Timeout:
        return {"error": "Request timeout."}
    except requests.HTTPError as e:
        try:
            return {"error": e.response.json().get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": f"HTTP Error: {e.response.status_code}"}
```

**Perubahan kunci:**
- Parameter `style_id` ditambahkan
- `data` dict sekarang dikonstruksi terpisah, `style_id` di-add hanya jika ada value

## 5. Output yang Diharapkan

```python
# Di Streamlit — tanpa style_id (backward compatible):
result = generate_from_document(file_bytes, "doc.pdf", "konteks")

# Di Streamlit — dengan style_id:
result = generate_from_document(file_bytes, "doc.pdf", "konteks", style_id="pelatihan_resmi")
```

## 6. Acceptance Criteria

- [x] `st.session_state` memiliki key `doc_style_mode` dan `doc_selected_style_id` setelah `init_session_state()`.
- [x] `reset_session()` mereset kedua key ke default.
- [x] `generate_from_document()` menerima parameter `style_id` opsional.
- [x] Tanpa `style_id` → request tidak mengirim field `style_id` (backward compatible).
- [x] Dengan `style_id` → request mengirim `style_id` di form data.
