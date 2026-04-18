# Task 01 — Pydantic Data Models untuk Decision Engine

## 1. Judul Task

Buat data models Pydantic untuk modul Decision Engine: `HybridOptions`, `RoutingResult`, `EscalationInfo`, `EscalationDecision`, `ProgressState`.

## 2. Deskripsi

Membuat semua model Pydantic yang dipakai di seluruh pipeline Decision Engine. Model ini menjadi contract antara komponen: HybridController (beta0.1.4) ↔ DecisionEngine ↔ EscalationChecker ↔ ProgressTracker.

## 3. Tujuan Teknis

- `HybridOptions` — opsi tambahan dari user (force_generate, language)
- `RoutingResult` — output utama dari `DecisionEngine.route()`
- `EscalationInfo` — detail eskalasi yang di-attach ke result
- `EscalationDecision` — keputusan internal dari EscalationChecker
- `ProgressState` — state tracking progress per session

## 4. Scope

### Yang dikerjakan
- `app/models/routing.py` — `HybridOptions`, `RoutingResult`, `EscalationInfo`
- `app/models/escalation.py` — `EscalationDecision`, `ProgressState`

### Yang tidak dikerjakan
- Logic/service apapun
- API endpoint

## 5. Langkah Implementasi

### Step 1: Buat `app/models/routing.py`

```python
from pydantic import BaseModel
from typing import Literal
from app.models.generate import GenerateResult


class HybridOptions(BaseModel):
    force_generate: bool = False
    language: str = "id"


class EscalationInfo(BaseModel):
    triggered_by: str                    # nama rule yang trigger
    reason: str                          # penjelasan human-readable
    turn_count: int                      # turn saat eskalasi terjadi
    completeness_at_escalation: float    # score saat eskalasi


class RoutingResult(BaseModel):
    session_id: str
    action_taken: Literal[
        "CHAT",
        "GENERATE_STANDARD",
        "GENERATE_ESCALATION",
        "FORCE_GENERATE",
    ]
    chat_response: object | None = None       # ChatResult (import circular prevention)
    generate_response: GenerateResult | None = None
    escalation_info: EscalationInfo | None = None
```

### Step 2: Buat `app/models/escalation.py`

```python
from pydantic import BaseModel


class EscalationDecision(BaseModel):
    should_escalate: bool
    rule_name: str | None = None
    reason: str | None = None
    confidence: float = 0.0


class ProgressState(BaseModel):
    """Tracking progress per session untuk stagnation detection."""
    score_history: list[float] = []
    last_field_filled_turn: int = 0
    lazy_strike_count: int = 0
    short_input_streak: int = 0
    previous_filled_count: int = 0
```

### Step 3: Verifikasi

```python
from app.models.routing import HybridOptions, RoutingResult, EscalationInfo
from app.models.escalation import EscalationDecision, ProgressState

# Test instantiation
opts = HybridOptions()
assert opts.force_generate is False
assert opts.language == "id"

info = EscalationInfo(
    triggered_by="lazy_pattern",
    reason="User menunjukkan pola tidak kooperatif",
    turn_count=5,
    completeness_at_escalation=0.33,
)
assert info.triggered_by == "lazy_pattern"

decision = EscalationDecision(should_escalate=False)
assert decision.confidence == 0.0

progress = ProgressState()
assert progress.lazy_strike_count == 0
assert progress.score_history == []

result = RoutingResult(session_id="test", action_taken="CHAT")
assert result.chat_response is None

print("ALL MODEL TESTS PASSED")
```

## 6. Output yang Diharapkan

Semua model bisa di-instantiate tanpa error dan sesuai type hints.

## 7. Dependencies

- **Task 01 (beta0.1.2)** — `GenerateResult` model
- Tidak ada dependency ke modul lain

## 8. Acceptance Criteria

- [ ] `HybridOptions` memiliki `force_generate` dan `language`
- [ ] `RoutingResult` memiliki `session_id`, `action_taken`, `chat_response`, `generate_response`, `escalation_info`
- [ ] `EscalationInfo` memiliki `triggered_by`, `reason`, `turn_count`, `completeness_at_escalation`
- [ ] `EscalationDecision` memiliki `should_escalate`, `rule_name`, `reason`, `confidence`
- [ ] `ProgressState` memiliki `score_history`, `last_field_filled_turn`, `lazy_strike_count`, `short_input_streak`, `previous_filled_count`
- [ ] Semua model bisa di-serialize ke JSON

## 9. Estimasi

**Low** — ~30 menit
