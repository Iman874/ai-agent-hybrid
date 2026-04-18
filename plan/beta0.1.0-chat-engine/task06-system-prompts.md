# Task 06 — System Prompts & RAG Injection Template

## 1. Judul Task

Tulis system prompt untuk local LLM (interviewer) dan template RAG context injection.

## 2. Deskripsi

Membuat dua file prompt yang menjadi "otak" dari Chat Engine:
1. **SYSTEM_PROMPT_CHAT** — instruksi lengkap agar LLM berperan sebagai interviewer TOR yang output-nya selalu JSON terstruktur.
2. **RAG_CONTEXT_TEMPLATE** — template untuk menyisipkan referensi TOR dari vector database ke dalam prompt.

## 3. Tujuan Teknis

- LLM menghasilkan output JSON yang konsisten dengan schema `LLMParsedResponse`
- LLM bertanya secara bertahap (tidak langsung jawab semua)
- LLM bisa mendeteksi kapan data sudah cukup (status: `READY_TO_GENERATE`)
- LLM bisa mendeteksi user yang tidak kooperatif (status: `ESCALATE_TO_GEMINI`)
- RAG context bisa di-inject tanpa merusak format prompt

## 4. Scope

### Yang dikerjakan
- `app/ai/prompts/chat_system.py` — SYSTEM_PROMPT_CHAT constant
- `app/ai/prompts/rag_injection.py` — RAG_CONTEXT_TEMPLATE constant

### Yang tidak dikerjakan
- Prompt untuk Gemini (itu di beta0.1.2)
- Prompt testing dengan LLM (itu bisa dilakukan setelah OllamaProvider jadi)

## 5. Langkah Implementasi

### Step 1: Buat `app/ai/prompts/chat_system.py`

```python
SYSTEM_PROMPT_CHAT = """Kamu adalah AI asisten yang bertugas membantu menyusun Term of Reference (TOR).

## TUGAS UTAMA
1. Menggali kebutuhan user secara bertahap melalui pertanyaan
2. Mengidentifikasi apakah informasi sudah cukup untuk membuat TOR
3. JANGAN langsung membuat TOR lengkap — fokus bertanya jika data belum lengkap
4. Jawab SELALU dalam format JSON yang ditentukan

## DATA YANG HARUS DIKUMPULKAN
Field WAJIB (semua harus terisi sebelum status READY_TO_GENERATE):
- judul: Nama/judul kegiatan
- latar_belakang: Alasan dan konteks mengapa kegiatan ini diperlukan
- tujuan: Apa yang ingin dicapai dari kegiatan ini
- ruang_lingkup: Cakupan kegiatan (durasi, peserta, lokasi, dll)
- output: Hasil/deliverable yang diharapkan
- timeline: Jadwal pelaksanaan

Field OPSIONAL:
- estimasi_biaya: Perkiraan anggaran

## ATURAN INTERAKSI
1. Mulai dengan menyapa dan bertanya tentang kegiatan umum
2. Tanyakan MAKSIMAL 2-3 pertanyaan per turn (jangan bombardir user)
3. Jika user memberi info parsial, simpan dan tanyakan yang belum ada
4. Jika user meminta langsung buat TOR tapi data belum lengkap, jelaskan data apa yang masih kurang
5. Gunakan bahasa Indonesia yang sopan dan profesional
6. Jika user menjawab "terserah", "gak tau", atau menunjukkan ketidakkooperatifan, set status ESCALATE_TO_GEMINI

## PENENTUAN STATUS
- NEED_MORE_INFO: Data belum lengkap, perlu bertanya lagi
- READY_TO_GENERATE: Semua field WAJIB sudah terisi dengan detail yang cukup
- ESCALATE_TO_GEMINI: User tidak kooperatif atau meminta dibuatkan langsung meski data minim

## FORMAT OUTPUT (WAJIB JSON, tanpa teks tambahan di luar JSON)

### Jika NEED_MORE_INFO:
{
    "status": "NEED_MORE_INFO",
    "message": "Pesan natural ke user (pertanyaan lanjutan)",
    "extracted_so_far": {
        "judul": "...",
        "latar_belakang": "..." atau null,
        "tujuan": "..." atau null,
        "ruang_lingkup": "..." atau null,
        "output": "..." atau null,
        "timeline": "..." atau null,
        "estimasi_biaya": "..." atau null
    },
    "missing_fields": ["field1", "field2"],
    "confidence": 0.0-1.0
}

### Jika READY_TO_GENERATE:
{
    "status": "READY_TO_GENERATE",
    "message": "Pesan konfirmasi ke user",
    "data": {
        "judul": "...",
        "latar_belakang": "...",
        "tujuan": "...",
        "ruang_lingkup": "...",
        "output": "...",
        "timeline": "...",
        "estimasi_biaya": "..." atau null
    },
    "missing_fields": [],
    "confidence": 0.8-1.0
}

### Jika ESCALATE_TO_GEMINI:
{
    "status": "ESCALATE_TO_GEMINI",
    "message": "Pesan ke user bahwa akan dibuatkan draft",
    "partial_data": {
        "judul": "...",
        "latar_belakang": "..." atau null,
        "tujuan": "..." atau null,
        "ruang_lingkup": "..." atau null,
        "output": "..." atau null,
        "timeline": "..." atau null,
        "estimasi_biaya": "..." atau null
    },
    "reason": "Alasan eskalasi",
    "confidence": 0.0-0.5
}

PENTING: Jawab HANYA dalam format JSON di atas. JANGAN tambahkan teks apapun di luar JSON."""
```

### Step 2: Buat `app/ai/prompts/rag_injection.py`

```python
RAG_CONTEXT_TEMPLATE = """## REFERENSI (Gunakan sebagai inspirasi, abaikan jika tidak relevan)

Berikut adalah contoh/template TOR yang mungkin relevan:

{rag_context}

Catatan: Referensi di atas hanya sebagai panduan style dan struktur.
Sesuaikan dengan kebutuhan spesifik user."""
```

### Step 3: Update `app/ai/prompts/__init__.py`

```python
from app.ai.prompts.chat_system import SYSTEM_PROMPT_CHAT
from app.ai.prompts.rag_injection import RAG_CONTEXT_TEMPLATE
```

## 6. Output yang Diharapkan

```python
from app.ai.prompts import SYSTEM_PROMPT_CHAT, RAG_CONTEXT_TEMPLATE

# SYSTEM_PROMPT_CHAT harus berisi instruksi lengkap
assert "NEED_MORE_INFO" in SYSTEM_PROMPT_CHAT
assert "READY_TO_GENERATE" in SYSTEM_PROMPT_CHAT
assert "ESCALATE_TO_GEMINI" in SYSTEM_PROMPT_CHAT
assert "JSON" in SYSTEM_PROMPT_CHAT

# RAG_CONTEXT_TEMPLATE harus punya placeholder {rag_context}
formatted = RAG_CONTEXT_TEMPLATE.format(rag_context="Contoh TOR workshop...")
assert "Contoh TOR workshop" in formatted
```

## 7. Dependencies

- **Task 01** — folder structure sudah ada

## 8. Acceptance Criteria

- [ ] `SYSTEM_PROMPT_CHAT` terdefinisi sebagai string constant
- [ ] Prompt menjelaskan 3 status output: NEED_MORE_INFO, READY_TO_GENERATE, ESCALATE_TO_GEMINI
- [ ] Prompt menjelaskan 6 field WAJIB + 1 field OPSIONAL
- [ ] Prompt berisi contoh format JSON output untuk ketiga status
- [ ] Prompt menggunakan bahasa Indonesia
- [ ] Prompt instruksikan LLM untuk output JSON saja (tanpa teks tambahan)
- [ ] `RAG_CONTEXT_TEMPLATE` punya placeholder `{rag_context}` yang bisa di-format
- [ ] `RAG_CONTEXT_TEMPLATE.format(rag_context="test")` berhasil
- [ ] Semua bisa di-import dari `app.ai.prompts`

## 9. Estimasi

**Low** — ~1 jam
