# Beta 0.1.0 — Chat Engine (Local LLM Interviewer)

> **Modul**: Chat Engine
> **Versi**: beta0.1.0
> **Status**: Ready to Implement
> **Estimasi**: 3 hari kerja
> **Prasyarat**: Ollama terinstall, model `qwen2.5:7b-instruct` sudah di-pull

---

## 1. Overview

Chat Engine adalah **otak kiri** sistem — sebuah LLM lokal yang berperan sebagai _interviewer_ profesional. Modul ini TIDAK membuat TOR. Tugasnya:

1. Menerima pesan user melalui endpoint `/api/v1/chat`
2. Membangun prompt yang menyertakan system instruction, chat history, dan RAG context (jika tersedia)
3. Mengirim prompt ke Ollama (`qwen2.5:7b-instruct`) via REST API lokal
4. Mem-parse respons LLM menjadi JSON terstruktur dengan status routing
5. Menyimpan setiap turn percakapan ke database (SQLite via aiosqlite)
6. Menghitung completeness score dari data yang sudah terkumpul

Modul ini menghasilkan **3 jenis status output**:
- `NEED_MORE_INFO` → masih perlu data, kirim pertanyaan lanjutan
- `READY_TO_GENERATE` → data cukup, siap dikirim ke Gemini (beta0.1.2)
- `ESCALATE_TO_GEMINI` → user tidak kooperatif, serahkan ke Gemini (beta0.1.2)

---

## 2. Scope

### ✅ Yang dikerjakan di modul ini

| Item | Detail |
|---|---|
| Ollama Provider | Client async ke Ollama REST API (`localhost:11434`) |
| Prompt Builder | Compose system prompt + chat history + RAG context + user message |
| Response Parser | Extract JSON dari raw LLM output, handle mixed text+JSON |
| Session Manager | CRUD session + chat messages di SQLite |
| Completeness Score | Hitung persentase field TOR yang sudah terisi |
| Chat Endpoint | `POST /api/v1/chat` — endpoint utama modul ini |
| Session Endpoint | `GET /api/v1/session/{session_id}` — ambil state session |
| Retry Logic | Retry jika LLM gagal output JSON valid |
| Config | Pydantic Settings untuk semua parameter Ollama |

### ❌ Yang TIDAK dikerjakan di modul ini

| Item | Alasan |
|---|---|
| RAG retrieval | Dikerjakan di beta0.1.1. Chat engine menerima `rag_context: str | None` sebagai parameter |
| Gemini generation | Dikerjakan di beta0.1.2 |
| Decision engine routing | Dikerjakan di beta0.1.3. Chat engine hanya return status, tidak melakukan routing |
| Hybrid endpoint | Dikerjakan di beta0.1.4 |

---

## 3. Input / Output

### Input (dari client ke endpoint `/api/v1/chat`)

```json
{
    "session_id": "string | null",
    "message": "string (1-5000 chars)"
}
```

### Input Internal (dari modul lain ke ChatService)

```python
class ChatInput:
    session_id: str | None    # null = buat session baru
    message: str              # pesan dari user
    rag_context: str | None   # injeksi dari RAG pipeline (beta0.1.1)
```

### Output (dari endpoint ke client)

```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "chat",
    "message": "Baik, saya mengerti Anda ingin workshop AI. Berapa hari dan berapa pesertanya?",
    "state": {
        "status": "NEED_MORE_INFO",
        "turn_count": 1,
        "completeness_score": 0.17,
        "filled_fields": ["judul"],
        "missing_fields": ["latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
    },
    "extracted_data": {
        "judul": "Workshop Penerapan AI",
        "latar_belakang": null,
        "tujuan": null,
        "ruang_lingkup": null,
        "output": null,
        "timeline": null,
        "estimasi_biaya": null
    }
}
```

### Output Internal (dari ChatService ke modul lain)

```python
class ChatResult:
    session_id: str
    status: Literal["NEED_MORE_INFO", "READY_TO_GENERATE", "ESCALATE_TO_GEMINI"]
    message: str                         # pesan natural untuk user
    extracted_data: TORData              # data yang sudah terkumpul
    missing_fields: list[str]            # field yang masih kosong
    confidence: float                    # 0.0 - 1.0
    completeness_score: float            # 0.0 - 1.0
    raw_llm_response: str               # respons mentah dari LLM (untuk debug)
    escalation_reason: str | None        # alasan jika ESCALATE
```

---

## 4. Flow Logic

### Step-by-step: Satu Turn Chat

```
STEP 1: RECEIVE REQUEST
────────────────────────
Client mengirim POST /api/v1/chat
    body: { session_id: "abc" | null, message: "Saya mau buat TOR workshop AI" }

STEP 2: SESSION MANAGEMENT
────────────────────────────
IF session_id is null:
    → SessionManager.create() → new UUID, state="NEW", turn_count=0
    → Simpan ke SQLite table `sessions`
ELSE:
    → SessionManager.get(session_id)
    → IF not found: raise SessionNotFoundError (E006)
    → Ambil chat_history dari table `chat_messages`
    → Ambil extracted_data_json dari table `sessions`

STEP 3: BUILD PROMPT
──────────────────────
Compose messages array untuk Ollama:

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT_CHAT  # lihat Section 7 di blueprint
    },
    # inject RAG context (jika ada) sebagai system message tambahan
    {
        "role": "system",
        "content": f"## REFERENSI\n{rag_context}"  # dari beta0.1.1
    },
    # chat history (max 10 turn terakhir)
    {"role": "user", "content": "pesan turn 1"},
    {"role": "assistant", "content": "respons turn 1"},
    {"role": "user", "content": "pesan turn 2"},
    {"role": "assistant", "content": "respons turn 2"},
    # pesan terbaru
    {"role": "user", "content": message}
]

STEP 4: CALL OLLAMA
─────────────────────
request ke http://localhost:11434/api/chat

payload = {
    "model": "qwen2.5:7b-instruct",
    "messages": messages,
    "format": "json",         # Ollama native JSON mode
    "stream": false,
    "options": {
        "temperature": 0.3,   # rendah → konsisten output JSON
        "num_ctx": 4096       # context window
    }
}

timeout: 60 detik
IF ConnectionError → raise OllamaConnectionError (E001)
IF Timeout → retry 1x, lalu raise OllamaTimeoutError (E008)

STEP 5: PARSE RESPONSE
────────────────────────
raw_response = ollama_response["message"]["content"]

TRY:
    parsed = json.loads(raw_response)
    validate against LLMParsedResponse schema (Pydantic)
EXCEPT JSONDecodeError:
    # Strategi 1: Cari JSON di dalam teks mixed
    json_match = regex_extract_json(raw_response)
    IF json_match:
        parsed = json.loads(json_match)
    ELSE:
        # Strategi 2: Retry dengan prompt suffix
        IF retry_count < 2:
            retry_count += 1
            Tambahkan suffix ke message:
              "PENTING: Jawab HANYA dalam format JSON. Tidak ada teks lain."
            GOTO STEP 4
        ELSE:
            # Strategi 3: Fallback → treat sebagai NEED_MORE_INFO
            parsed = {
                "status": "NEED_MORE_INFO",
                "message": raw_response,  # tampilkan raw sebagai pesan
                "extracted_so_far": previous_extracted_data,
                "missing_fields": previous_missing_fields,
                "confidence": 0.0
            }

STEP 6: UPDATE SESSION
────────────────────────
SessionManager.append_message(
    session_id,
    role="user",
    content=message
)
SessionManager.append_message(
    session_id,
    role="assistant",
    content=parsed["message"],
    parsed_status=parsed["status"]
)

# Update extracted data (merge, jangan overwrite null)
IF parsed.status == "READY_TO_GENERATE":
    extracted = parsed["data"]
ELIF parsed.status == "NEED_MORE_INFO":
    extracted = merge_extracted_data(
        existing=session.extracted_data,
        new=parsed["extracted_so_far"]
    )
ELIF parsed.status == "ESCALATE_TO_GEMINI":
    extracted = parsed.get("partial_data", session.extracted_data)

# Calculate completeness score
completeness = calculate_completeness(extracted)

SessionManager.update(
    session_id,
    state=map_status_to_state(parsed.status),
    turn_count=session.turn_count + 1,
    extracted_data=extracted,
    completeness_score=completeness
)

STEP 7: RETURN RESPONSE
─────────────────────────
Return ChatResponse(
    session_id=session_id,
    type="chat",
    message=parsed["message"],
    state=SessionState(
        status=parsed["status"],
        turn_count=session.turn_count + 1,
        completeness_score=completeness,
        filled_fields=get_filled_fields(extracted),
        missing_fields=get_missing_fields(extracted)
    ),
    extracted_data=extracted
)
```

---

## 5. Data Structure

### 5.1 TORData — Data TOR yang dikumpulkan

```python
class TORData(BaseModel):
    """Schema data TOR yang dikumpulkan selama chat."""
    judul: str | None = None
    latar_belakang: str | None = None
    tujuan: str | None = None
    ruang_lingkup: str | None = None
    output: str | None = None
    timeline: str | None = None
    estimasi_biaya: str | None = None   # opsional

    def filled_fields(self) -> list[str]:
        return [f for f in REQUIRED_FIELDS if getattr(self, f) is not None]

    def missing_fields(self) -> list[str]:
        return [f for f in REQUIRED_FIELDS if getattr(self, f) is None]

REQUIRED_FIELDS = ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
OPTIONAL_FIELDS = ["estimasi_biaya"]
```

### 5.2 LLMParsedResponse — Respons terstruktur dari LLM

```python
class LLMParsedResponse(BaseModel):
    """Schema respons JSON yang diharapkan dari local LLM."""
    status: Literal["NEED_MORE_INFO", "READY_TO_GENERATE", "ESCALATE_TO_GEMINI"]
    message: str
    data: TORData | None = None                  # hanya jika READY_TO_GENERATE
    extracted_so_far: TORData | None = None       # hanya jika NEED_MORE_INFO
    partial_data: TORData | None = None           # hanya jika ESCALATE_TO_GEMINI
    missing_fields: list[str] | None = None
    reason: str | None = None                     # hanya jika ESCALATE_TO_GEMINI
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
```

### 5.3 Session — State percakapan

```python
class Session(BaseModel):
    id: str                             # UUID v4
    created_at: datetime
    updated_at: datetime
    state: Literal["NEW", "CHATTING", "READY", "ESCALATED", "GENERATING", "COMPLETED"]
    turn_count: int = 0
    completeness_score: float = 0.0
    extracted_data: TORData = TORData()
    generated_tor: str | None = None
    escalation_reason: str | None = None
    gemini_calls_count: int = 0
    total_tokens_local: int = 0
    total_tokens_gemini: int = 0
```

### 5.4 ChatMessage — Satu pesan di percakapan

```python
class ChatMessage(BaseModel):
    id: int                             # auto-increment
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    parsed_status: str | None = None    # status dari response LLM
    timestamp: datetime
```

### 5.5 SQLite Tables

```sql
-- TABLE: sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    state TEXT DEFAULT 'NEW' CHECK(state IN ('NEW','CHATTING','READY','ESCALATED','GENERATING','COMPLETED')),
    turn_count INTEGER DEFAULT 0,
    completeness_score REAL DEFAULT 0.0,
    extracted_data_json TEXT DEFAULT '{}',
    generated_tor TEXT,
    escalation_reason TEXT,
    gemini_calls_count INTEGER DEFAULT 0,
    total_tokens_local INTEGER DEFAULT 0,
    total_tokens_gemini INTEGER DEFAULT 0
);

-- TABLE: chat_messages
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
    content TEXT NOT NULL,
    parsed_status TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_session ON chat_messages(session_id);
CREATE INDEX idx_sessions_state ON sessions(state);
CREATE INDEX idx_sessions_updated ON sessions(updated_at);
```

---

## 6. API Contract

### 6.1 `POST /api/v1/chat`

**Request**:
```
POST /api/v1/chat
Content-Type: application/json

{
    "session_id": null,
    "message": "Saya ingin membuat TOR untuk workshop penerapan AI di instansi pemerintah"
}
```

**Response (200 OK) — NEED_MORE_INFO**:
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "chat",
    "message": "Bagus! Workshop AI di instansi pemerintah terdengar menarik. Saya perlu beberapa informasi tambahan:\n\n1. Berapa lama workshop ini akan berlangsung?\n2. Siapa target pesertanya dan berapa jumlahnya?",
    "state": {
        "status": "NEED_MORE_INFO",
        "turn_count": 1,
        "completeness_score": 0.17,
        "filled_fields": ["judul"],
        "missing_fields": ["latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
    },
    "extracted_data": {
        "judul": "Workshop Penerapan AI di Instansi Pemerintah",
        "latar_belakang": null,
        "tujuan": null,
        "ruang_lingkup": null,
        "output": null,
        "timeline": null,
        "estimasi_biaya": null
    }
}
```

**Response (200 OK) — READY_TO_GENERATE**:
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "chat",
    "message": "Terima kasih! Informasinya sudah lengkap. Saya siap membuatkan TOR untuk Anda.",
    "state": {
        "status": "READY_TO_GENERATE",
        "turn_count": 4,
        "completeness_score": 1.0,
        "filled_fields": ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"],
        "missing_fields": []
    },
    "extracted_data": {
        "judul": "Workshop Penerapan AI di Instansi Pemerintah",
        "latar_belakang": "Transformasi digital di sektor pemerintahan memerlukan...",
        "tujuan": "Meningkatkan pemahaman ASN tentang pemanfaatan AI...",
        "ruang_lingkup": "Pelatihan 3 hari untuk 30 peserta...",
        "output": "Sertifikat, modul pelatihan, prototype AI sederhana",
        "timeline": "3 hari, bulan Juli 2026",
        "estimasi_biaya": "Rp 50.000.000"
    }
}
```

**Response (422 Validation Error)**:
```json
{
    "detail": [
        {
            "loc": ["body", "message"],
            "msg": "String should have at least 1 character",
            "type": "string_too_short"
        }
    ]
}
```

**Response (503 Service Unavailable) — Ollama Down**:
```json
{
    "error": {
        "code": "E001",
        "message": "Tidak dapat terhubung ke Ollama. Pastikan Ollama berjalan dengan perintah: ollama serve",
        "details": "Connection refused: localhost:11434"
    }
}
```

---

### 6.2 `GET /api/v1/session/{session_id}`

**Request**:
```
GET /api/v1/session/550e8400-e29b-41d4-a716-446655440000
```

**Response (200 OK)**:
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-04-18T12:00:00Z",
    "updated_at": "2026-04-18T12:05:22Z",
    "state": "CHATTING",
    "turn_count": 3,
    "completeness_score": 0.50,
    "extracted_data": { ... },
    "chat_history": [
        {"role": "user", "content": "...", "timestamp": "..."},
        {"role": "assistant", "content": "...", "parsed_status": "NEED_MORE_INFO", "timestamp": "..."}
    ],
    "generated_tor": null,
    "metadata": {
        "gemini_calls_count": 0,
        "total_tokens_local": 2400,
        "total_tokens_gemini": 0
    }
}
```

**Response (404 Not Found)**:
```json
{
    "error": {
        "code": "E006",
        "message": "Session tidak ditemukan",
        "session_id": "invalid-uuid-here"
    }
}
```

---

## 7. Dependencies

### Dependency ke modul lain

| Modul | Interface | Wajib? | Fallback jika tidak ada |
|---|---|---|---|
| **beta0.1.1 (RAG)** | `RAGPipeline.retrieve(query) → str` | ❌ Opsional | Chat jalan tanpa RAG context (`rag_context = None`) |
| **beta0.1.2 (Gemini)** | Tidak ada dependency langsung | — | — |
| **beta0.1.3 (Decision Engine)** | Tidak ada dependency langsung | — | — |
| **beta0.1.4 (API Layer)** | Endpoint di-register ke FastAPI router | ✅ Wajib | Bisa test standalone dengan uvicorn |

### Interface yang disediakan untuk modul lain

```python
class ChatService:
    """Interface utama yang dipakai oleh modul lain."""

    async def process_message(
        self,
        session_id: str | None,
        message: str,
        rag_context: str | None = None
    ) -> ChatResult:
        """
        Process satu turn chat.
        Dipanggil oleh:
          - Chat endpoint (langsung)
          - Hybrid Controller (beta0.1.3/beta0.1.4)
        """
        ...

    async def get_session(self, session_id: str) -> Session:
        """Ambil state session lengkap."""
        ...

    async def get_chat_history(self, session_id: str) -> list[ChatMessage]:
        """Ambil chat history (untuk dikirim ke Gemini saat escalation)."""
        ...

    async def get_extracted_data(self, session_id: str) -> TORData:
        """Ambil data TOR yang sudah terkumpul (untuk dikirim ke Gemini saat generate)."""
        ...
```

### Library dependencies (Python packages)

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0
pydantic-settings>=2.0
ollama>=0.4.0              # Ollama Python SDK
aiosqlite>=0.20.0          # Async SQLite
httpx>=0.27.0              # Async HTTP (alternatif untuk Ollama jika SDK gagal)
python-dotenv>=1.0
```

### External dependencies

| Service | Versi | Install |
|---|---|---|
| Ollama | >= 0.3.0 | `curl -fsSL https://ollama.com/install.sh \| sh` |
| Model qwen2.5:7b-instruct | latest | `ollama pull qwen2.5:7b-instruct` |

---

## 8. Pseudocode

### 8.1 OllamaProvider — Komunikasi ke Ollama

```python
import ollama
from app.config import Settings

class OllamaProvider:
    def __init__(self, settings: Settings):
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
        self.model = settings.ollama_chat_model
        self.temperature = settings.ollama_temperature
        self.num_ctx = settings.ollama_num_ctx
        self.timeout = settings.ollama_timeout

    async def chat(self, messages: list[dict]) -> dict:
        """
        Kirim chat completion ke Ollama.
        Returns: {"content": str, "total_duration": int, "eval_count": int}
        """
        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=messages,
                    format="json",
                    options={
                        "temperature": self.temperature,
                        "num_ctx": self.num_ctx,
                    }
                ),
                timeout=self.timeout
            )
            return {
                "content": response["message"]["content"],
                "total_duration": response.get("total_duration", 0),
                "eval_count": response.get("eval_count", 0),
            }
        except asyncio.TimeoutError:
            raise OllamaTimeoutError(f"Ollama timeout after {self.timeout}s")
        except ConnectionError:
            raise OllamaConnectionError(
                "Tidak dapat terhubung ke Ollama. "
                "Pastikan menjalankan: ollama serve"
            )
```

### 8.2 PromptBuilder — Compose Prompt

```python
from app.ai.prompts.chat_system import SYSTEM_PROMPT_CHAT
from app.ai.prompts.rag_injection import RAG_CONTEXT_TEMPLATE

class PromptBuilder:
    @staticmethod
    def build_chat_messages(
        chat_history: list[ChatMessage],
        user_message: str,
        rag_context: str | None = None,
        max_history_turns: int = 10
    ) -> list[dict]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_CHAT}
        ]

        # Inject RAG context jika ada
        if rag_context:
            messages.append({
                "role": "system",
                "content": RAG_CONTEXT_TEMPLATE.format(rag_context=rag_context)
            })

        # Append recent chat history (max N turns)
        recent = chat_history[-(max_history_turns * 2):]
        for msg in recent:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Append current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages
```

### 8.3 ResponseParser — Extract JSON dari LLM

```python
import json
import re

class ResponseParser:
    @staticmethod
    def extract_json(raw: str) -> dict:
        """
        Tiga strategi parsing:
        1. Direct JSON parse
        2. Regex extract JSON dari mixed text
        3. Raise ParseError
        """
        # Strategi 1: Direct parse
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass

        # Strategi 2: Cari JSON object di dalam teks
        # Cari pattern { ... } yang valid
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, raw, re.DOTALL)

        for match in reversed(matches):  # ambil yang terpanjang/terakhir
            try:
                parsed = json.loads(match)
                if "status" in parsed:  # validasi minimal
                    return parsed
            except json.JSONDecodeError:
                continue

        # Strategi 3: Gagal total
        raise LLMParseError(
            f"Tidak dapat mengekstrak JSON dari respons LLM. "
            f"Raw response (first 200 chars): {raw[:200]}"
        )

    @staticmethod
    def validate_parsed(data: dict) -> LLMParsedResponse:
        """Validasi dan convert dict ke Pydantic model."""
        try:
            return LLMParsedResponse(**data)
        except ValidationError as e:
            raise LLMParseError(f"JSON valid tapi schema tidak sesuai: {e}")
```

### 8.4 SessionManager — CRUD Session

```python
import uuid
import json
from datetime import datetime
import aiosqlite

class SessionManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create(self) -> Session:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)",
                (session_id, now, now)
            )
            await db.commit()
        return Session(id=session_id, created_at=now, updated_at=now, state="NEW")

    async def get(self, session_id: str) -> Session:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = await cursor.fetchone()
            if not row:
                raise SessionNotFoundError(session_id)
            return self._row_to_session(row)

    async def append_message(self, session_id: str, role: str, content: str, parsed_status: str | None = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO chat_messages (session_id, role, content, parsed_status) VALUES (?, ?, ?, ?)",
                (session_id, role, content, parsed_status)
            )
            await db.commit()

    async def update(self, session_id: str, **kwargs):
        set_clauses = []
        values = []
        for key, value in kwargs.items():
            if key == "extracted_data":
                set_clauses.append("extracted_data_json = ?")
                values.append(value.model_dump_json() if hasattr(value, 'model_dump_json') else json.dumps(value))
            else:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        set_clauses.append("updated_at = ?")
        values.append(datetime.utcnow())
        values.append(session_id)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE sessions SET {', '.join(set_clauses)} WHERE id = ?",
                values
            )
            await db.commit()

    async def get_chat_history(self, session_id: str) -> list[ChatMessage]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            )
            rows = await cursor.fetchall()
            return [ChatMessage(**dict(row)) for row in rows]
```

### 8.5 CompletenessCalculator

```python
REQUIRED_FIELDS = ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
OPTIONAL_FIELDS = ["estimasi_biaya"]
OPTIONAL_BONUS = 0.05  # bonus per optional field yang terisi

def calculate_completeness(data: TORData) -> float:
    """
    Hitung completeness score.
    1.0 = semua required terisi.
    Bonus 0.05 per optional field.
    """
    filled_required = sum(
        1 for f in REQUIRED_FIELDS
        if getattr(data, f) is not None and getattr(data, f).strip() != ""
    )
    score = filled_required / len(REQUIRED_FIELDS)

    # Bonus optional
    for f in OPTIONAL_FIELDS:
        val = getattr(data, f)
        if val is not None and val.strip() != "":
            score = min(1.0, score + OPTIONAL_BONUS)

    return round(score, 2)
```

### 8.6 ChatService — Orchestrator

```python
class ChatService:
    def __init__(
        self,
        ollama: OllamaProvider,
        session_mgr: SessionManager,
        prompt_builder: PromptBuilder,
        parser: ResponseParser,
    ):
        self.ollama = ollama
        self.session_mgr = session_mgr
        self.prompt_builder = prompt_builder
        self.parser = parser

    async def process_message(
        self,
        session_id: str | None,
        message: str,
        rag_context: str | None = None,
    ) -> ChatResult:
        # Step 1: Session
        if session_id is None:
            session = await self.session_mgr.create()
        else:
            session = await self.session_mgr.get(session_id)

        # Step 2: Chat history
        history = await self.session_mgr.get_chat_history(session.id)

        # Step 3: Build prompt
        messages = self.prompt_builder.build_chat_messages(
            chat_history=history,
            user_message=message,
            rag_context=rag_context,
        )

        # Step 4: Call Ollama (with retry)
        parsed = await self._call_with_retry(messages, max_retries=2)

        # Step 5: Update session
        await self.session_mgr.append_message(session.id, "user", message)
        await self.session_mgr.append_message(
            session.id, "assistant", parsed.message, parsed.status
        )

        # Extract & merge data
        extracted = self._merge_extracted(session.extracted_data, parsed)
        completeness = calculate_completeness(extracted)

        await self.session_mgr.update(
            session.id,
            state=self._map_state(parsed.status),
            turn_count=session.turn_count + 1,
            extracted_data=extracted,
            completeness_score=completeness,
        )

        # Step 6: Build result
        return ChatResult(
            session_id=session.id,
            status=parsed.status,
            message=parsed.message,
            extracted_data=extracted,
            missing_fields=extracted.missing_fields(),
            confidence=parsed.confidence,
            completeness_score=completeness,
            raw_llm_response=parsed.model_dump_json(),
            escalation_reason=parsed.reason,
        )

    async def _call_with_retry(self, messages: list[dict], max_retries: int) -> LLMParsedResponse:
        """Call Ollama dengan retry jika JSON parse gagal."""
        last_error = None
        for attempt in range(max_retries + 1):
            raw = await self.ollama.chat(messages)
            try:
                data = self.parser.extract_json(raw["content"])
                return self.parser.validate_parsed(data)
            except LLMParseError as e:
                last_error = e
                if attempt < max_retries:
                    # Append instruction to force JSON
                    messages.append({
                        "role": "user",
                        "content": "PENTING: Jawab HANYA dalam format JSON yang diminta. Tanpa teks tambahan."
                    })
                    await asyncio.sleep(1)  # backoff
        raise last_error

    def _merge_extracted(self, existing: TORData, parsed: LLMParsedResponse) -> TORData:
        """Merge data baru ke existing tanpa overwrite non-null dengan null."""
        new_data = parsed.data or parsed.extracted_so_far or parsed.partial_data or TORData()
        merged = existing.model_copy()
        for field in REQUIRED_FIELDS + OPTIONAL_FIELDS:
            new_val = getattr(new_data, field)
            if new_val is not None and new_val.strip() != "":
                setattr(merged, field, new_val)
        return merged

    def _map_state(self, status: str) -> str:
        return {
            "NEED_MORE_INFO": "CHATTING",
            "READY_TO_GENERATE": "READY",
            "ESCALATE_TO_GEMINI": "ESCALATED",
        }.get(status, "CHATTING")
```

---

## 9. Edge Cases

### Edge Case 1: Ollama Tidak Berjalan

**Trigger**: User kirim chat tapi `ollama serve` belum dijalankan.

**Handling**:
```python
try:
    response = await self.ollama.chat(messages)
except OllamaConnectionError:
    raise HTTPException(
        status_code=503,
        detail={
            "code": "E001",
            "message": "Tidak dapat terhubung ke Ollama. Jalankan: ollama serve",
            "details": "Connection refused: localhost:11434"
        }
    )
```

### Edge Case 2: LLM Output Non-JSON Berulang

**Trigger**: Model terus mengeluarkan teks bebas meski format: json sudah diset.

**Handling**:
- Retry 2x dengan prompt tambahan
- Jika tetap gagal, fallback: gunakan raw text sebagai `message`, set status `NEED_MORE_INFO`, pertahankan extracted data dari turn sebelumnya
- Log warning untuk monitoring

```python
# Fallback response
fallback = LLMParsedResponse(
    status="NEED_MORE_INFO",
    message=raw_response[:500],  # trim agar tidak terlalu panjang
    extracted_so_far=session.extracted_data,
    missing_fields=session.extracted_data.missing_fields(),
    confidence=0.0
)
```

### Edge Case 3: Session Expired / Not Found

**Trigger**: User kirim session_id yang sudah dihapus atau tidak valid.

**Handling**:
```python
try:
    session = await self.session_mgr.get(session_id)
except SessionNotFoundError:
    raise HTTPException(
        status_code=404,
        detail={
            "code": "E006",
            "message": "Session tidak ditemukan. Mulai percakapan baru.",
            "session_id": session_id
        }
    )
```

### Edge Case 4: User Kirim Pesan Kosong atau Terlalu Panjang

**Trigger**: `message: ""` atau `message: "..." (>5000 chars)`

**Handling**: Pydantic validation otomatis di FastAPI
```python
class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(..., min_length=1, max_length=5000)
```

### Edge Case 5: Ollama Timeout (Model Lambat di Hardware Rendah)

**Trigger**: Model 7B butuh >60 detik di mesin dengan RAM terbatas.

**Handling**:
```python
# Retry 1x, lalu error
except asyncio.TimeoutError:
    if retry_count == 0:
        retry_count += 1
        # retry once
    else:
        raise HTTPException(
            status_code=504,
            detail={
                "code": "E008",
                "message": f"Ollama tidak merespons dalam {self.timeout}s. "
                           "Coba model yang lebih kecil atau tingkatkan hardware.",
            }
        )
```

### Edge Case 6: Concurrent Access ke Session yang Sama

**Trigger**: Dua request dengan session_id yang sama masuk bersamaan.

**Handling**:
- SQLite WAL mode untuk concurrent reads
- Optimistic locking: cek `updated_at` sebelum update, jika berubah → retry
- Pada tahap awal, ini jarang terjadi karena single-user per session

---

## 10. File yang Harus Dibuat

```
app/
├── config.py                      # Pydantic Settings
├── main.py                        # FastAPI entry point + lifespan
├── ai/
│   ├── __init__.py
│   ├── base.py                    # BaseLLMProvider ABC
│   ├── ollama_provider.py         # OllamaProvider implementation
│   └── prompts/
│       ├── __init__.py
│       ├── chat_system.py         # SYSTEM_PROMPT_CHAT constant
│       └── rag_injection.py       # RAG_CONTEXT_TEMPLATE constant
├── core/
│   ├── __init__.py
│   ├── response_parser.py         # ResponseParser class
│   ├── session_manager.py         # SessionManager class
│   └── completeness.py            # calculate_completeness()
├── models/
│   ├── __init__.py
│   ├── requests.py                # ChatRequest, etc.
│   ├── responses.py               # ChatResponse, SessionState, etc.
│   ├── session.py                 # Session, ChatMessage
│   └── tor.py                     # TORData, LLMParsedResponse
├── db/
│   ├── __init__.py
│   ├── database.py                # init_db(), get_db()
│   └── migrations/
│       └── 001_initial.sql        # CREATE TABLE statements
├── api/
│   ├── __init__.py
│   ├── router.py                  # include all route modules
│   └── routes/
│       ├── __init__.py
│       ├── chat.py                # POST /api/v1/chat
│       ├── session.py             # GET /api/v1/session/{id}
│       └── health.py              # GET /api/v1/health
├── services/
│   ├── __init__.py
│   └── chat_service.py            # ChatService orchestrator
├── utils/
│   ├── __init__.py
│   ├── logger.py                  # structured logging setup
│   └── errors.py                  # custom exception classes
│
├── .env.example
└── requirements.txt
```

---

## 11. Cara Test Modul Ini Secara Standalone

```bash
# 1. Pastikan Ollama berjalan
ollama serve

# 2. Pull model (jika belum)
ollama pull qwen2.5:7b-instruct

# 3. Jalankan server
cd ai-agent-hybrid
uvicorn app.main:app --reload --port 8000

# 4. Test health check
curl http://localhost:8000/api/v1/health

# 5. Test chat (turn 1 — session baru)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Saya mau buat TOR untuk workshop AI"}'

# 6. Test chat (turn 2 — lanjut session)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID_DARI_RESPONSE", "message": "3 hari, 30 peserta, budget 50 juta"}'

# 7. Cek session state
curl http://localhost:8000/api/v1/session/SESSION_ID
```
