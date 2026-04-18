# Beta 0.1.3 — Decision Engine (Hybrid Routing & Smart Escalation)

> **Modul**: Decision Engine
> **Versi**: beta0.1.3
> **Status**: Ready to Implement
> **Estimasi**: 3 hari kerja
> **Prasyarat**: beta0.1.0 (Chat Engine) + beta0.1.2 (Gemini Generator) berjalan

---

## 1. Overview

Decision Engine adalah **otak keputusan** sistem — ia menentukan kapan local LLM sudah cukup dan kapan harus menyerahkan ke Gemini. Modul ini:

1. Mengelola **state machine** sesi percakapan (NEW → CHATTING → READY/ESCALATED → GENERATING → COMPLETED)
2. Mendeteksi **smart escalation triggers**: pola user malas, stagnasi data, max turns
3. Melakukan **routing otomatis** antara Chat Engine dan Gemini Generator
4. Menghitung **progress tracking** (completeness score trend, stagnation detection)
5. Menerapkan **pre-routing checks** SEBELUM pesan dikirim ke LLM

Ini adalah "controller" pusat yang membuat endpoint `/api/v1/hybrid` bisa bekerja secara cerdas. Tanpa modul ini, sistem hanya bisa chat atau generate secara manual.

---

## 2. Scope

### ✅ Yang dikerjakan di modul ini

| Item | Detail |
|---|---|
| State Machine | Transisi state sesi: NEW → CHATTING → READY → GENERATING → COMPLETED |
| Smart Escalation | 5 aturan eskalasi otomatis (lazy patterns, stagnation, max turns, dll) |
| Pre-routing Check | Analisa pesan user SEBELUM kirim ke LLM (lazy detection, short input check) |
| Routing Logic | Dispatch ke ChatService atau GenerateService berdasarkan state & status |
| Progress Tracker | Track completeness score history, deteksi stagnasi |
| Escalation Logger | Log alasan setiap eskalasi untuk audit trail |

### ❌ Yang TIDAK dikerjakan di modul ini

| Item | Alasan |
|---|---|
| Chat logic | Itu milik beta0.1.0 (Chat Engine) |
| TOR generation | Itu milik beta0.1.2 (Gemini Generator) |
| HTTP endpoint | Itu milik beta0.1.4 (API Layer). Modul ini menyediakan `DecisionEngine` class |
| RAG retrieval | Itu milik beta0.1.1 (RAG System) |

---

## 3. Input / Output

### Input (dari Hybrid Controller)

```python
class RoutingInput:
    session_id: str | None             # null = session baru
    message: str                        # pesan user
    options: HybridOptions | None

class HybridOptions:
    force_generate: bool = False        # bypass semua logic, langsung Gemini
    language: str = "id"
```

### Output

```python
class RoutingResult:
    session_id: str
    action_taken: Literal[
        "CHAT",                         # pesan dikirim ke local LLM, return pertanyaan
        "GENERATE_STANDARD",            # LLM bilang READY, Gemini auto-triggered
        "GENERATE_ESCALATION",          # Smart escalation triggered, Gemini ambil alih
        "FORCE_GENERATE",               # User paksa generate via option
    ]
    chat_response: ChatResult | None    # hasil dari ChatService (jika action = CHAT)
    generate_response: GenerateResult | None  # hasil dari GenerateService (jika action = GENERATE_*)
    escalation_info: EscalationInfo | None    # detail eskalasi (jika ada)

class EscalationInfo:
    triggered_by: str                   # nama rule yang trigger
    reason: str                         # penjelasan human-readable
    turn_count: int                     # turn saat eskalasi terjadi
    completeness_at_escalation: float   # score saat eskalasi
```

---

## 4. Flow Logic

### Step-by-step: Hybrid Routing

```
STEP 0: FORCE GENERATE CHECK
──────────────────────────────
IF options.force_generate == True:
    → Skip semua logic
    → Langsung panggil GenerateService.generate_tor(mode="escalation")
    → Return RoutingResult(action="FORCE_GENERATE", generate_response=...)

STEP 1: SESSION STATE CHECK
──────────────────────────────
session = SessionManager.get_or_create(session_id)

IF session.state == "COMPLETED":
    → Session sudah punya TOR
    → Return dari cache ATAU tanya: "TOR sudah dibuat. Ingin revisi?"

IF session.state == "GENERATING":
    → Gemini sedang proses
    → Return: "Sedang memproses TOR Anda, mohon tunggu."

STEP 2: PRE-ROUTING ESCALATION CHECK
───────────────────────────────────────
SEBELUM kirim ke LLM, cek apakah harus langsung eskalasi:

    2a. LAZY PATTERN DETECTION
    ──────────────────────────
    IF message matches ANY lazy_pattern regex:
        patterns: ["terserah", "gak tau", "ga tau", "bebas aja",
                   "pokoknya buat", "yang penting jadi", "serahin aja",
                   "bingung", "males jelasin", "tidak tau"]

        IF ini lazy pattern PERTAMA (beri 1x toleransi):
            → Lanjut ke LLM, biarkan LLM coba gali lagi
            → Set flag: session.lazy_strike = 1
        ELIF sudah lazy_strike >= 1 (lazy kedua kalinya):
            → TRIGGER ESCALATION
            → reason: "User menunjukkan pola tidak kooperatif (2x lazy response)"

    2b. SHORT INPUT CHECK
    ──────────────────────
    IF len(message) <= 15 chars AND session.turn_count >= 2:
        IF previous message juga <= 15 chars:
            → TRIGGER ESCALATION
            → reason: "2x berturut-turut jawaban sangat pendek (≤15 karakter)"

    2c. MAX TURNS CHECK
    ─────────────────────
    IF session.turn_count >= ABSOLUTE_MAX_TURNS (10):
        → TRIGGER ESCALATION
        → reason: "Batas maksimum turn (10) tercapai"

    2d. STAGNATION CHECK
    ──────────────────────
    IF completeness score TIDAK naik selama 3 turn berturut-turut:
        → TRIGGER ESCALATION
        → reason: "Tidak ada progress data baru selama 3 turn"

    2e. IDLE TURNS CHECK
    ─────────────────────
    IF turn_count - last_field_filled_turn >= MAX_IDLE_TURNS (5):
        → TRIGGER ESCALATION
        → reason: "5 turn tanpa field baru terisi"

STEP 3: CHAT WITH LOCAL LLM
──────────────────────────────
IF no escalation triggered:
    → Panggil ChatService.process_message(session_id, message, rag_context)
    → Dapat ChatResult dengan status

STEP 4: POST-ROUTING DECISION
────────────────────────────────
MATCH chat_result.status:

    CASE "NEED_MORE_INFO":
        → Return RoutingResult(
            action="CHAT",
            chat_response=chat_result
          )
        → Update progress tracker

    CASE "READY_TO_GENERATE":
        → Panggil GenerateService.generate_tor(
            session_id,
            mode="standard"
          )
        → Return RoutingResult(
            action="GENERATE_STANDARD",
            chat_response=chat_result,     # konfirmasi dari LLM
            generate_response=gen_result    # TOR final
          )

    CASE "ESCALATE_TO_GEMINI":
        → Panggil GenerateService.generate_tor(
            session_id,
            mode="escalation"
          )
        → Return RoutingResult(
            action="GENERATE_ESCALATION",
            chat_response=chat_result,
            generate_response=gen_result,
            escalation_info=EscalationInfo(
                triggered_by="llm_decision",
                reason=chat_result.escalation_reason
            )
          )

    DEFAULT:
        → Treat as NEED_MORE_INFO (fallback safety)
```

---

## 5. Data Structure

### 5.1 Escalation Rules Configuration

```python
@dataclass
class EscalationConfig:
    """Semua threshold untuk smart escalation."""

    # Rule 1: Max turns tanpa progress
    max_idle_turns: int = 5

    # Rule 2: Absolute max turns
    absolute_max_turns: int = 10

    # Rule 3: Lazy patterns (regex, case-insensitive)
    lazy_patterns: list[str] = field(default_factory=lambda: [
        r"terserah",
        r"gak\s*tau",
        r"ga\s*tau",
        r"tidak\s*tau",
        r"bebas\s*(aja)?",
        r"pokoknya\s*(buat|bikin)",
        r"yang\s*penting\s*jadi",
        r"serah(in)?\s*(aja|kamu)?",
        r"bingung",
        r"males\s*jelasin",
        r"gak\s*ngerti",
        r"ga\s*paham",
        r"yaudah\s*(lah)?",
        r"langsung\s*aja",
    ])
    lazy_tolerance: int = 1          # berapa kali lazy dimaafkan sebelum escalate

    # Rule 4: Short input consecutive
    short_input_max_chars: int = 15
    short_input_consecutive: int = 2

    # Rule 5: Stagnation
    stagnation_turns: int = 3        # berapa turn tanpa kenaikan score
```

### 5.2 ProgressTracker State

```python
class ProgressState(BaseModel):
    """Tracking progress per session untuk stagnation detection."""
    score_history: list[float] = []     # completeness score per turn
    last_field_filled_turn: int = 0     # turn terakhir ada field baru terisi
    lazy_strike_count: int = 0          # berapa kali lazy pattern terdeteksi
    short_input_streak: int = 0         # berturut-turut input pendek
    previous_filled_count: int = 0      # jumlah field terisi di turn sebelumnya
```

### 5.3 EscalationDecision

```python
class EscalationDecision(BaseModel):
    should_escalate: bool
    rule_name: str | None = None         # nama rule yang trigger
    reason: str | None = None            # penjelasan
    confidence: float = 0.0              # seberapa yakin (0-1)
```

### 5.4 Escalation Log (SQLite)

```sql
CREATE TABLE escalation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rule_name TEXT NOT NULL,
    reason TEXT NOT NULL,
    turn_count INTEGER,
    completeness_score REAL,
    message_that_triggered TEXT,          -- pesan user yang memicu eskalasi
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_escalation_session ON escalation_log(session_id);
```

---

## 6. API Contract

Modul ini **tidak punya endpoint sendiri**. Ia menyediakan `DecisionEngine` class yang dipanggil oleh Hybrid endpoint (beta0.1.4).

### Interface Contract

```python
class DecisionEngine:
    """Interface yang dipakai oleh HybridController (beta0.1.4)."""

    async def route(
        self,
        session_id: str | None,
        message: str,
        options: HybridOptions | None = None,
    ) -> RoutingResult:
        """
        Main entry point.
        Menerima message, menjalankan semua logic, return hasil routing.

        Caller (HybridController) cukup panggil ini dan forward hasilnya ke client.
        """
        ...
```

### Response yang diteruskan ke API Response (di beta0.1.4)

**Jika action == "CHAT"**:
```json
{
    "session_id": "...",
    "type": "chat",
    "message": "Baik, untuk timeline-nya kira-kira kapan pelaksanaannya?",
    "state": { "status": "NEED_MORE_INFO", "turn_count": 3, ... },
    "extracted_data": { ... }
}
```

**Jika action == "GENERATE_STANDARD"**:
```json
{
    "session_id": "...",
    "type": "generate",
    "message": "Data sudah lengkap! Berikut TOR yang telah dibuat:",
    "tor_document": { "content": "# TOR ...", "metadata": { ... } },
    "state": { "status": "COMPLETED", ... }
}
```

**Jika action == "GENERATE_ESCALATION"**:
```json
{
    "session_id": "...",
    "type": "generate",
    "message": "Baik, saya akan buatkan draft TOR berdasarkan informasi yang ada. Bagian [ASUMSI] bisa Anda sesuaikan.",
    "tor_document": { "content": "# TOR ...\n[ASUMSI]...", "metadata": { "mode": "escalation", ... } },
    "escalation_info": {
        "triggered_by": "lazy_pattern",
        "reason": "User menunjukkan pola tidak kooperatif (2x lazy response)"
    },
    "state": { "status": "COMPLETED", ... }
}
```

---

## 7. Dependencies

### Dependency ke modul lain

| Modul | Interface yang dipakai | Wajib? |
|---|---|---|
| **beta0.1.0 (Chat Engine)** | `ChatService.process_message()`, `SessionManager.*` | ✅ |
| **beta0.1.1 (RAG)** | `RAGPipeline.retrieve()` — retrieve context sebelum chat | ❌ Opsional |
| **beta0.1.2 (Gemini Generator)** | `GenerateService.generate_tor()` — saat READY/ESCALATE | ✅ |
| **beta0.1.4 (API Layer)** | Endpoint memanggil `DecisionEngine.route()` | ✅ |

### Interface yang disediakan untuk modul lain

```python
class DecisionEngine:
    async def route(self, session_id, message, options) -> RoutingResult
```

### Library dependencies

```
# Tidak ada library baru. Hanya butuh:
re                    # built-in — regex untuk lazy pattern matching
dataclasses           # built-in — configuration
```

---

## 8. Pseudocode

### 8.1 EscalationChecker — Deteksi Kapan Harus Eskalasi

```python
import re
from dataclasses import dataclass

class EscalationChecker:
    def __init__(self, config: EscalationConfig):
        self.config = config
        self.compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in config.lazy_patterns
        ]

    def check_pre_routing(
        self,
        message: str,
        session: Session,
        progress: ProgressState,
    ) -> EscalationDecision:
        """
        Check SEBELUM kirim ke LLM.
        Returns EscalationDecision.
        """
        # Rule 1: Absolute max turns
        if session.turn_count >= self.config.absolute_max_turns:
            return EscalationDecision(
                should_escalate=True,
                rule_name="absolute_max_turns",
                reason=f"Batas maksimum turn ({self.config.absolute_max_turns}) tercapai",
                confidence=1.0,
            )

        # Rule 2: Lazy pattern detection
        is_lazy = self._match_lazy_pattern(message)
        if is_lazy:
            new_strike = progress.lazy_strike_count + 1
            if new_strike > self.config.lazy_tolerance:
                return EscalationDecision(
                    should_escalate=True,
                    rule_name="lazy_pattern",
                    reason=f"User menunjukkan pola tidak kooperatif "
                           f"({new_strike}x lazy response, toleransi: {self.config.lazy_tolerance})",
                    confidence=0.9,
                )
            # Belum melewati toleransi — update strike, lanjut ke LLM
            progress.lazy_strike_count = new_strike

        # Rule 3: Short input consecutive
        is_short = len(message.strip()) <= self.config.short_input_max_chars
        if is_short and session.turn_count >= 2:
            new_streak = progress.short_input_streak + 1
            if new_streak >= self.config.short_input_consecutive:
                return EscalationDecision(
                    should_escalate=True,
                    rule_name="short_input_consecutive",
                    reason=f"{new_streak}x berturut-turut jawaban sangat pendek "
                           f"(≤{self.config.short_input_max_chars} karakter)",
                    confidence=0.8,
                )
            progress.short_input_streak = new_streak
        else:
            progress.short_input_streak = 0  # reset streak

        # Rule 4: Stagnation (score tidak naik selama N turn)
        if len(progress.score_history) >= self.config.stagnation_turns:
            recent_scores = progress.score_history[-self.config.stagnation_turns:]
            if all(s == recent_scores[0] for s in recent_scores) and recent_scores[0] < 1.0:
                return EscalationDecision(
                    should_escalate=True,
                    rule_name="stagnation",
                    reason=f"Tidak ada progress data baru selama "
                           f"{self.config.stagnation_turns} turn "
                           f"(score tetap {recent_scores[0]:.2f})",
                    confidence=0.85,
                )

        # Rule 5: Idle turns (lama sejak field terakhir terisi)
        idle_turns = session.turn_count - progress.last_field_filled_turn
        if idle_turns >= self.config.max_idle_turns:
            return EscalationDecision(
                should_escalate=True,
                rule_name="idle_turns",
                reason=f"{idle_turns} turn tanpa field baru terisi "
                       f"(max idle: {self.config.max_idle_turns})",
                confidence=0.7,
            )

        # No escalation needed
        return EscalationDecision(should_escalate=False)

    def _match_lazy_pattern(self, message: str) -> bool:
        """Check if message matches any lazy pattern."""
        text = message.strip().lower()
        return any(pattern.search(text) for pattern in self.compiled_patterns)
```

### 8.2 ProgressTracker

```python
class ProgressTracker:
    """Track completeness progress per session (in-memory, synced from DB)."""

    def __init__(self):
        self._states: dict[str, ProgressState] = {}

    def get(self, session_id: str) -> ProgressState:
        if session_id not in self._states:
            self._states[session_id] = ProgressState()
        return self._states[session_id]

    def update_after_chat(
        self,
        session_id: str,
        new_completeness: float,
        new_filled_count: int,
    ):
        """Update progress setelah chat turn selesai."""
        state = self.get(session_id)
        state.score_history.append(new_completeness)

        # Cek apakah ada field baru terisi
        if new_filled_count > state.previous_filled_count:
            current_turn = len(state.score_history)
            state.last_field_filled_turn = current_turn
            state.previous_filled_count = new_filled_count

    def reset(self, session_id: str):
        """Reset progress state (misal saat session di-reset)."""
        self._states.pop(session_id, None)
```

### 8.3 DecisionEngine — Orchestrator Utama

```python
class DecisionEngine:
    def __init__(
        self,
        chat_service: ChatService,
        generate_service: GenerateService,
        rag_pipeline: RAGPipeline | None,
        session_mgr: SessionManager,
        escalation_checker: EscalationChecker,
        progress_tracker: ProgressTracker,
    ):
        self.chat = chat_service
        self.generate = generate_service
        self.rag = rag_pipeline
        self.session_mgr = session_mgr
        self.checker = escalation_checker
        self.tracker = progress_tracker

    async def route(
        self,
        session_id: str | None,
        message: str,
        options: HybridOptions | None = None,
    ) -> RoutingResult:
        """Main routing logic."""
        options = options or HybridOptions()

        # === STEP 0: Force generate ===
        if options.force_generate:
            if not session_id:
                raise ValueError("session_id diperlukan untuk force_generate")
            gen_result = await self.generate.generate_tor(
                session_id, mode="escalation"
            )
            return RoutingResult(
                session_id=session_id,
                action_taken="FORCE_GENERATE",
                generate_response=gen_result,
            )

        # === STEP 1: Get/create session ===
        if session_id:
            session = await self.session_mgr.get(session_id)
        else:
            session = await self.session_mgr.create()
            session_id = session.id

        # Check if already completed
        if session.state == "COMPLETED" and session.generated_tor:
            return RoutingResult(
                session_id=session_id,
                action_taken="CHAT",
                chat_response=ChatResult(
                    session_id=session_id,
                    status="COMPLETED",
                    message="TOR sudah dibuat sebelumnya. Kirim pesan untuk memulai revisi.",
                    extracted_data=session.extracted_data,
                    missing_fields=[],
                    confidence=1.0,
                    completeness_score=session.completeness_score,
                    raw_llm_response="",
                ),
            )

        # === STEP 2: Pre-routing escalation check ===
        progress = self.tracker.get(session_id)
        escalation = self.checker.check_pre_routing(message, session, progress)

        if escalation.should_escalate:
            return await self._handle_escalation(
                session_id, session, escalation, message
            )

        # === STEP 3: Get RAG context ===
        rag_context = None
        if self.rag:
            try:
                rag_context = await self.rag.retrieve(message, top_k=3)
            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without: {e}")

        # === STEP 4: Chat with local LLM ===
        chat_result = await self.chat.process_message(
            session_id=session_id,
            message=message,
            rag_context=rag_context,
        )

        # === STEP 5: Update progress ===
        filled_count = len(chat_result.extracted_data.filled_fields())
        self.tracker.update_after_chat(
            session_id, chat_result.completeness_score, filled_count
        )

        # === STEP 6: Post-routing decision ===
        match chat_result.status:
            case "NEED_MORE_INFO":
                return RoutingResult(
                    session_id=session_id,
                    action_taken="CHAT",
                    chat_response=chat_result,
                )

            case "READY_TO_GENERATE":
                gen_result = await self.generate.generate_tor(
                    session_id, mode="standard"
                )
                return RoutingResult(
                    session_id=session_id,
                    action_taken="GENERATE_STANDARD",
                    chat_response=chat_result,
                    generate_response=gen_result,
                )

            case "ESCALATE_TO_GEMINI":
                gen_result = await self.generate.generate_tor(
                    session_id, mode="escalation"
                )
                return RoutingResult(
                    session_id=session_id,
                    action_taken="GENERATE_ESCALATION",
                    chat_response=chat_result,
                    generate_response=gen_result,
                    escalation_info=EscalationInfo(
                        triggered_by="llm_decision",
                        reason=chat_result.escalation_reason or "LLM memutuskan eskalasi",
                        turn_count=session.turn_count + 1,
                        completeness_at_escalation=chat_result.completeness_score,
                    ),
                )

            case _:
                # Fallback: treat as chat
                return RoutingResult(
                    session_id=session_id,
                    action_taken="CHAT",
                    chat_response=chat_result,
                )

    async def _handle_escalation(
        self,
        session_id: str,
        session: Session,
        decision: EscalationDecision,
        triggering_message: str,
    ) -> RoutingResult:
        """Handle escalation: log, generate, return."""
        # Log escalation
        await self._log_escalation(
            session_id, decision, session.turn_count,
            session.completeness_score, triggering_message
        )

        # Update session state
        await self.session_mgr.update(
            session_id,
            state="ESCALATED",
            escalation_reason=decision.reason,
        )

        # Generate via Gemini (escalation mode)
        gen_result = await self.generate.generate_tor(
            session_id, mode="escalation"
        )

        return RoutingResult(
            session_id=session_id,
            action_taken="GENERATE_ESCALATION",
            generate_response=gen_result,
            escalation_info=EscalationInfo(
                triggered_by=decision.rule_name,
                reason=decision.reason,
                turn_count=session.turn_count,
                completeness_at_escalation=session.completeness_score,
            ),
        )

    async def _log_escalation(
        self, session_id, decision, turn_count, score, message
    ):
        """Simpan log eskalasi ke database."""
        async with aiosqlite.connect(self.session_mgr.db_path) as db:
            await db.execute(
                "INSERT INTO escalation_log "
                "(session_id, rule_name, reason, turn_count, "
                "completeness_score, message_that_triggered) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, decision.rule_name, decision.reason,
                 turn_count, score, message[:500])
            )
            await db.commit()
```

---

## 9. Edge Cases

### Edge Case 1: User Kembali ke Session yang Sudah COMPLETED

**Trigger**: User kirim pesan baru ke session yang sudah punya TOR.

**Handling**:
```python
if session.state == "COMPLETED":
    # Opsi 1: Reset session untuk revisi
    # Opsi 2: Return TOR dari cache + pesan
    return RoutingResult(
        action="CHAT",
        chat_response=ChatResult(
            message="TOR sudah dibuat sebelumnya. "
                    "Kirim detail tambahan untuk revisi, "
                    "atau mulai percakapan baru.",
            ...
        )
    )
```

### Edge Case 2: LLM Bilang READY tapi Completeness Score Rendah

**Trigger**: LLM mengeluarkan `READY_TO_GENERATE` tapi data extracted hanya 30% terisi.

**Handling**:
```python
if chat_result.status == "READY_TO_GENERATE":
    if chat_result.completeness_score < 0.5:
        logger.warning(
            f"LLM says READY but score only {chat_result.completeness_score:.2f}. "
            "Overriding to escalation mode."
        )
        # Generate tetap jalan tapi pakai mode ESCALATION agar Gemini bisa
        # melengkapi dengan asumsi
        gen_result = await self.generate.generate_tor(
            session_id, mode="escalation"
        )
```

### Edge Case 3: RAG Pipeline Down saat Routing

**Trigger**: ChromaDB tidak accessible.

**Handling**:
```python
try:
    rag_context = await self.rag.retrieve(message)
except Exception as e:
    logger.warning(f"RAG failed, continuing without context: {e}")
    rag_context = None  # graceful degradation
```

### Edge Case 4: Generate Service Gagal setelah Escalation Triggered

**Trigger**: Gemini down saat Decision Engine memutuskan escalation.

**Handling**:
```python
try:
    gen_result = await self.generate.generate_tor(session_id, mode="escalation")
except (GeminiTimeoutError, RateLimitError) as e:
    # Rollback state dari ESCALATED ke CHATTING
    await self.session_mgr.update(session_id, state="CHATTING")
    return RoutingResult(
        action="CHAT",
        chat_response=ChatResult(
            message="Maaf, sistem sedang sibuk. Coba lagi nanti. "
                    "Sementara itu, beri saya informasi tambahan "
                    "agar TOR bisa lebih lengkap.",
            ...
        )
    )
```

### Edge Case 5: Semua Rules Tidak Trigger tapi User Jelas Frustasi

**Trigger**: User ketik sesuatu yang tidak match pattern tapi nada frustrasi (e.g., "ah sudahlah capek").

**Handling**: Untuk v0.1, ini diandalkan ke LLM. Jika LLM mendeteksi frustasi, ia akan return `ESCALATE_TO_GEMINI`. Jika tidak, stagnation/idle rules akan menangkap di turn berikutnya.

---

## 10. File yang Harus Dibuat

```
app/
├── core/
│   ├── decision_engine.py          # DecisionEngine class (orchestrator)
│   ├── escalation_checker.py       # EscalationChecker + EscalationConfig
│   └── progress_tracker.py         # ProgressTracker class
│
├── models/
│   ├── routing.py                  # RoutingInput, RoutingResult, EscalationInfo
│   └── escalation.py               # EscalationDecision, EscalationConfig, ProgressState
│
├── db/migrations/
│   └── 003_escalation_log.sql      # CREATE TABLE escalation_log
│
└── tests/
    ├── test_escalation_checker.py   # Unit test semua 5 rules
    ├── test_progress_tracker.py     # Unit test stagnation detection
    └── test_decision_engine.py      # Integration test routing scenarios
```

---

## 11. Test Scenarios

### Unit Tests untuk EscalationChecker

```python
# test_escalation_checker.py

def test_lazy_pattern_first_time_is_tolerated():
    """Lazy pertama → tidak escalate (toleransi 1x)."""
    result = checker.check_pre_routing("terserah aja", session, progress)
    assert result.should_escalate == False
    assert progress.lazy_strike_count == 1

def test_lazy_pattern_second_time_triggers():
    """Lazy kedua → escalate."""
    progress.lazy_strike_count = 1
    result = checker.check_pre_routing("gak tau", session, progress)
    assert result.should_escalate == True
    assert result.rule_name == "lazy_pattern"

def test_absolute_max_turns():
    """Turn 10 → pasti escalate."""
    session.turn_count = 10
    result = checker.check_pre_routing("halo", session, progress)
    assert result.should_escalate == True
    assert result.rule_name == "absolute_max_turns"

def test_short_input_consecutive():
    """2x input pendek berturut → escalate."""
    progress.short_input_streak = 1
    session.turn_count = 3
    result = checker.check_pre_routing("ok", session, progress)
    assert result.should_escalate == True

def test_stagnation_detection():
    """Score sama 3 turn berturut → escalate."""
    progress.score_history = [0.33, 0.33, 0.33]
    result = checker.check_pre_routing("idk", session, progress)
    assert result.should_escalate == True
    assert result.rule_name == "stagnation"

def test_normal_message_no_escalation():
    """Pesan normal → tidak escalate."""
    result = checker.check_pre_routing(
        "Timeline nya 3 hari di bulan Juli",
        session,
        progress,
    )
    assert result.should_escalate == False
```
