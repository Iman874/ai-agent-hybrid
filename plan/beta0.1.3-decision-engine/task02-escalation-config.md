# Task 02 — EscalationConfig: Konfigurasi Rules Eskalasi

## 1. Judul Task

Buat `EscalationConfig` dataclass — konfigurasi semua threshold dan regex pattern untuk smart escalation rules.

## 2. Deskripsi

Konfigurasi terpusat untuk semua parameter eskalasi: max turns, lazy patterns (regex), short input threshold, stagnation turns, idle turns. Menggunakan `dataclass` agar bisa di-override dari Settings jika diperlukan nanti.

## 3. Tujuan Teknis

- `EscalationConfig` dataclass dengan semua default values
- Lazy patterns sebagai list regex string (case-insensitive)
- Semua threshold bisa di-override saat instantiation

## 4. Scope

### Yang dikerjakan
- `app/core/escalation_config.py` — `EscalationConfig` dataclass

### Yang tidak dikerjakan
- Logic pengecekan (itu task 03)
- Integration dengan Settings (nanti jika diperlukan)

## 5. Langkah Implementasi

### Step 1: Buat `app/core/escalation_config.py`

```python
from dataclasses import dataclass, field


@dataclass
class EscalationConfig:
    """Semua threshold untuk smart escalation."""

    # Rule 1: Absolute max turns — pasti escalate
    absolute_max_turns: int = 10

    # Rule 2: Max idle turns — lama tanpa field baru terisi
    max_idle_turns: int = 5

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
    lazy_tolerance: int = 1           # berapa kali lazy dimaafkan

    # Rule 4: Short input consecutive
    short_input_max_chars: int = 15
    short_input_consecutive: int = 2

    # Rule 5: Stagnation
    stagnation_turns: int = 3         # berapa turn tanpa kenaikan score
```

### Step 2: Verifikasi

```python
from app.core.escalation_config import EscalationConfig

# Test default
config = EscalationConfig()
assert config.absolute_max_turns == 10
assert config.max_idle_turns == 5
assert config.lazy_tolerance == 1
assert config.short_input_max_chars == 15
assert config.stagnation_turns == 3
assert len(config.lazy_patterns) >= 10

# Test override
custom = EscalationConfig(absolute_max_turns=5, lazy_tolerance=2)
assert custom.absolute_max_turns == 5
assert custom.lazy_tolerance == 2

print("ALL ESCALATION CONFIG TESTS PASSED")
```

## 6. Output yang Diharapkan

Dataclass yang bisa di-instantiate dengan default values atau custom override.

## 7. Dependencies

- Tidak ada (standalone dataclass)

## 8. Acceptance Criteria

- [ ] `EscalationConfig` memiliki semua 5 groups of rules
- [ ] Default values sesuai design doc
- [ ] `lazy_patterns` berisi minimal 10 regex patterns bahasa Indonesia
- [ ] Semua field bisa di-override saat instantiation
- [ ] `lazy_tolerance` default 1 (maafkan lazy pertama)

## 9. Estimasi

**Low** — ~20 menit
