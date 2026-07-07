# Task 01 — Base Agent Abstraction (BaseAgent, AgentContext, AgentResult)

## Deskripsi

Membangun fondasi abstraksi agent. Mendefinisikan kontrak interface yang WAJIB dipatuhi oleh setiap agent. Tiga komponen utama:

1. **`AgentContext`** — Pydantic model untuk input context ke agent
2. **`AgentResult`** — Pydantic model untuk output dari agent
3. **`BaseAgent`** — Abstract base class yang memaksa setiap agent mengimplementasi `process()` dan `build_messages()`

---

## Tujuan Teknis

- Mendefinisikan kontrak interface ketat menggunakan ABC
- Memastikan setiap agent punya struktur input/output yang konsisten
- Menggunakan Pydantic V2 untuk validasi data otomatis

---

## Scope

### Termasuk

- Membuat direktori `app/agents/` dengan `__init__.py`
- Membuat `app/agents/agent_context.py` berisi `AgentContext`, `AgentResult`
- Membuat `app/agents/base_agent.py` berisi `BaseAgent`

### Tidak Termasuk

- Implementasi agent spesifik (Supervisor, Interviewer, Writer)
- Integrasi dengan DecisionEngine / ChatService
- Frontend changes

---

## Langkah Implementasi

### Langkah 1: Buat struktur direktori

Buat folder `app/agents/` dan file `__init__.py` kosong.

### Langkah 2: Buat `app/agents/agent_context.py` — AgentContext, AgentResult

```python
from enum import Enum
from pydantic import BaseModel, Field
from app.models.tor import TORData


class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    INTERVIEWER = "interviewer"
    WRITER = "writer"


class AgentContext(BaseModel):
    """Input context untuk agent."""
    agent_type: AgentType
    user_message: str | None = None
    session_id: str
    extracted_data: TORData
    missing_fields: list[str]
    completeness: float = 0.0
    turn_count: int = 0
    conversation_history: list[dict] = Field(default_factory=list)
    generated_tor: str | None = None


class AgentResult(BaseModel):
    """Output dari agent."""
    agent: AgentType
    decision: str | None = None        # Supervisor: INTERVIEW/GENERATE/REVISE/CLARIFY
    message: str | None = None         # Natural language response ke user
    data: TORData | None = None        # Extracted TOR data (Interviewer)
    tor_content: str | None = None     # Generated TOR (Writer)
    confidence: float = 0.0
    error: str | None = None
```

### Langkah 3: Buat `app/agents/base_agent.py` — BaseAgent

```python
from abc import ABC, abstractmethod
from app.agents.agent_context import AgentContext, AgentResult


class BaseAgent(ABC):
    name: str
    description: str
    system_prompt: str

    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResult:
        """Process context dan return result."""
        ...

    @abstractmethod
    def build_messages(self, context: AgentContext) -> list[dict]:
        """Build messages array untuk LLM call."""
        ...
```

---

## Output yang Diharapkan

```
app/agents/
├── __init__.py
├── agent_context.py     # AgentContext, AgentResult, AgentType
└── base_agent.py        # BaseAgent (abstract)
```

---

## Acceptance Criteria

### Functional
- [ ] `AgentContext` bisa diinstansiasi dengan semua field
- [ ] `AgentResult` bisa diinstansiasi
- [ ] `AgentType` memiliki 3 values: SUPERVISOR, INTERVIEWER, WRITER
- [ ] `BaseAgent` tidak bisa diinstansiasi langsung
- [ ] Class turunan `BaseAgent` WAJIB implement `process()` dan `build_messages()`

### Code Quality
- [ ] Semua class menggunakan Pydantic V2
- [ ] Type hints lengkap
- [ ] Import hanya dari standard library + pydantic + model yang sudah ada

---

## Dependencies

- `pydantic>=2.0`
- `app.models.tor.TORData` (existing)

---

## Estimasi

**Low** (~1 jam)
