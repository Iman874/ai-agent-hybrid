# Task 05 — Prompt Template: Document-to-TOR

## 1. Judul Task

Buat prompt template `DOCUMENT_TO_TOR_PROMPT` untuk generate TOR dari isi dokumen.

## 2. Deskripsi

Prompt ini instruksikan Gemini untuk membaca dokumen sumber, mengekstrak informasi TOR-relevan, dan output TOR formal lengkap. Prompt juga support konteks tambahan dari user dan RAG examples.

## 3. Tujuan Teknis

- File `app/ai/prompts/document_tor.py` dengan constant `DOCUMENT_TO_TOR_PROMPT`
- Placeholder: `{DOCUMENT_TEXT}`, `{USER_CONTEXT}`, `{RAG_EXAMPLES}`
- Helper function `build_document_prompt(document_text, user_context, rag_examples)` di `GeminiPromptBuilder`

## 4. Scope

### Yang dikerjakan
- Prompt template
- Builder method di `GeminiPromptBuilder`

### Yang tidak dikerjakan
- API endpoint (task selanjutnya)
- Streamlit UI (task selanjutnya)

## 5. Langkah Implementasi

### Step 1: Buat `app/ai/prompts/document_tor.py`

```python
DOCUMENT_TO_TOR_PROMPT = """# INSTRUKSI
Kamu adalah pembuat dokumen TOR (Term of Reference / Kerangka Acuan Kerja) profesional pemerintah Indonesia.

## TUGAS UTAMA
Berdasarkan DOKUMEN SUMBER yang diberikan di bawah, buat TOR yang lengkap dan formal.

## LANGKAH KERJA
1. Baca dan pahami dokumen sumber secara menyeluruh
2. Identifikasi informasi kunci: nama kegiatan, tujuan, ruang lingkup, target, anggaran, timeline
3. Susun TOR dalam format standar pemerintah Indonesia
4. Jika ada informasi kurang di dokumen, berikan catatan [ASUMSI] dan isi dengan estimasi wajar
5. Jika ada informasi yang bertentangan, gunakan yang paling logis

## KONTEKS TAMBAHAN DARI USER
{USER_CONTEXT}

## DOKUMEN SUMBER
---
{DOCUMENT_TEXT}
---

{RAG_EXAMPLES}

## FORMAT OUTPUT WAJIB
Tulis TOR dalam format Markdown dengan struktur berikut:

# [JUDUL KEGIATAN]

## 1. Latar Belakang
(Konteks, alasan kegiatan, dasar hukum jika ada)

## 2. Tujuan
### 2.1 Tujuan Umum
### 2.2 Tujuan Khusus

## 3. Ruang Lingkup
(Batasan dan cakupan pekerjaan)

## 4. Sasaran / Target Peserta
(Jumlah peserta, kriteria, instansi)

## 5. Output / Deliverable
(Daftar output yang diharapkan)

## 6. Jadwal Pelaksanaan
(Timeline, tahapan, durasi)

## 7. Anggaran
(Estimasi biaya, breakdown jika ada)

## 8. Penutup

## ATURAN PENULISAN
- Gunakan Bahasa Indonesia formal dan baku
- Gunakan kosakata birokrasi pemerintah yang sesuai
- Minimal 500 kata
- Tandai bagian asumsi dengan [ASUMSI] jika data tidak tersedia
- Jangan mengarang data yang tidak ada di dokumen sumber
"""
```

### Step 2: Tambah method di `GeminiPromptBuilder`

Di `app/core/gemini_prompt_builder.py`, tambah:

```python
from app.ai.prompts.document_tor import DOCUMENT_TO_TOR_PROMPT

@staticmethod
def build_from_document(
    document_text: str,
    user_context: str = "",
    rag_examples: str | None = None,
) -> str:
    """Build prompt untuk document-to-TOR generation."""
    prompt = DOCUMENT_TO_TOR_PROMPT.replace("{DOCUMENT_TEXT}", document_text)
    prompt = prompt.replace("{USER_CONTEXT}", user_context or "Tidak ada konteks tambahan.")

    if rag_examples:
        prompt = prompt.replace("{RAG_EXAMPLES}", f"## REFERENSI STYLE\n{rag_examples}")
    else:
        prompt = prompt.replace(
            "{RAG_EXAMPLES}",
            "## REFERENSI STYLE\nTidak ada referensi tersedia. Gunakan best-practice umum."
        )

    return prompt
```

## 6. Output yang Diharapkan

```python
>>> from app.core.gemini_prompt_builder import GeminiPromptBuilder
>>> prompt = GeminiPromptBuilder.build_from_document(
...     document_text="Laporan workshop AI...",
...     user_context="Buat TOR lanjutan 2026",
... )
>>> "DOKUMEN SUMBER" in prompt
True
>>> "Laporan workshop AI" in prompt
True
```

## 7. Dependencies

- Tidak ada dependency task sebelumnya (file prompt berdiri sendiri)

## 8. Acceptance Criteria

- [ ] File `app/ai/prompts/document_tor.py` ada
- [ ] `DOCUMENT_TO_TOR_PROMPT` mencakup instruksi, format output, aturan penulisan
- [ ] Placeholder `{DOCUMENT_TEXT}`, `{USER_CONTEXT}`, `{RAG_EXAMPLES}` bisa di-replace
- [ ] `GeminiPromptBuilder.build_from_document()` method tersedia
- [ ] RAG examples optional (fallback ke "tidak ada referensi")

## 9. Estimasi

**Low** — ~30 menit
