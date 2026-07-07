# Task 03 — Interviewer Agent

## Deskripsi

Interviewer Agent bertugas **menggali data TOR dari user**. Ini mirip dengan fungsi `ChatService.process_message()` yang existing, tapi LEBIH FOKUS — cuma ngegas data, gak perlu mikirin soal generate atau escalation.

Prompt-nya lebih simpel dari `chat_system.py` yang sekarang karena gak perlu handle 3 status (NEED_MORE_INFO, READY_TO_GENERATE, ESCALATE). Cuma perlu ngobrol dan mapping data ke JSON.

---

## Tujuan Teknis

- Fokus: gali data TOR, output JSON
- Prompt lebih kecil & simpel dari chat_system.py existing
- Output: extracted_data (TORData) tanpa perlu status generate

---

## Scope

### Termasuk

- Membuat `app/agents/interviewer_agent.py`
- System prompt interviewer (turunan dari `chat_system.py` yang sudah ada, tapi disederhanakan)
- Output: AgentResult dengan `data` (TORData) + `message` (respon ke user)
- LLM call + JSON parsing + fallback

### Tidak Termasuk

- Integrasi ke ChatService (task 06)
- Completeness checking (itu urusan Supervisor)

---

## System Prompt (Draft)

```
Kamu adalah Interviewer Agent yang bertugas mengumpulkan data untuk TOR.
Output SELALU dalam format JSON tanpa teks tambahan.

Data yang harus dikumpulkan:
- judul: Nama/judul kegiatan
- latar_belakang: Alasan dan konteks
- tujuan: Apa yang ingin dicapai
- ruang_lingkup: Cakupan kegiatan
- output: Hasil yang diharapkan
- timeline: Jadwal pelaksanaan
- estimasi_biaya: Perkiraan anggaran (opsional)

ATURAN:
- Tanyakan 2-3 hal per turn
- Jangan tanya ulang yang sudah diisi
- Bahasa Indonesia profesional

Output JSON:
{
    "message": "Pesan natural ke user",
    "extracted_so_far": { ... },
    "missing_fields": ["field1", ...]
}
```

---

## Acceptance Criteria

- [ ] Interviewer bisa ngobrol dengan user untuk gali data
- [ ] Output JSON dengan extracted_so_far
- [ ] Prompt lebih fokus daripada chat_system.py yang existing
- [ ] Error handling + retry kalo JSON parsing gagal

---

## Dependencies

- Task 01 (BaseAgent, AgentContext, AgentResult)
- ZenChatProvider / provider sesuai config

---

## Estimasi

**Low-Medium** (~2 jam)
