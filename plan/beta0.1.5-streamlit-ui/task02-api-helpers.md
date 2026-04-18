# Task 02 — API Helper Functions

## 1. Judul Task

Buat helper functions untuk komunikasi Streamlit → FastAPI: `send_message()`, `check_health()`, `force_generate()`.

## 2. Deskripsi

Abstraksi semua HTTP call ke backend menjadi fungsi-fungsi reusable. Includes error handling untuk connection error, timeout, dan HTTP errors. Fungsi-fungsi ini akan dipanggil dari main app.

## 3. Tujuan Teknis

- `send_message(session_id, message, options)` → panggil POST /api/v1/hybrid
- `check_health()` → panggil GET /api/v1/health
- `force_generate(session_id)` → panggil hybrid dengan force_generate=True
- Error handling: connection error, timeout, HTTP error → return dict dengan key "error"

## 4. Scope

### Yang dikerjakan
- Tambah helper functions di `streamlit_app.py`
- Error handling untuk semua failure scenarios

### Yang tidak dikerjakan
- UI yang memanggil fungsi ini (task selanjutnya)

## 5. Langkah Implementasi

### Step 1: Tambah import dan helper functions di `streamlit_app.py`

```python
import requests

def send_message(session_id: str | None, message: str, options: dict = None) -> dict:
    """Kirim pesan ke hybrid endpoint."""
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    if options:
        payload["options"] = options

    try:
        resp = requests.post(f"{API_URL}/hybrid", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Backend tidak bisa dihubungi. Pastikan server berjalan di port 8000."}
    except requests.Timeout:
        return {"error": "Request timeout. LLM mungkin sedang sibuk, coba lagi."}
    except requests.HTTPError as e:
        try:
            error_data = e.response.json()
            return {"error": error_data.get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": f"HTTP Error: {e.response.status_code}"}


def check_health() -> dict:
    """Cek status backend."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        return resp.json()
    except Exception:
        return {"status": "unreachable"}


def force_generate(session_id: str) -> dict:
    """Force generate TOR."""
    return send_message(session_id, "generate", options={"force_generate": True})
```

### Step 2: Verifikasi

```python
# Test manual di python console:
# from streamlit_app import send_message, check_health
# health = check_health()
# assert health["status"] in ("healthy", "degraded", "unreachable")
```

## 6. Output yang Diharapkan

3 helper functions yang bisa dipanggil dari bagian UI manapun.

## 7. Dependencies

- **Task 01** — file `streamlit_app.py` sudah ada

## 8. Acceptance Criteria

- [ ] `send_message()` return dict dari API atau dict dengan key "error"
- [ ] `check_health()` return health status atau "unreachable"
- [ ] `force_generate()` panggil hybrid dengan `force_generate: true`
- [ ] Timeout diset ke 120s untuk message, 5s untuk health
- [ ] Connection error di-handle gracefully

## 9. Estimasi

**Low** — ~30 menit
