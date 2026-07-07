# Beta 0.4.0 — Multi-Agent System (3 Agent Architecture)

## 1. Ringkasan

Saat ini sistem menggunakan **1 LLM call per turn** — satu agent menangani everything dari ngegali data sampe nentuin kapan generate. Ini bikin prompt jadi besar, kompleks, dan kadang inkonsisten.

**Beta 0.4.0** memperkenalkan **Multi-Agent Architecture** dengan 3 agent:

```
Supervisor Agent
  ├── Coordinator: nerima input user, nentuin langkah selanjutnya
  ├── Mutusin: INTERVIEW / GENERATE / REVISE
  └── Delegasi ke agent yang tepat

Interviewer Agent     Writer Agent
  ├── Gali data TOR     ├── Nulis TOR final
  ├── Output: JSON      ├── Output: dokumen
  └── Fokus: data       └── Fokus: kualitas tulisan
```

### Kenapa 3 Agent?

| # | Problem Sekarang | Solusi Multi-Agent |
|---|-----------------|-------------------|
| 1 | **Prompt besar & kompleks** — 1 prompt harus handle everything | Tiap agent punya 1 job, prompt kecil & fokus |
| 2 | **Susah debug** — error parsing campur aduk | Setiap agent independen, error isolation |
| 3 | **Susah extend** — mau tambah skill (budget, timeline) bikin prompt makin gede | Tinggal tambah agent baru tanpa ganggu existing |
| 4 | **Inkonsisten output** — kadang JSON valid, kadang nggak | Tiap agent punya format output strict |
| 5 | **Gak ada quality control** — generate langsung kirim ke user | Writer Agent bisa di-review sama Supervisor |

---

## 2. Arsitektur

### 2.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SUPERVISOR AGENT                          │
│                                                             │
│  Input: user_message + session_state + conversation_history │
│  Output: Decision { action: str, agent: str, context: dict }│
│                                                             │
│  Decisions:                                                  │
│    - INTERVIEW  → Interviewer Agent (gali data)              │
│    - GENERATE   → Writer Agent (buat TOR)                    │
│    - COMPLETE   → Return final ke user                       │
│    - REVISE     → Writer Agent (revisi TOR)                  │
│    - CLARIFY    → Tanya balik ke user                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ INTERVIEWER     │ │ WRITER          │ │ (Future: BUDGET │
│ AGENT           │ │ AGENT           │ │  ANALYST, etc)  │
│                 │ │                 │ │                 │
│ Gali data TOR   │ │ Generate TOR    │ │                 │
│ dari user       │ │ dari data       │ │                 │
│ Output: JSON    │ │ Output: dokumen │ │                 │
│ (TORData)       │ │ (Markdown)      │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 2.2 Alur Percakapan

```
Turn 1:
  User: "Saya mau buat TOR untuk workshop AI"
    → Supervisor: INTERVIEW → Interviewer
    → Interviewer: "Baik, berapa hari durasinya?"
    → Response ke user

Turn 2:
  User: "3 hari, budget 50jt"
    → Supervisor: INTERVIEW → Interviewer
    → Interviewer: "Siapa target pesertanya?"
    → Response ke user

Turn 3:
  User: "30 orang, internal karyawan"
    → Supervisor: cek completeness → cukup
    → GENERATE → Writer
    → Writer: hasilin TOR
    → Response: TOR document

Turn 4:
  User: "Tolong tambahin bagian evaluasi"
    → Supervisor: REVISE → Writer
    → Writer: update TOR dengan bagian evaluasi
    → Response: TOR revisi
```

### 2.3 State Machine

```
                         ┌─────────────┐
                         │    NEW      │
                         └──────┬──────┘
                                │ user message
                                ▼
                    ┌─────────────────────┐
           ┌─────── │ SUPERVISOR DECIDES  │
           │        └──────┬──────────────┘
           │               │
           ▼               ▼               ▼
   ┌────────────┐  ┌──────────────┐  ┌────────────┐
   │ INTERVIEW  │  │  GENERATE    │  │  REVISE    │
   │ (gali data)│  │  (buat TOR)  │  │  (revisi)  │
   └─────┬──────┘  └──────┬───────┘  └──────┬─────┘
         │                │                  │
         ▼                ▼                  │
   ┌────────────┐  ┌──────────────┐          │
   │ Supervisor │  │ Supervisor   │──────────┘
   │ (lagi)     │  │ (cek hasil)  │
   └────────────┘  └──────┬───────┘
                          │
               ┌──────────┼──────────┐
               ▼          ▼          ▼
          ┌────────┐ ┌────────┐ ┌────────┐
          │COMPLETE│ │ REVISE │ │DONE/   │
          │ (selesai│ │ (revisi│ │ FORWARD│
          │  )      │ │  lagi) │ │        │
          └────────┘ └────────┘ └────────┘
```

---

## 3. Component Design

### 3.1 Base Agent

```python
class BaseAgent(ABC):
    name: str
    description: str
    system_prompt: str

    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResult:
        """Process input dan return result."""
        pass

    @abstractmethod
    def build_messages(self, context: AgentContext) -> list[dict]:
        """Build messages array untuk LLM call."""
        pass
```

### 3.2 Supervisor Agent

**Job**: Coordinator — nerima input, nentuin action.

**System Prompt**:
```
Kamu adalah Supervisor Agent yang mengoordinasikan pembuatan dokumen TOR.

Tugasmu:
1. Analisis input user + state session
2. Decide action: INTERVIEW / GENERATE / REVISE / CLARIFY

Output JSON:
{
    "decision": "INTERVIEW" | "GENERATE" | "REVISE" | "CLARIFY",
    "reason": "Alasan singkat",
    "context": { ... }  // data yang relevan untuk agent selanjutnya
}
```

**Input Context**:
- `user_message`: Pesan user saat ini
- `session_state`: Current session state (turn_count, completeness, dll)
- `extracted_data`: Data TOR yang sudah terkumpul
- `missing_fields`: Field yang masih kosong
- `conversation_summary`: Ringkasan percakapan

### 3.3 Interviewer Agent

**Job**: Gali data TOR dari user secara interaktif.

**System Prompt**:
```
Kamu adalah Interviewer Agent yang bertugas mengumpulkan data untuk TOR.
Output SELALU dalam format JSON.

Data yang harus dikumpulkan:
- judul, latar_belakang, tujuan, ruang_lingkup, output, timeline, estimasi_biaya
```

**Catatan**: Prompt ini mirip dengan `chat_system.py` yang existing, tapi LEBIH FOKUS — cuma ngegas data, gak perlu mikirin status READY_TO_GENERATE atau escalation. Itu urusan Supervisor.

### 3.4 Writer Agent

**Job**: Nulis TOR dari data yang udah lengkap.

**System Prompt**:
```
Kamu adalah Writer Agent yang bertugas menulis dokumen TOR profesional.
Gunakan data yang diberikan untuk membuat TOR yang lengkap dan siap pakai.
```

**Catatan**: Ini mirip prompt `generate_tor.py` yang existing. Fokus: kualitas tulisan.

---

## 4. Backend Changes

### 4.1 New Files

```
app/
├── agents/                              # NEW: Agent directory
│   ├── __init__.py
│   ├── base_agent.py                    # Abstract BaseAgent
│   ├── supervisor_agent.py              # Supervisor decision maker
│   ├── interviewer_agent.py             # Interviewer
│   ├── writer_agent.py                  # Writer
│   └── agent_context.py                 # Context/result models
```

### 4.2 Modified Files

| File | Changes |
|------|---------|
| `app/core/decision_engine.py` | Ganti logic if-else dengan Supervisor Agent call |
| `app/services/chat_service.py` | Simplify — jadi thin wrapper atau di-refactor |
| `app/services/generate_service.py` | Tetap ada, dipanggil oleh Writer Agent |
| `app/ai/prompts/` | Split prompt jadi per-agent |

### 4.3 New Models

```python
# app/agents/agent_context.py

class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    INTERVIEWER = "interviewer"
    WRITER = "writer"

class AgentContext(BaseModel):
    agent_type: AgentType
    user_message: str | None = None
    session_id: str
    extracted_data: TORData
    missing_fields: list[str]
    completeness: float
    turn_count: int
    conversation_history: list[dict]
    generated_tor: str | None = None

class AgentResult(BaseModel):
    agent: AgentType
    decision: str | None = None       # Supervisor output
    message: str | None = None        # Interviewer/Writer output
    data: TORData | None = None
    tor_content: str | None = None    # Writer output
    confidence: float = 0.0
```

---

## 5. Frontend Changes

### 5.1 Visual Indicator

Tambahan UI untuk menunjukkan **agent mana yang sedang aktif**:

```
┌─────────────────────────────────────┐
│  Supervisor Agent                   │
│  ─────────────────────              │
│  │ Menganalisis pesan Anda...     │ │
│  └────────────────────              │
│                                     │
│  → Interviewer Agent aktif          │
│  ─────────────────────              │
│  │ Baik, saya akan menggali data   │ │
│  │ TOR yang dibutuhkan...          │ │
│  └────────────────────              │
│                                     │
│  [User: "3 hari, budget 50jt"]     │
│                                     │
│  → Writer Agent aktif               │
│  ─────────────────────              │
│  │ Menyusun TOR...                  │ │
│  └────────────────────              │
└─────────────────────────────────────┘
```

### 5.2 New/Modified Components

| Component | Status | Description |
|-----------|--------|-------------|
| `AgentIndicator.tsx` | NEW | Menampilkan agent yang aktif |
| `ChatArea.tsx` | MODIFY | Integrasi agent indicator |
| `StreamingText.tsx` | MODIFY | Agent-aware streaming |

### 5.3 Frontend Types

```typescript
// types/agent.ts
type AgentType = "supervisor" | "interviewer" | "writer";

interface AgentEvent {
  agent: AgentType;
  action: string;
  message?: string;
}
```

### 5.4 SSE Events Update

Tambahan event type baru di streaming:

```json
{
    "type": "agent_switch",
    "agent": "interviewer",
    "action": "Mulai menggali data TOR..."
}
```

---

## 6. Data Flow Detail

### 6.1 Streaming Flow

```
POST /api/v1/hybrid/stream

Frontend ────────────────────────────► Backend
                                         │
    ◄── SSE: {"type": "agent_switch",    │
    │         "agent": "supervisor"}     │ Supervisor decides
    ◄── SSE: {"type": "thinking_token"}  │
    ◄── SSE: {"type": "agent_switch",    │ Supervisor → Interviewer
    │         "agent": "interviewer"}    │
    ◄── SSE: {"type": "token", ...}      │ Interviewer ngobrol
    ◄── SSE: {"type": "agent_switch",    │ Next turn: Supervisor lagi
    │         "agent": "supervisor"}     │
    ◄── SSE: {"type": "token", ...}      │
    ◄── SSE: {"type": "agent_switch",    │ Supervisor → Writer
    │         "agent": "writer"}         │
    ◄── SSE: {"type": "token", ...}      │ Writer nulis TOR
    ◄── SSE: {"type": "done", ...}       │ Selesai
```

### 6.2 Non-Streaming Flow

```
POST /api/v1/hybrid

1. Supervisor.process(user_message, session_state)
   → Decision: INTERVIEW

2. Interviewer.process(user_message, extracted_data)
   → AgentResult { message, data, confidence }

3. Return ke user
   (tanpa generate — data belum lengkap)
```

---

## 7. Tasks

### Phase 1: Backend Foundation

| # | Task | File | Description |
|---|------|------|-------------|
| 1 | Base agent abstraction | `app/agents/base_agent.py` | Abstract class + AgentContext, AgentResult models |
| 2 | Supervisor Agent | `app/agents/supervisor_agent.py` | Decision maker — INTERVIEW/GENERATE/REVISE/CLARIFY |
| 3 | Interviewer Agent | `app/agents/interviewer_agent.py` | Data gathering — mirip chat_system.py yang existing |
| 4 | Writer Agent | `app/agents/writer_agent.py` | TOR generation — mirip generate_service.py |
| 5 | Update DecisionEngine | `app/core/decision_engine.py` | Ganti routing logic pake Supervisor Agent |
| 6 | Update ChatService | `app/services/chat_service.py` | Integrasi dengan agent system |
| 7 | Update API streaming | `app/api/routes/hybrid.py` | Tambah SSE event `agent_switch` |
| 8 | Update main.py | `app/main.py` | Init agent dependencies |

### Phase 2: Frontend

| # | Task | File | Description |
|---|------|------|-------------|
| 9 | Agent types | `app_frontend/src/types/agent.ts` | NEW: AgentType, AgentEvent |
| 10 | Agent indicator | `app_frontend/src/components/chat/AgentIndicator.tsx` | NEW: UI agent switcher |
| 11 | Update chat store | `app_frontend/src/stores/chat-store.ts` | Handle `agent_switch` events |
| 12 | Update chat components | `app_frontend/src/components/chat/` | Integrate indicator |
| 13 | Update i18n | `app_frontend/src/i18n/locales/id.ts` | Agent labels |

---

## 8. Timeline Estimate

| Phase | Tasks | Estimated Effort |
|-------|-------|------------------|
| Backend Foundation | 1-8 | 3-4 hari |
| Frontend | 9-13 | 2-3 hari |
| Testing & Debug | - | 1-2 hari |
| **Total** | | **~1 minggu** |

---

## 9. Open Questions

1. Supervisor Agent pake LLM call terpisah atau cukup logika Python? (Gua saranin LLM biar fleksibel)
2. Satu turn chat bisa ada >1 agent call? Misal: Supervisor → Interviewer (dalam 1 request)
3. Writer Agent perlu streaming atau cukup blocking?
