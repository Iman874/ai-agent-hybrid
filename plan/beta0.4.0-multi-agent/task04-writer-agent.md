# Task 04 — Writer Agent

## Deskripsi

Writer Agent bertugas **menulis TOR final** dari data yang udah dikumpulkan sama Interviewer. Ini mirip `GenerateService.generate_tor()` yang existing — bedanya Writer Agent adalah wrapper LLM yang bisa dipanggil kapan aja, gak cuma pas "READY_TO_GENERATE".

Bisa juga dipanggil buat **revisi** kalo user minta perubahan.

---

## Tujuan Teknis

- Generate TOR dari extracted_data (TORData)
- Support revisi: nerima TOR existing + instruksi revisi
- Output: `tor_content` string (Markdown)

---

## Scope

### Termasuk

- Membuat `app/agents/writer_agent.py`
- System prompt writer (turunan dari `generate_tor.py`)
- Support generate baru & revisi
- Post-processing (cleanup, word count — reuse existing PostProcessor)

### Tidak Termasuk

- Caching logic (masih bisa pake TORCache existing kalo perlu)
- Export (DOCX/PDF)

---

## System Prompt (Draft)

Generate:
```
Kamu adalah Writer Agent yang bertugas menulis TOR profesional.
Gunakan data berikut untuk membuat TOR yang lengkap dan siap pakai.

DATA:
{extracted_data_json}

FORMAT:
- Gunakan bahasa Indonesia formal
- Format Markdown
- Struktur: Latar Belakang, Tujuan, Ruang Lingkup, Output, Timeline, Estimasi Biaya
```

Revisi:
```
Kamu adalah Writer Agent yang bertugas merevisi TOR.

TOR SAAT INI:
{existing_tor}

PERMINTAAN REVISI:
{user_message}

Buat TOR yang sudah direvisi sesuai permintaan.
```

---

## Acceptance Criteria

- [ ] Writer bisa generate TOR dari extracted_data
- [ ] Writer bisa revisi TOR existing berdasarkan instruksi user
- [ ] Output Markdown dengan struktur TOR yang benar
- [ ] Post-processing jalan (word count, formatting)

---

## Dependencies

- Task 01 (BaseAgent, AgentContext, AgentResult)
- Task 03 (Interviewer Agent — untuk dapetin data)
- `app.core.post_processor` (existing)
- `app.models.generate.TORDocument` (existing)

---

## Estimasi

**Low-Medium** (~2 jam)
