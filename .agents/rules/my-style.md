---
trigger: always_on
glob: "*.py, *.md"
description: Aturan coding style dan konvensi untuk project AI Agent Hybrid.
---

# Aturan Gaya Pengkodean (Coding Style)

1. **Python as the Main Backend**: 
   - Gunakan typing hints yang ketat pada fungsi (`def do_something(name: str) -> bool:`).
   - Pastikan prinsip asinkron dipertahankan. Gunakan `async def` dan `await` di service/controller.
2. **Pydantic Models**:
   - Selalu gunakan Pydantic `BaseModel` (V2) untuk validasi IO. 
   - Model untuk request di `models/api.py`, model untuk database di `models/db.py`.
3. **Modularitas (Separation of Concerns)**:
   - **Routes**: Hanya berisi dekorator endpoint (`@app.get`) dan meneruskan request ke service.
   - **Services**: Logika bisnis utama diletakkan di folder `/app/services/`.
   - **AI Providers**: Modul integrasi ke Ollama/Gemini berada di `/app/ai/`.
   - **Prompts**: Sistem prompt berlokasi di `/app/ai/prompts/` dalam format konstanta file Python.
4. **Error Handling**:
   - Return status menggunakan custom `AppError`. Jangan menggunakan `print()`, pakailah python `logging`.
5. **Streamlit Frontend (UI)**:
   - Pecah komponen visual ke `/streamlit_app/components/`. State diatur di `state.py`.
