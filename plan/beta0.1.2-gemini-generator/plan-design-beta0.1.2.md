# Beta 0.1.2 — Gemini Generator (TOR Document Generation)

> **Modul**: Gemini Generator
> **Versi**: beta0.1.2
> **Status**: Ready to Implement
> **Estimasi**: 2 hari kerja
> **Prasyarat**: beta0.1.0 (Chat Engine) berjalan, Gemini API key tersedia

---

## 1. Overview

Gemini Generator adalah **otak kanan** sistem — AI profesional yang menghasilkan dokumen TOR berkualitas proposal resmi. Modul ini:

1. Menerima data terstruktur (dari Chat Engine) ATAU full chat history (saat escalation)
2. Membangun prompt Gemini yang spesifik sesuai mode (`standard` atau `escalation`)
3. Meng-inject referensi dari RAG (jika tersedia) sebagai contoh style
4. Memanggil Google Gemini API (`gemini-2.0-flash`) untuk generate TOR
5. Post-processing: validasi struktur, hitung word count, format final
6. Menyimpan hasil ke cache (SQLite) agar tidak perlu re-generate
7. Meng-enforce cost control (max calls per session, per hour)

Modul ini **hanya dipanggil** saat:
- Chat Engine menghasilkan status `READY_TO_GENERATE` (standard mode)
- Decision Engine memutuskan escalation `ESCALATE_TO_GEMINI` (escalation mode)
- User manual trigger via `POST /api/v1/generate`

---

## 2. Scope

### ✅ Yang dikerjakan di modul ini

| Item | Detail |
|---|---|
| GeminiProvider | Client async ke Google Gemini API via SDK |
| Standard Mode Prompt | Prompt untuk generate TOR dari data JSON lengkap |
| Escalation Mode Prompt | Prompt untuk generate TOR dari chat history (data tidak lengkap) |
| PostProcessor | Validasi struktur TOR, word count, formatting |
| TOR Cache | Simpan hasil generate ke SQLite, serve dari cache jika ada |
| Cost Controller | Rate limiting: max calls per session & per hour |
| Generate Endpoint | `POST /api/v1/generate` |

### ❌ Yang TIDAK dikerjakan di modul ini

| Item | Alasan |
|---|---|
| Auto-trigger generate | Itu tugas Decision Engine (beta0.1.3) |
| PDF export | Ditunda ke roadmap v1.0 |
| Multi-model fallback (GPT, Claude) | Ditunda ke roadmap v1.0 |
| Streaming response | Terlalu kompleks untuk v0.1 |

---

## 3. Input / Output

### Input: Standard Mode

```python
class GenerateInput:
    session_id: str
    mode: Literal["standard", "escalation"]
    data: TORData                       # dari Chat Engine extracted_data
    rag_examples: str | None            # dari RAG Pipeline
    chat_history: list[ChatMessage]     # hanya dipakai di escalation mode
```

**data (TORData) contoh — Standard Mode**:
```json
{
    "judul": "Workshop Penerapan AI di Instansi Pemerintah",
    "latar_belakang": "Transformasi digital di sektor pemerintahan memerlukan pemahaman tentang AI...",
    "tujuan": "Meningkatkan kompetensi ASN dalam pemanfaatan AI generatif",
    "ruang_lingkup": "Pelatihan 3 hari untuk 30 peserta level manajerial",
    "output": "Sertifikat, modul pelatihan, prototype AI sederhana per kelompok",
    "timeline": "3 hari, bulan Juli 2026",
    "estimasi_biaya": "Rp 50.000.000"
}
```

### Input: Escalation Mode

```json
{
    "session_id": "...",
    "mode": "escalation",
    "chat_history": [
        {"role": "user", "content": "buat TOR AI"},
        {"role": "assistant", "content": "Bisa jelaskan lebih detail...?"},
        {"role": "user", "content": "terserah aja"}
    ],
    "partial_data": {
        "judul": "TOR AI",
        "latar_belakang": null,
        "tujuan": null,
        "ruang_lingkup": null,
        "output": null,
        "timeline": null,
        "estimasi_biaya": null
    }
}
```

### Output

```python
class GenerateResult:
    session_id: str
    tor_document: TORDocument
    cached: bool                         # True jika disajikan dari cache

class TORDocument:
    format: str = "markdown"             # selalu markdown
    content: str                         # full TOR dalam markdown
    metadata: TORMetadata

class TORMetadata:
    generated_by: str                    # "gemini-2.0-flash"
    mode: str                            # "standard" | "escalation"
    word_count: int
    generation_time_ms: int
    has_assumptions: bool                # True jika ada tag [ASUMSI]
    prompt_tokens: int
    completion_tokens: int
```

**TOR Output contoh (standard mode)**:
```markdown
# TERM OF REFERENCE (TOR)
# Workshop Penerapan AI di Instansi Pemerintah

## 1. Latar Belakang

Transformasi digital di sektor pemerintahan Indonesia saat ini memasuki
fase akselerasi. Pemerintah melalui Perpres No. 95 Tahun 2018 tentang
Sistem Pemerintahan Berbasis Elektronik (SPBE) telah menetapkan roadmap...

[... dst lengkap 500+ kata ...]

## 7. Penutup

Demikian Term of Reference ini disusun sebagai acuan pelaksanaan
Workshop Penerapan AI di Instansi Pemerintah. Dokumen ini dapat
disesuaikan sesuai dengan kebutuhan dan kondisi di lapangan.
```

---

## 4. Flow Logic

### Step-by-step: Generate TOR

```
STEP 1: RECEIVE REQUEST
─────────────────────────
Client / Decision Engine mengirim GenerateInput
    ├─► session_id: "abc-123"
    ├─► mode: "standard" | "escalation"
    └─► data / chat_history

STEP 2: COST CONTROL CHECK
────────────────────────────
CostController.check(session_id):
    ├─► Ambil gemini_calls_count dari session
    │   IF gemini_calls_count >= MAX_PER_SESSION (3):
    │       raise RateLimitError("Batas Gemini per sesi tercapai")
    │
    ├─► Ambil global call count per jam
    │   IF global_hourly_count >= MAX_PER_HOUR (20):
    │       raise RateLimitError("Batas Gemini per jam tercapai")
    │
    └─► OK, lanjut

STEP 3: CHECK CACHE
──────────────────────
IF mode == "standard":
    cached_tor = Cache.get(session_id)
    IF cached_tor exists AND force_regenerate is False:
        return GenerateResult(tor=cached_tor, cached=True)
        # Skip Gemini call, hemat biaya

STEP 4: BUILD PROMPT
───────────────────────
IF mode == "standard":
    prompt = PromptBuilder.build_gemini_standard(
        data=tor_data,
        rag_examples=rag_examples   # dari RAG Pipeline
    )
    # Inject data JSON ke template prompt
    # Inject RAG examples sebagai referensi style

ELIF mode == "escalation":
    formatted_history = format_chat_history(chat_history)
    prompt = PromptBuilder.build_gemini_escalation(
        chat_history=formatted_history,
        partial_data=partial_data,
        rag_examples=rag_examples
    )
    # Inject full percakapan
    # Instruksi: gunakan asumsi terbaik, tandai [ASUMSI]

STEP 5: CALL GEMINI API
──────────────────────────
start_time = time.monotonic()

TRY (max retries: 3, backoff: [2, 5, 10] seconds):
    response = await gemini_client.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 4096,
            "top_p": 0.95,
            "top_k": 40,
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    )
    raw_tor = response.text
    generation_time = (time.monotonic() - start_time) * 1000

EXCEPT google.api_core.exceptions.ResourceExhausted:
    → RateLimitError (E003): "Quota Gemini habis. Coba lagi nanti."
EXCEPT google.api_core.exceptions.InvalidArgument:
    → APIKeyError (E004): "API key Gemini tidak valid."
EXCEPT asyncio.TimeoutError:
    → TimeoutError (E008): retry atau error

STEP 6: POST-PROCESSING
──────────────────────────
PostProcessor.process(raw_tor):
    ├─► validate_structure(): cek minimal ada heading ## 1 s/d ## 7
    │   IF missing sections:
    │       log warning, tapi JANGAN reject — kualitas masih acceptable
    │
    ├─► count_words(): hitung word count
    │   IF word_count < 300:
    │       log warning "TOR terlalu pendek"
    │
    ├─► check_assumptions(): cari tag [ASUMSI]
    │   has_assumptions = "[ASUMSI]" in raw_tor
    │
    ├─► clean_formatting():
    │       - Remove markdown code block wrapping jika ada (```markdown ... ```)
    │       - Normalize heading levels
    │       - Trim whitespace
    │
    └─► Output: cleaned TOR content + metadata

STEP 7: CACHE & UPDATE SESSION
─────────────────────────────────
# Simpan ke cache
Cache.store(session_id, tor_content, model, mode)

# Update session
SessionManager.update(
    session_id,
    state="COMPLETED",
    generated_tor=tor_content,
    gemini_calls_count=session.gemini_calls_count + 1,
    total_tokens_gemini=session.total_tokens_gemini + response.usage.total_tokens
)

STEP 8: RETURN RESULT
───────────────────────
Return GenerateResult(
    session_id=session_id,
    tor_document=TORDocument(
        format="markdown",
        content=tor_content,
        metadata=TORMetadata(
            generated_by="gemini-2.0-flash",
            mode=mode,
            word_count=word_count,
            generation_time_ms=generation_time,
            has_assumptions=has_assumptions,
            prompt_tokens=response.usage_metadata.prompt_token_count,
            completion_tokens=response.usage_metadata.candidates_token_count,
        )
    ),
    cached=False,
)
```

---

## 5. Data Structure

### 5.1 GenerateRequest (API Input)

```python
class GenerateRequest(BaseModel):
    session_id: str
    mode: Literal["standard", "escalation"] = "standard"
    data_override: TORData | None = None     # optional override
    force_regenerate: bool = False            # bypass cache
```

### 5.2 TORDocument (Output)

```python
class TORDocument(BaseModel):
    format: str = "markdown"
    content: str
    metadata: TORMetadata

class TORMetadata(BaseModel):
    generated_by: str                    # "gemini-2.0-flash"
    mode: str                            # "standard" | "escalation"
    word_count: int
    generation_time_ms: int
    has_assumptions: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
```

### 5.3 GenerateResponse (API Output)

```python
class GenerateResponse(BaseModel):
    session_id: str
    type: Literal["generate"] = "generate"
    message: str                              # "TOR berhasil dibuat."
    tor_document: TORDocument
    cached: bool = False
    state: SessionState
```

### 5.4 TOR Cache (SQLite)

```sql
CREATE TABLE tor_cache (
    session_id TEXT PRIMARY KEY,
    tor_content TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_used TEXT NOT NULL,
    mode TEXT NOT NULL,
    word_count INTEGER,
    generation_time_ms INTEGER,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
```

### 5.5 Gemini Call Log (untuk cost tracking)

```sql
CREATE TABLE gemini_call_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model TEXT NOT NULL,
    mode TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    duration_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_gemini_calls_time ON gemini_call_log(called_at);
```

---

## 6. API Contract

### `POST /api/v1/generate`

**Request**:
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "mode": "standard",
    "force_regenerate": false
}
```

**Response (200 OK) — Standard Mode**:
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "generate",
    "message": "TOR berhasil dibuat berdasarkan informasi yang Anda berikan.",
    "tor_document": {
        "format": "markdown",
        "content": "# TERM OF REFERENCE (TOR)\n# Workshop Penerapan AI di Instansi Pemerintah\n\n## 1. Latar Belakang\n\nTransformasi digital...",
        "metadata": {
            "generated_by": "gemini-2.0-flash",
            "mode": "standard",
            "word_count": 876,
            "generation_time_ms": 3200,
            "has_assumptions": false,
            "prompt_tokens": 1420,
            "completion_tokens": 980
        }
    },
    "cached": false,
    "state": {
        "status": "COMPLETED",
        "turn_count": 4,
        "completeness_score": 1.0,
        "filled_fields": ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline", "estimasi_biaya"],
        "missing_fields": []
    }
}
```

**Response (200 OK) — Escalation Mode**:
```json
{
    "session_id": "...",
    "type": "generate",
    "message": "TOR telah dibuat berdasarkan informasi yang tersedia. Bagian yang ditandai [ASUMSI] dapat disesuaikan.",
    "tor_document": {
        "format": "markdown",
        "content": "# TERM OF REFERENCE (TOR)\n# Implementasi Sistem AI\n\n## 1. Latar Belakang\n\n[ASUMSI] Dalam rangka meningkatkan efisiensi...",
        "metadata": {
            "generated_by": "gemini-2.0-flash",
            "mode": "escalation",
            "word_count": 650,
            "generation_time_ms": 4100,
            "has_assumptions": true,
            "prompt_tokens": 2100,
            "completion_tokens": 1200
        }
    },
    "cached": false,
    "state": { "status": "COMPLETED", ... }
}
```

**Response (200 OK) — Cached**:
```json
{
    "session_id": "...",
    "type": "generate",
    "message": "TOR disajikan dari cache.",
    "tor_document": { ... },
    "cached": true,
    "state": { ... }
}
```

**Response (429 Too Many Requests)**:
```json
{
    "error": {
        "code": "E003",
        "message": "Batas panggilan Gemini tercapai (3/session atau 20/jam). Coba lagi nanti.",
        "retry_after_seconds": 120
    }
}
```

**Response (502 Bad Gateway) — Gemini Error**:
```json
{
    "error": {
        "code": "E004",
        "message": "Gemini API error. API key mungkin tidak valid atau quota habis.",
        "details": "InvalidArgument: API key is invalid"
    }
}
```

---

## 7. Dependencies

### Dependency ke modul lain

| Modul | Interface yang dipakai | Wajib? |
|---|---|---|
| **beta0.1.0 (Chat Engine)** | `SessionManager.get()`, `SessionManager.update()`, `SessionManager.get_chat_history()` | ✅ |
| **beta0.1.1 (RAG)** | `RAGPipeline.retrieve(query)` — untuk ambil contoh TOR | ❌ Opsional |
| **beta0.1.3 (Decision Engine)** | Tidak ada dependency | — |
| **beta0.1.4 (API Layer)** | Endpoint di-register ke router | ✅ |

### Interface yang disediakan untuk modul lain

```python
class GenerateService:
    """Interface utama yang dipakai oleh Decision Engine dan Hybrid Controller."""

    async def generate_tor(
        self,
        session_id: str,
        mode: Literal["standard", "escalation"] = "standard",
        data_override: TORData | None = None,
        force_regenerate: bool = False,
    ) -> GenerateResult:
        """
        Generate TOR document via Gemini.
        Dipanggil oleh:
          - Generate endpoint (langsung)
          - Decision Engine (beta0.1.3) → saat READY atau ESCALATE
          - Hybrid Controller (beta0.1.4)
        """
        ...
```

### Library dependencies

```
google-generativeai>=0.8.0     # Google Gemini Python SDK
aiosqlite>=0.20.0              # Shared — cache & session
```

### External dependencies

| Service | Setup |
|---|---|
| Google Gemini API | Dapatkan API key dari https://aistudio.google.com/apikey |
| Env var | `GEMINI_API_KEY=your-key-here` di `.env` |

---

## 8. Pseudocode

### 8.1 GeminiProvider

```python
import google.generativeai as genai
import time
import asyncio

class GeminiProvider:
    def __init__(self, settings: Settings):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
            generation_config=genai.GenerationConfig(
                temperature=settings.gemini_temperature,
                max_output_tokens=settings.gemini_max_tokens,
                top_p=0.95,
                top_k=40,
            ),
        )
        self.timeout = settings.gemini_timeout

    async def generate(self, prompt: str) -> GeminiResponse:
        """Generate content via Gemini API."""
        start = time.monotonic()

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content, prompt
                ),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            raise GeminiTimeoutError(f"Gemini timeout after {self.timeout}s")

        duration_ms = int((time.monotonic() - start) * 1000)

        # Extract usage metadata
        usage = response.usage_metadata
        return GeminiResponse(
            text=response.text,
            prompt_tokens=usage.prompt_token_count if usage else 0,
            completion_tokens=usage.candidates_token_count if usage else 0,
            duration_ms=duration_ms,
        )
```

### 8.2 Prompt Builder — Gemini Standard

```python
from app.ai.prompts.generate_tor import GEMINI_STANDARD_PROMPT
from app.ai.prompts.escalation import GEMINI_ESCALATION_PROMPT

class GeminiPromptBuilder:
    @staticmethod
    def build_standard(data: TORData, rag_examples: str | None = None) -> str:
        """Build prompt untuk standard TOR generation."""
        data_json = data.model_dump_json(indent=2, exclude_none=True)

        prompt = GEMINI_STANDARD_PROMPT.replace("{DATA_JSON}", data_json)

        if rag_examples:
            prompt = prompt.replace("{RAG_EXAMPLES}", rag_examples)
        else:
            prompt = prompt.replace(
                "## REFERENSI STYLE (dari RAG, jika ada)\n{RAG_EXAMPLES}",
                "## REFERENSI STYLE\nTidak ada referensi tersedia. Gunakan best-practice umum."
            )

        return prompt

    @staticmethod
    def build_escalation(
        chat_history: str,
        partial_data: TORData | None = None,
        rag_examples: str | None = None,
    ) -> str:
        """Build prompt untuk escalation mode."""
        prompt = GEMINI_ESCALATION_PROMPT.replace("{FULL_CHAT_HISTORY}", chat_history)

        if partial_data:
            partial_json = partial_data.model_dump_json(indent=2, exclude_none=True)
            prompt += f"\n\n## DATA PARSIAL YANG TERSEDIA\n{partial_json}"

        if rag_examples:
            prompt += f"\n\n## REFERENSI STYLE\n{rag_examples}"

        return prompt
```

### 8.3 PostProcessor

```python
import re

class PostProcessor:
    EXPECTED_SECTIONS = [
        "Latar Belakang",
        "Tujuan",
        "Ruang Lingkup",
        "Output",
        "Timeline",
    ]
    MIN_WORD_COUNT = 300

    @staticmethod
    def process(raw_tor: str) -> ProcessedTOR:
        """Validate dan clean TOR output."""
        content = PostProcessor._clean_formatting(raw_tor)
        word_count = len(content.split())
        has_assumptions = "[ASUMSI]" in content
        missing_sections = PostProcessor._check_structure(content)

        if word_count < PostProcessor.MIN_WORD_COUNT:
            logger.warning(f"TOR pendek: {word_count} kata (min: {PostProcessor.MIN_WORD_COUNT})")

        if missing_sections:
            logger.warning(f"TOR missing sections: {missing_sections}")

        return ProcessedTOR(
            content=content,
            word_count=word_count,
            has_assumptions=has_assumptions,
            missing_sections=missing_sections,
        )

    @staticmethod
    def _clean_formatting(text: str) -> str:
        """Remove wrapping code blocks, normalize whitespace."""
        # Remove ```markdown ... ``` wrapper
        text = re.sub(r'^```(?:markdown)?\s*\n', '', text)
        text = re.sub(r'\n```\s*$', '', text)
        # Normalize multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def _check_structure(content: str) -> list[str]:
        """Check apakah semua expected sections ada."""
        missing = []
        for section in PostProcessor.EXPECTED_SECTIONS:
            if section.lower() not in content.lower():
                missing.append(section)
        return missing
```

### 8.4 CostController

```python
from datetime import datetime, timedelta

class CostController:
    def __init__(self, session_mgr: SessionManager, settings: Settings):
        self.session_mgr = session_mgr
        self.max_per_session = settings.max_gemini_calls_per_session
        self.max_per_hour = settings.max_gemini_calls_per_hour

    async def check(self, session_id: str) -> None:
        """Raise RateLimitError jika melebihi batas."""
        # Check per-session limit
        session = await self.session_mgr.get(session_id)
        if session.gemini_calls_count >= self.max_per_session:
            raise RateLimitError(
                f"Batas {self.max_per_session} panggilan Gemini per session tercapai."
            )

        # Check global hourly limit
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        async with aiosqlite.connect(self.session_mgr.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM gemini_call_log WHERE called_at > ? AND success = TRUE",
                (one_hour_ago,)
            )
            row = await cursor.fetchone()
            hourly_count = row[0]

        if hourly_count >= self.max_per_hour:
            raise RateLimitError(
                f"Batas {self.max_per_hour} panggilan Gemini per jam tercapai. "
                "Coba lagi dalam beberapa menit."
            )

    async def log_call(
        self, session_id: str, model: str, mode: str,
        prompt_tokens: int, completion_tokens: int,
        duration_ms: int, success: bool, error_msg: str | None = None
    ):
        """Log setiap panggilan Gemini untuk tracking."""
        async with aiosqlite.connect(self.session_mgr.db_path) as db:
            await db.execute(
                "INSERT INTO gemini_call_log "
                "(session_id, model, mode, prompt_tokens, completion_tokens, duration_ms, success, error_message) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, model, mode, prompt_tokens, completion_tokens, duration_ms, success, error_msg)
            )
            await db.commit()
```

### 8.5 TORCache

```python
class TORCache:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, session_id: str) -> TORDocument | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM tor_cache WHERE session_id = ?", (session_id,)
            )
            row = await cursor.fetchone()
            if row:
                return TORDocument(
                    content=row["tor_content"],
                    metadata=TORMetadata(
                        generated_by=row["model_used"],
                        mode=row["mode"],
                        word_count=row["word_count"],
                        generation_time_ms=row["generation_time_ms"],
                        prompt_tokens=row["prompt_tokens"],
                        completion_tokens=row["completion_tokens"],
                    )
                )
            return None

    async def store(self, session_id: str, tor: TORDocument):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO tor_cache "
                "(session_id, tor_content, model_used, mode, word_count, "
                "generation_time_ms, prompt_tokens, completion_tokens) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, tor.content, tor.metadata.generated_by,
                 tor.metadata.mode, tor.metadata.word_count,
                 tor.metadata.generation_time_ms, tor.metadata.prompt_tokens,
                 tor.metadata.completion_tokens)
            )
            await db.commit()
```

### 8.6 GenerateService — Orchestrator

```python
class GenerateService:
    def __init__(
        self,
        gemini: GeminiProvider,
        session_mgr: SessionManager,
        rag_pipeline: RAGPipeline | None,
        prompt_builder: GeminiPromptBuilder,
        post_processor: PostProcessor,
        cache: TORCache,
        cost_ctrl: CostController,
    ):
        self.gemini = gemini
        self.session_mgr = session_mgr
        self.rag = rag_pipeline
        self.prompt_builder = prompt_builder
        self.post_processor = post_processor
        self.cache = cache
        self.cost_ctrl = cost_ctrl

    async def generate_tor(
        self,
        session_id: str,
        mode: str = "standard",
        data_override: TORData | None = None,
        force_regenerate: bool = False,
    ) -> GenerateResult:
        """Full generate pipeline."""

        # Step 1: Cost check
        await self.cost_ctrl.check(session_id)

        # Step 2: Check cache (standard mode only)
        if not force_regenerate and mode == "standard":
            cached = await self.cache.get(session_id)
            if cached:
                return GenerateResult(session_id=session_id, tor_document=cached, cached=True)

        # Step 3: Get session data
        session = await self.session_mgr.get(session_id)
        data = data_override or session.extracted_data
        history = await self.session_mgr.get_chat_history(session_id)

        # Step 4: Get RAG examples
        rag_examples = None
        if self.rag and data.judul:
            rag_examples = await self.rag.retrieve(data.judul, top_k=2)

        # Step 5: Build prompt
        if mode == "standard":
            prompt = self.prompt_builder.build_standard(data, rag_examples)
        else:
            formatted_history = format_chat_history(history)
            prompt = self.prompt_builder.build_escalation(
                formatted_history, data, rag_examples
            )

        # Step 6: Call Gemini (with retry)
        gemini_response = await self._call_with_retry(prompt, retries=3, backoff=[2, 5, 10])

        # Step 7: Post-process
        processed = self.post_processor.process(gemini_response.text)

        tor_doc = TORDocument(
            content=processed.content,
            metadata=TORMetadata(
                generated_by=self.gemini.model.model_name,
                mode=mode,
                word_count=processed.word_count,
                generation_time_ms=gemini_response.duration_ms,
                has_assumptions=processed.has_assumptions,
                prompt_tokens=gemini_response.prompt_tokens,
                completion_tokens=gemini_response.completion_tokens,
            )
        )

        # Step 8: Cache & update session
        await self.cache.store(session_id, tor_doc)
        await self.cost_ctrl.log_call(
            session_id, self.gemini.model.model_name, mode,
            gemini_response.prompt_tokens, gemini_response.completion_tokens,
            gemini_response.duration_ms, success=True
        )
        await self.session_mgr.update(
            session_id,
            state="COMPLETED",
            generated_tor=processed.content,
            gemini_calls_count=session.gemini_calls_count + 1,
            total_tokens_gemini=session.total_tokens_gemini
                + gemini_response.prompt_tokens
                + gemini_response.completion_tokens,
        )

        return GenerateResult(session_id=session_id, tor_document=tor_doc, cached=False)

    async def _call_with_retry(self, prompt: str, retries: int, backoff: list[int]) -> GeminiResponse:
        last_error = None
        for attempt in range(retries):
            try:
                return await self.gemini.generate(prompt)
            except (GeminiTimeoutError, Exception) as e:
                last_error = e
                if attempt < retries - 1:
                    await asyncio.sleep(backoff[attempt])
        raise last_error
```

---

## 9. Edge Cases

### Edge Case 1: Gemini API Key Tidak Valid

**Trigger**: `.env` belum di-set atau key expired.

**Handling**:
```python
except google.api_core.exceptions.InvalidArgument as e:
    raise HTTPException(status_code=502, detail={
        "code": "E004",
        "message": "API key Gemini tidak valid. Periksa GEMINI_API_KEY di .env",
        "details": str(e)
    })
```

### Edge Case 2: Gemini Rate Limit / Quota Habis

**Trigger**: Free tier quota 15 RPM / 1M tokens/day habis.

**Handling**:
```python
except google.api_core.exceptions.ResourceExhausted:
    await self.cost_ctrl.log_call(..., success=False, error_msg="quota_exhausted")
    raise HTTPException(status_code=429, detail={
        "code": "E003",
        "message": "Quota Gemini habis. Coba lagi nanti atau upgrade plan.",
        "retry_after_seconds": 60
    })
```

### Edge Case 3: Session Belum Siap untuk Generate (data masih kosong)

**Trigger**: User panggil `/generate` tapi session masih `NEW` atau `CHATTING` dengan data minim.

**Handling**:
```python
if mode == "standard" and session.completeness_score < 0.3:
    raise HTTPException(status_code=400, detail={
        "code": "E011",
        "message": "Data belum cukup untuk generate TOR. "
                   f"Completeness: {session.completeness_score:.0%}. "
                   "Lanjutkan chat dulu atau gunakan mode escalation.",
        "missing_fields": data.missing_fields()
    })
```

### Edge Case 4: Gemini Output Bukan TOR (Halusinasi)

**Trigger**: Gemini mengeluarkan konten tidak relevan.

**Handling**:
```python
processed = self.post_processor.process(raw_tor)
if processed.word_count < 100:
    logger.error(f"Gemini output too short: {processed.word_count} words")
    # Re-try dengan prompt yang lebih tegas
    # Atau return warning ke user
```

### Edge Case 5: Concurrent Generate Requests untuk Session yang Sama

**Trigger**: Dua request generate masuk bersamaan.

**Handling**: CostController cek `gemini_calls_count` secara atomik di database sebelum proceed. Yang kedua akan terhit rate limit per-session.

---

## 10. File yang Harus Dibuat

```
app/
├── ai/
│   ├── gemini_provider.py          # GeminiProvider class
│   └── prompts/
│       ├── generate_tor.py         # GEMINI_STANDARD_PROMPT constant
│       └── escalation.py           # GEMINI_ESCALATION_PROMPT constant
│
├── core/
│   ├── post_processor.py           # PostProcessor class
│   └── cost_controller.py          # CostController class
│
├── services/
│   └── generate_service.py         # GenerateService orchestrator
│
├── models/
│   └── generate.py                 # GenerateRequest, GenerateResponse, TORDocument, TORMetadata
│
├── db/
│   ├── repositories/
│   │   └── cache_repo.py           # TORCache class
│   └── migrations/
│       └── 002_gemini_tables.sql   # tor_cache + gemini_call_log tables
│
└── api/routes/
    └── generate.py                 # POST /api/v1/generate endpoint
```
