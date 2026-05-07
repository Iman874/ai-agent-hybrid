# Task 02: OllamaGeneratorProvider

## Status
[ ] Belum dimulai

## Deskripsi
Buat `OllamaGeneratorProvider` yang mengimplementasi `BaseGeneratorProvider` untuk generate TOR via Ollama local LLM.

## File yang Diubah
- **NEW**: `app/ai/ollama_generator_provider.py`
- **MODIFY**: `app/config.py` (tambah `ollama_tor_model`)

## Spesifikasi

### 1. Config Baru di `app/config.py`

```python
# Ollama TOR Generator
ollama_tor_model: str = ""  # Jika kosong, pakai ollama_chat_model
ollama_tor_temperature: float = 0.3
ollama_tor_timeout: int = 120  # TOR generate butuh waktu lebih lama
```

### 2. OllamaGeneratorProvider (`app/ai/ollama_generator_provider.py`)

```python
class OllamaGeneratorProvider(BaseGeneratorProvider):
    """Generate TOR via Ollama local LLM."""

    def __init__(self, settings: Settings):
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
        # Jika ollama_tor_model tidak diset, pakai ollama_chat_model
        self.model = settings.ollama_tor_model or settings.ollama_chat_model
        self.temperature = settings.ollama_tor_temperature
        self.num_ctx = settings.ollama_num_ctx
        self.timeout = settings.ollama_tor_timeout

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def is_available(self) -> bool:
        """Cek apakah Ollama berjalan dan model tersedia."""
        try:
            result = await asyncio.wait_for(
                self.client.list(), timeout=5
            )
            model_ids = [m.model for m in result.models]
            return any(self.model in m for m in model_ids)
        except Exception:
            return False

    async def generate(self, prompt: str) -> str:
        """Generate TOR via Ollama — non-streaming."""
        # prompt adalah string, konversi ke messages format
        messages = [
            {"role": "system", "content": OLLAMA_TOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        
        response = await asyncio.wait_for(
            self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                },
            ),
            timeout=self.timeout,
        )
        return response["message"]["content"]

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Generate TOR via Ollama — streaming."""
        messages = [
            {"role": "system", "content": OLLAMA_TOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        
        stream = await asyncio.wait_for(
            self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                },
            ),
            timeout=self.timeout,
        )
        
        async for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
```

### 3. System Prompt untuk Ollama TOR

Buat di `app/ai/prompts/ollama_generate_tor.py`:

```python
OLLAMA_TOR_SYSTEM_PROMPT = """Kamu adalah penulis dokumen TOR (Term of Reference / Kerangka Acuan Kerja) profesional.

TUGAS:
Buat dokumen TOR yang lengkap, profesional, dan siap digunakan.

ATURAN:
1. Output dalam format Markdown
2. Jangan gunakan placeholder seperti [isi di sini]
3. Jika ada data kurang, buat asumsi masuk akal dan tandai dengan [ASUMSI]
4. Jangan tambahkan penjelasan di luar dokumen TOR
5. Gunakan bahasa Indonesia formal
6. Struktur TOR minimal: Judul, Latar Belakang, Tujuan, Ruang Lingkup, Output, Timeline
"""
```

## Catatan
- Ollama tidak support `response_mime_type="application/json"` — output plain text
- Prompt untuk Ollama harus lebih eksplisit tentang format yang diharapkan
- Timeout lebih panjang dari chat (120s vs 60s) karena generate TOR lebih berat
- Model terpisah (`ollama_tor_model`) memberi fleksibilitas pakai model lebih besar untuk generate
