# Task 02 — Supervisor Agent

## Deskripsi

Supervisor Agent adalah "otak" koordinator. Dia nerima input user + state session, trus mutusin langkah selanjutnya. Keputusannya: INTERVIEW (gali data), GENERATE (buat TOR), REVISE (revisi TOR yang udah ada), atau CLARIFY (tanya balik).

Prompt-nya fokus: **cuma nentuin "next action"** — gak perlu nulis TOR atau ngegas data.

---

## Tujuan Teknis

- Supervisor pake LLM, bukan Python if-else
- Output decision JSON: action + reason + context

---

## Scope

### Termasuk

- Membuat `app/agents/supervisor_agent.py`
- System prompt khusus supervisor
- Logic decision: INTERVIEW / GENERATE / REVISE / CLARIFY
- Menggunakan ZenChatProvider atau provider dari session config

### Tidak Termasuk

- Integrasi ke DecisionEngine (task 05)
- Error handling spesifik

---

## Langkah Implementasi

### Langkah 1: System Prompt Supervisor

```python
SUPERVISOR_SYSTEM_PROMPT = """Kamu adalah Supervisor Agent yang mengoordinasikan pembuatan dokumen TOR.

Tugasmu:
1. Analisis input user + state session + riwayat percakapan
2. Tentukan action terbaik

Data TOR yang harus dikumpulkan:
wajib: judul, latar_belakang, tujuan, ruang_lingkup, output, timeline
opsional: estimasi_biaya

Output JSON WAJIB:
{
    "decision": "INTERVIEW" | "GENERATE" | "REVISE" | "CLARIFY",
    "reason": "Penjelasan singkat kenapa ambil keputusan ini",
}

Aturan:
- INTERVIEW: data belum lengkap, perlu gali lebih lanjut
- GENERATE: semua field wajib terisi cukup detail → lanjut ke Writer
- REVISE: user minta revisi TOR yang sudah ada (generated_tor ada)
- CLARIFY: input user ambigu, perlu klarifikasi sebelum lanjut
"""
```

### Langkah 2: Implementasi

```python
class SupervisorAgent(BaseAgent):
    name = "supervisor"
    description = "Koordinasi agent dan tentukan next action"

    def __init__(self, settings: Settings):
        self.provider = ZenChatProvider(settings)  # atau from settings
        self.system_prompt = SUPERVISOR_SYSTEM_PROMPT

    async def process(self, context: AgentContext) -> AgentResult:
        messages = self.build_messages(context)
        raw = await self.provider.chat(messages)
        decision = json.loads(raw["content"])
        return AgentResult(
            agent=AgentType.SUPERVISOR,
            decision=decision["decision"],
            message=decision.get("reason", ""),
            confidence=0.8,
        )

    def build_messages(self, context: AgentContext) -> list[dict]:
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._build_prompt(context)},
        ]

    def _build_prompt(self, context: AgentContext) -> str:
        ...
```

---

## Acceptance Criteria

- [ ] Supervisor bisa output decision INTERVIEW, GENERATE, REVISE, CLARIFY
- [ ] Decision berdasarkan state completeness + input user
- [ ] Prompt hanya fokus nentuin action, bukan nulis/gali data
- [ ] Error handling kalo LLM output JSON invalid

---

## Dependencies

- Task 01 (BaseAgent, AgentContext)
- ZenChatProvider (existing)

---

## Estimasi

**Low** (~2 jam)
