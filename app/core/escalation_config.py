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
