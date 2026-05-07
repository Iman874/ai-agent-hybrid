# Task 03: OllamaPromptBuilder + Prompt Templates

## Status
[ ] Belum dimulai

## Deskripsi
Buat `OllamaPromptBuilder` untuk membangun prompt yang dioptimalkan untuk Ollama local LLM. Juga buat prompt templates untuk standard dan escalation mode.

## File yang Diubah
- **NEW**: `app/core/ollama_prompt_builder.py`
- **NEW**: `app/ai/prompts/ollama_generate_tor.py` (standard prompt)
- **NEW**: `app/ai/prompts/ollama_escalation.py` (escalation prompt)

## Spesifikasi

### 1. OllamaPromptBuilder (`app/core/ollama_prompt_builder.py`)

```python
class OllamaPromptBuilder:
    """Build prompt untuk Ollama TOR generation."""

    @staticmethod
    def build_standard(
        data: TORData,
        rag_examples: str | None = None,
        format_spec: str | None = None,
    ) -> str:
        """Build prompt string untuk standard TOR generation via Ollama."""
        data_json = data.model_dump_json(indent=2, exclude_none=True)
        
        prompt = OLLAMA_STANDARD_PROMPT.replace("{DATA_JSON}", data_json)
        
        if rag_examples:
            prompt = prompt.replace("{RAG_EXAMPLES}", rag_examples)
        else:
            prompt = prompt.replace(
                "## REFERENSI KONTEN (dari RAG, jika ada)\n{RAG_EXAMPLES}",
                ""
            )
        
        prompt = prompt.replace("{FORMAT_SPEC}", format_spec or "")
        return prompt

    @staticmethod
    def build_escalation(
        chat_history: str,
        partial_data: TORData | None = None,
        rag_examples: str | None = None,
        format_spec: str | None = None,
    ) -> str:
        """Build prompt string untuk escalation mode via Ollama."""
        prompt = OLLAMA_ESCALATION_PROMPT.replace("{FULL_CHAT_HISTORY}", chat_history)
        
        if partial_data:
            partial_json = partial_data.model_dump_json(indent=2, exclude_none=True)
            prompt += f"\n\n## DATA PARSIAL YANG TERSEDIA\n{partial_json}"
        
        if rag_examples:
            prompt += f"\n\n## REFERENSI KONTEN\n{rag_examples}"
        
        prompt = prompt.replace("{FORMAT_SPEC}", format_spec or "")
        return prompt
```

### 2. Standard Prompt (`app/ai/prompts/ollama_generate_tor.py`)

```python
OLLAMA_STANDARD_PROMPT = """Kamu adalah penulis dokumen TOR (Term of Reference / Kerangka Acuan Kerja) profesional.

## TUGAS
Buatkan dokumen TOR yang lengkap, profesional, dan siap digunakan berdasarkan data berikut.

## DATA INPUT
{DATA_JSON}

## REFERENSI KONTEN (dari RAG, jika ada)
{RAG_EXAMPLES}

{FORMAT_SPEC}

## ATURAN PENTING
1. Output dalam format Markdown — jangan gunakan JSON
2. Jangan gunakan placeholder seperti [isi di sini] — isi dengan data yang ada
3. Jika ada data yang kurang, buat asumsi masuk akal dan tandai dengan [ASUMSI]
4. Jangan tambahkan penjelasan di luar dokumen TOR
5. Tulis langsung dokumen TOR-nya, tanpa kata pengantar

## STRUKTUR MINIMAL
- Judul Kegiatan
- Latar Belakang
- Tujuan
- Ruang Lingkup
- Output Kegiatan
- Timeline Pelaksanaan
"""
```

### 3. Escalation Prompt (`app/ai/prompts/ollama_escalation.py`)

```python
OLLAMA_ESCALATION_PROMPT = """Kamu adalah penulis dokumen TOR (Term of Reference) profesional.

## SITUASI
User telah berdiskusi tentang pembuatan TOR tapi percakapan tidak menghasilkan data lengkap. Kamu harus membuat TOR terbaik berdasarkan informasi yang tersedia.

## PERCAKAPAN
{FULL_CHAT_HISTORY}

## INSTRUKSI KHUSUS
1. Analisis percakapan di atas untuk mengekstrak semua informasi yang bisa dijadikan data TOR
2. Untuk informasi yang TIDAK tersedia dalam percakapan, buat asumsi yang masuk akal dan tandai dengan tag [ASUMSI]
3. Output dalam format Markdown — jangan gunakan JSON
4. Jangan tambahkan penjelasan di luar dokumen TOR

{FORMAT_SPEC}
"""
```

## Catatan
- OllamaPromptBuilder return **string prompt** (bukan list of messages) — konsisten dengan GeminiPromptBuilder
- Prompt untuk Ollama lebih eksplisit tentang format Markdown (karena Ollama tidak bisa `response_mime_type`)
- Template prompt dipisah file agar mudah di-maintain
