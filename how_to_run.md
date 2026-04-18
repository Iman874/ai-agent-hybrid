# Cara Menjalankan AI Agent Hybrid (Chat Engine)

Project ini menggunakan Python virtual environment (`venv`) agar library yang terinstall tidak bercampur dengan environment lokal komputer Anda. 

Karena sebelumnya muncul pesan Error `ModuleNotFoundError: No module named 'pydantic_settings'` saat Anda menjalankan dengan *base uvicorn*, itu berarti Anda menjalankan server di luar Virtual Environment. 

Berikut adalah panduan lengkap cara menjalankannya dengan aman:

## 1. Pastikan Ollama Sedang Berjalan
Chat Engine berjalan bergantung secara penuh pada localhost LLM yang diserver oleh Ollama.
Buka tab terminal baru (bisa CMD atau PowerShell), lalu jalankan:
```bash
ollama serve
```
*(Pastikan Anda tidak menutup terminal ini selama aplikasi berjalan).*

## 2. Aktifkan Virtual Environment
Buka terminal di dalam root folder projek ini (`d:\Iman874\Documents\Github\ai-agent-hybrid`).
Untuk Windows PowerShell, jalankan perintah ini:
```powershell
.\venv\Scripts\activate
```
_Jika berhasil, Anda akan melihat awalan `(venv)` di kiri command line._

## 3. Jalankan FastAPI Server
Setelah `venv` mulai aktif, Anda bisa langsung memulai Uvicorn Server.
```powershell
uvicorn app.main:app --reload --port 8000
```
*(Catatan: jika `uvicorn` tidak dikenali padahal sudah aktif di venv, Anda bisa menggunakan `.\venv\Scripts\uvicorn.exe app.main:app --reload`).*

## 4. Buka Browser
Buka browser dan akses antarmuka testing dokumentasi dari FastAPI Swagger:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## (Opsional) Testing End-to-End dengan Postman / Curl
Jika Anda ingin mengetes Endpoint utama (Session Baru):

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Halo, saya mau buat instruksi workshop Machine Learning nih."}'
```

---
### Command Berguna Lainnya
Jika sewaktu-waktu Anda perlu mengaktifkan ulang dependensi:
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Jika Anda perlu menjalankan Test Suite (PyTest):
```powershell
.\venv\Scripts\pytest.exe tests/ -v
```
