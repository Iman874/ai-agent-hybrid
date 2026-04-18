# Task 12 — Integrasi RAGPipeline ke ChatService

## 1. Judul Task

Integrasikan `RAGPipeline` ke dalam `ChatService.process_message()` agar context dari dokumen referensi otomatis di-inject ke prompt LLM.

## 2. Deskripsi

Saat ini `ChatService.process_message()` menerima parameter `rag_context: str | None` tapi selalu mendapat `None`. Task ini mengubah chat endpoint dan `ChatService` agar memanggil `RAGPipeline.retrieve()` menggunakan pesan user sebagai query, lalu hasilnya di-pass ke `PromptBuilder.build_chat_messages()`.

## 3. Tujuan Teknis

- `ChatService` menerima injeksi `RAGPipeline` yang optional (jika tidak ada → chat tetap berjalan)
- `process_message()` memanggil `rag_pipeline.retrieve(message)` sebelum build prompt
- Jika RAG tidak available atau return `None` → chat berjalan normal tanpa RAG
- Chat endpoint update: pass `rag_pipeline` saat instantiate `ChatService`

## 4. Scope

### Yang dikerjakan
- Update `app/services/chat_service.py` — tambahkan `rag_pipeline` parameter optional
- Update `app/main.py` — pass `rag_pipeline` ke `ChatService`
- Update `app/api/routes/chat.py` — tidak banyak perubahan (service sudah handle RAG)

### Yang tidak dikerjakan
- Re-implement ChatService dari awal
- Perubahan logic retrieval (itu di RAGPipeline)

## 5. Langkah Implementasi

### Step 1: Update `app/services/chat_service.py`

Tambahkan `rag_pipeline` sebagai optional dependency:

```python
from app.rag.pipeline import RAGPipeline  # import baru

class ChatService:
    def __init__(
        self,
        ollama: OllamaProvider,
        session_mgr: SessionManager,
        prompt_builder: PromptBuilder,
        parser: ResponseParser,
        rag_pipeline: RAGPipeline | None = None,  # TAMBAHKAN INI
    ):
        self.ollama = ollama
        self.session_mgr = session_mgr
        self.prompt_builder = prompt_builder
        self.parser = parser
        self.rag_pipeline = rag_pipeline  # TAMBAHKAN INI
        self._logger = setup_logger("chat")
```

Di method `process_message()`, ubah bagian RAG context:

```python
async def process_message(
    self,
    session_id: str | None,
    message: str,
    rag_context: str | None = None,
) -> ChatResult:
    # ... (step session management sama seperti sebelumnya) ...

    # === RAG RETRIEVAL (baru) ===
    if rag_context is None and self.rag_pipeline is not None:
        try:
            rag_context = await self.rag_pipeline.retrieve(query=message)
            if rag_context:
                self._logger.debug(
                    f"RAG context retrieved: {len(rag_context)} chars"
                )
        except Exception as e:
            self._logger.warning(f"RAG retrieval failed, continuing without: {e}")
            rag_context = None

    # === BUILD PROMPT (sama seperti sebelumnya, tapi sekarang rag_context bisa berisi data) ===
    messages = self.prompt_builder.build_chat_messages(
        chat_history=chat_history,
        user_message=message,
        rag_context=rag_context,  # sudah di-populate dari RAGPipeline
    )
    # ... sisa flow sama ...
```

### Step 2: Update `app/main.py` lifespan

Ubah instantiasi `ChatService` untuk pass `rag_pipeline`:

```python
# Sebelum:
app.state.chat_service = ChatService(
    ollama=ollama_provider,
    session_mgr=session_mgr,
    prompt_builder=PromptBuilder(),
    parser=ResponseParser(),
)

# Sesudah:
app.state.chat_service = ChatService(
    ollama=ollama_provider,
    session_mgr=session_mgr,
    prompt_builder=PromptBuilder(),
    parser=ResponseParser(),
    rag_pipeline=rag_pipeline,    # inject RAGPipeline
)
```

> **Catatan**: Pastikan `rag_pipeline` di-init sebelum `ChatService` di lifespan.

### Step 3: Verifikasi dengan TestClient (tanpa Ollama)

```python
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Mock RAGPipeline untuk test tanpa Ollama
mock_rag = MagicMock()
mock_rag.retrieve = AsyncMock(return_value=(
    "## REFERENSI\n\n---\n[Referensi 1: tor_example.md (similarity: 0.89)]\n"
    "Workshop ini bertujuan meningkatkan kompetensi ASN...\n---"
))

# Attach ke app state (sebelum test request)
from app.main import app
app.state.rag_pipeline = mock_rag

# Verifikasi bahwa service menggunakan mock rag
with TestClient(app) as client:
    # Hanya cek startup berhasil (karena chat butuh Ollama live)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    print("Health check OK dengan RAGPipeline")

print("Integration wiring test PASSED")
```

### Step 4: Manual end-to-end test (dengan Ollama + bge-m3)

1. Pastikan Ollama running (`ollama serve`)
2. Pastikan `bge-m3` sudah di-pull (`ollama pull bge-m3`)
3. Ingest minimal 1 dokumen:
   ```bash
   python scripts/ingest_documents.py --dir data/documents/examples --category tor_example
   ```
4. Jalankan server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. Kirim chat request:
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Saya mau buat TOR workshop AI untuk ASN"}'
   ```
6. Cek di log bahwa `"RAG context retrieved: XXX chars"` muncul

## 6. Output yang Diharapkan

Log saat chat dengan dokumen ter-ingest:
```
2026-04-XX HH:MM:SS | ai-agent-hybrid.chat | DEBUG | RAG context retrieved: 487 chars
2026-04-XX HH:MM:SS | ai-agent-hybrid.chat | INFO  | Calling Ollama model: qwen2.5:7b-instruct
```

Response dari `/chat` bisa lebih akurat karena LLM mendapat referensi TOR nyata.

## 7. Dependencies

- **Task 08** — `RAGPipeline`
- **Task 11 (beta0.1.0)** — `ChatService` yang sudah ada
- **Task 10** — RAGPipeline sudah di-init di `app.state`

## 8. Acceptance Criteria

- [ ] `ChatService` bisa diinstansiasi dengan atau tanpa `rag_pipeline`
- [ ] Jika `rag_pipeline=None` → chat berjalan normal (tidak error)
- [ ] Jika `rag_pipeline` ada → `retrieve()` dipanggil sebelum build prompt
- [ ] Jika RAG return `None` (tidak ada konteks relevan) → chat tetap berjalan
- [ ] Jika RAG error/exception → chat tetap berjalan (fallback gracefully)
- [ ] Log menunjukkan `"RAG context retrieved"` ketika ada hit
- [ ] Server startup tidak error setelah perubahan ini

## 9. Estimasi

**Low** — ~1 jam (perubahan minimal, mostly wiring)
