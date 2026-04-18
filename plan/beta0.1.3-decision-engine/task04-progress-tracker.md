# Task 04 — ProgressTracker: Track Completeness & Stagnation

## 1. Judul Task

Implementasikan `ProgressTracker` — class in-memory untuk tracking progress completeness per session, deteksi field baru terisi, dan state management untuk stagnation detection.

## 2. Deskripsi

ProgressTracker menyimpan state per session (score history, field counts, lazy strikes) di memory. State ini digunakan oleh EscalationChecker untuk menentukan stagnation dan idle turns. Data di-reset saat session selesai.

## 3. Tujuan Teknis

- `get(session_id) → ProgressState` — ambil atau buat state baru
- `update_after_chat(session_id, completeness, filled_count)` — update setelah chat turn
- `reset(session_id)` — hapus state (saat session selesai/di-reset)

## 4. Scope

### Yang dikerjakan
- `app/core/progress_tracker.py` — class `ProgressTracker`

### Yang tidak dikerjakan
- Persistensi ke database (in-memory only untuk v0.1)
- TTL/eviction

## 5. Langkah Implementasi

### Step 1: Buat `app/core/progress_tracker.py`

```python
import logging
from app.models.escalation import ProgressState

logger = logging.getLogger("ai-agent-hybrid.progress")


class ProgressTracker:
    """Track completeness progress per session (in-memory)."""

    def __init__(self):
        self._states: dict[str, ProgressState] = {}

    def get(self, session_id: str) -> ProgressState:
        """Ambil state, buat baru jika belum ada."""
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

### Step 2: Verifikasi

```python
from app.core.progress_tracker import ProgressTracker

tracker = ProgressTracker()

# Test 1: Get creates new state
state = tracker.get("session-1")
assert state.score_history == []
assert state.lazy_strike_count == 0
print("Test 1: get creates new state OK")

# Test 2: Update after chat
tracker.update_after_chat("session-1", 0.33, 2)
state = tracker.get("session-1")
assert state.score_history == [0.33]
assert state.last_field_filled_turn == 1
assert state.previous_filled_count == 2
print("Test 2: update_after_chat OK")

# Test 3: No new field → last_field_filled_turn stays
tracker.update_after_chat("session-1", 0.33, 2)  # same filled count
state = tracker.get("session-1")
assert state.score_history == [0.33, 0.33]
assert state.last_field_filled_turn == 1  # unchanged
print("Test 3: no new field OK")

# Test 4: New field → last_field_filled_turn updates
tracker.update_after_chat("session-1", 0.5, 3)
state = tracker.get("session-1")
assert state.last_field_filled_turn == 3  # turn 3
assert state.previous_filled_count == 3
print("Test 4: new field updates OK")

# Test 5: Reset
tracker.reset("session-1")
state2 = tracker.get("session-1")
assert state2.score_history == []
print("Test 5: reset OK")

print("ALL PROGRESS TRACKER TESTS PASSED")
```

## 6. Output yang Diharapkan

ProgressTracker yang track score history dan field count per session di memory.

## 7. Dependencies

- **Task 01** — `ProgressState` model

## 8. Acceptance Criteria

- [ ] `get()` return existing state atau buat baru
- [ ] `update_after_chat()` append score ke history
- [ ] `update_after_chat()` update `last_field_filled_turn` hanya jika ada field baru
- [ ] `reset()` hapus state untuk session
- [ ] Multiple sessions dikelola secara independen

## 9. Estimasi

**Low** — ~45 menit
