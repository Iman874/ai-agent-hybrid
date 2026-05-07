# Beta 0.2.9 — Ollama Local TOR Generator

## 1. Ringkasan

Saat ini **hanya Gemini API** yang bisa menghasilkan dokumen TOR. Ollama hanya digunakan untuk fase *chat interview*. Ini menciptakan **single point of failure** dan **ketergantungan penuh pada cloud**.

Beta 0.2.9 menambahkan kemampuan **Ollama (local LLM) sebagai generator TOR** — sehingga sistem bisa berfungsi **fully offline** untuk TOR sederhana, dan menggunakan Gemini hanya untuk kasus kompleks atau sebagai fallback.

---

## 2. Analisis Masalah

### 2.1 Kondisi Saat Ini

```
Chat (Ollama) → READY_TO_GENERATE → GenerateService → Gemini → TOR
                                        ↓
                                  HANYA GeminiProvider
                                  HANYA generate() / generate_stream()
                                  HANYA GeminiPromptBuilder
                                  HANYA CostController (Gemini rate limit)
```

### 2.2 Dampak

| # | Problem | Dampak |
|---|---------|--------|
| 1 | **Full cloud dependency** | Tanpa internet / API key → tidak bisa generate TOR sama sekali |
| 2 | **Biaya** | Setiap generate kena biaya Gemini, padahal TOR sederhana bisa local |
| 3 | **Rate limit** | CostController membatasi panggilan Gemini, tapi tidak ada fallback |
| 4 | **Latency** | Gemini call butuh network round-trip, local LLM bisa lebih cepat |
| 5 | **No offline mode** | User tidak punya opsi fully offline |

### 2.3 Root Cause

- `GenerateService` secara **hardcode** hanya menerima `GeminiProvider`
- `DecisionEngine.route()` saat `READY_TO_GENERATE` langsung panggil `generate_service.generate_tor()` → Gemini
- Tidak ada abstraction layer untuk TOR generation provider
- `GeminiPromptBuilder` menggunakan prompt yang dioptimalkan untuk Gemini (dengan `response_mime_type="application/json"`)

---

## 3. Keputusan Arsitektur (FINAL — TIDAK BOLEH DIUBAH)

### 3.1 Provider Abstraction untuk TOR Generation

```
Sebelum:
  GenerateService → GeminiProvider (hardcode)

Sesudah:
  GenerateService → BaseGeneratorProvider (abstract)
                      ├── GeminiGeneratorProvider (existing, refactored)
                      └── OllamaGeneratorProvider (new)
```

**Rules:**
- `BaseGeneratorProvider` adalah abstract class dengan method `generate()` dan `generate_stream()`
- Kedua provider mengembalikan format output yang **IDENTIK** (`AsyncGenerator[str, None]` untuk stream)
- `GenerateService` menerima **semua provider** dan memilih berdasarkan mode/ketersediaan
- `DecisionEngine` menentukan provider mana yang dipakai berdasarkan aturan routing

### 3.2 Routing Logic: Kapan Ollama, Kapan Gemini?

```
Jika mode generate = "local":
  → OllamaGeneratorProvider (WAJIB)
  → Gagal → fallback ke Gemini (jika tersedia)

Jika mode generate = "gemini":
  → GeminiGeneratorProvider (WAJIB)
  → Gagal → fallback ke Ollama (jika tersedia)

Jika mode generate = "auto" (default):
  → Cek kompleksitas data:
      - completeness_score >= 0.8 → Ollama (data sudah lengkap, TOR sederhana)
      - completeness_score < 0.8 → Gemini (butuh escalation, data parsial)
  → Jika provider yang dipilih gagal → fallback ke provider lain
```

**Rules:**
- Mode "local" dan "gemini" bisa dipilih user dari frontend
- Mode "auto" adalah default — sistem memilih yang terbaik
- Fallback WAJIB ada — jika provider utama gagal, coba provider lain
- Jika kedua provider gagal → return error terstruktur

### 3.3 Prompt Builder per Provider

```
BasePromptBuilder (abstract)
  ├── GeminiPromptBuilder (existing — pakai prompt untuk Gemini)
  └── OllamaPromptBuilder (new — prompt untuk local LLM)
```

**Kenapa dipisah?**
- Gemini bisa pakai `response_mime_type="application/json"` — Ollama tidak
- Ollama butuh instruksi format yang lebih eksplisit dalam prompt
- Ollama untuk TOR generation pakai format **chat messages** (bukan single prompt string)
- Masing-masing provider punya karakteristik berbeda dalam hal:
  - Panjang konteks (Ollama terbatas `num_ctx`)
  - Kemampuan mengikuti format kompleks
  - Gaya output (Ollama lebih suka bullet points, Gemini lebih naratif)

### 3.4 OllamaGeneratorProvider — Detail

```python
class OllamaGeneratorProvider(BaseGeneratorProvider):
    """
    Generate TOR via Ollama local LLM.
    Menggunakan chat_stream() dengan prompt khusus TOR.
    """
    
    async def generate(self, prompt: str) -> str:
        # Convert prompt string ke messages format
        # Panggil self.ollama.chat(messages)
        # Return full text
    
    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        # Convert prompt string ke messages format
        # Panggil self.ollama.chat_stream(messages)
        # Yield token per token
```

**Key differences from Gemini:**
- Input: prompt dalam format **chat messages** (bukan single string)
- Output: yield dari `ollama.chat_stream()` — sudah dalam format token
- Timeout: pakai `ollama_timeout` dari settings (default 60s, lebih pendek dari Gemini 300s)
- **Tidak ada** `response_mime_type="application/json"` — Ollama output plain text
- **Tidak ada** usage metadata (prompt_tokens, completion_tokens) — opsional

### 3.5 GenerateService — Refactor

```python
class GenerateService:
    def __init__(
        self,
        gemini_provider: BaseGeneratorProvider,
        ollama_provider: BaseGeneratorProvider,
        session_mgr, rag_pipeline, prompt_builder, post_processor,
        cache, cost_ctrl, style_manager,
    ):
        self.providers = {
            "gemini": gemini_provider,
            "ollama": ollama_provider,
        }
    
    async def generate_tor(
        self, session_id, mode="standard",
        generator: str = "auto",  # "auto" | "gemini" | "ollama"
        data_override=None, force_regenerate=False,
    ) -> GenerateResult:
        # 1. Tentukan provider berdasarkan generator mode
        # 2. Panggil provider.generate() atau provider.generate_stream()
        # 3. Post-process
        # 4. Cache & persist
```

### 3.6 DecisionEngine — Update Routing

Saat `READY_TO_GENERATE`:

```
1. Cek preferensi user (dari HybridOptions.generator)
2. Jika "auto":
     - completeness >= 0.8 → Ollama (local)
     - completeness < 0.8 → Gemini (escalation)
3. Jika "ollama":
     - Coba Ollama dulu
     - Gagal → fallback Gemini
4. Jika "gemini":
     - Coba Gemini dulu
     - Gagal → fallback Ollama
5. Jika semua gagal → return error
```

### 3.7 Frontend — Generator Selector

User bisa memilih generator di **Settings** atau **Model Selector**:

```
Generator Mode:
  ○ Auto (sistem memilih terbaik)
  ○ Local (Ollama) — offline, gratis
  ○ Gemini (Cloud) — kualitas lebih tinggi
```

**Rules:**
- Default: "Auto"
- Pilihan disimpan di `model-store` atau `ui-store`
- Dikirim ke backend via `HybridOptions.generator`
- Frontend menampilkan badge "Local" atau "Gemini" pada hasil generate

### 3.8 Error Handling & Fallback Chain

```
Generate TOR → Provider A gagal?
  ├── Ya → Coba Provider B
  │       ├── Berhasil → return result
  │       └── Gagal → return error "Semua provider tidak tersedia"
  └── Tidak → return result

Error yang di-handle:
  - Ollama: OllamaConnectionError, OllamaTimeoutError
  - Gemini: GeminiAPIError, GeminiTimeoutError, RateLimitError
  - Keduanya: timeout, connection refused, model not found
```

---

## 4. File Changes

### 4.1 Backend — New Files

| File | Description |
|------|-------------|
| `app/ai/base_generator.py` | Abstract `BaseGeneratorProvider` class |
| `app/ai/ollama_generator_provider.py` | `OllamaGeneratorProvider` — generate TOR via Ollama |
| `app/ai/gemini_generator_provider.py` | Refactored `GeminiProvider` → implement `BaseGeneratorProvider` |
| `app/core/ollama_prompt_builder.py` | `OllamaPromptBuilder` — prompt builder untuk Ollama TOR |
| `app/ai/prompts/ollama_generate_tor.py` | Prompt template untuk Ollama generate TOR |
| `app/ai/prompts/ollama_escalation.py` | Prompt template untuk Ollama escalation mode |

### 4.2 Backend — Modified Files

| File | Changes |
|------|---------|
| `app/ai/gemini_provider.py` | Refactor implement `BaseGeneratorProvider`, tambah `generate_stream()` sudah ada |
| `app/services/generate_service.py` | Terima multiple provider, routing logic "auto" \| "gemini" \| "ollama" |
| `app/core/decision_engine.py` | Update `route()` untuk passing `generator` mode, fallback logic |
| `app/core/gemini_prompt_builder.py` | Tetap ada, tapi jadi salah satu implementasi |
| `app/models/api.py` | Tambah field `generator` di `HybridOptions` |
| `app/models/routing.py` | Tambah field `generator` di `HybridOptions` |
| `app/models/generate.py` | Tambah field `generator` di metadata |
| `app/config.py` | Mungkin tambah `ollama_tor_model` (opsional, bisa beda model untuk generate) |
| `app/main.py` | Init `OllamaGeneratorProvider`, register ke `GenerateService` |

### 4.3 Frontend — Modified Files

| File | Changes |
|------|---------|
| `src/types/api.ts` | Tambah `generator` di `HybridRequest.options` |
| `src/stores/model-store.ts` | Tambah `generatorMode: "auto" \| "local" \| "gemini"` |
| `src/stores/generate-store.ts` | Kirim `generator` mode ke backend |
| `src/stores/chat-store.ts` | Kirim `generator` mode via `HybridRequest` |
| `src/components/settings/` | Tambah dropdown/radio untuk generator mode |
| `src/components/generate/StreamingResult.tsx` | Tampilkan badge "Local" / "Gemini" |

---

## 5. Data Flow

### 5.1 Flow: Auto Mode (Ollama untuk TOR sederhana)

```
User chat → DecisionEngine.route()
  → ChatService.process_message() → Ollama
  → Status: READY_TO_GENERATE (completeness=0.85)
  → DecisionEngine:
      1. generator = "auto"
      2. completeness >= 0.8 → pilih Ollama
      3. Panggil GenerateService.generate_tor(generator="ollama")
  → GenerateService:
      1. Build prompt via OllamaPromptBuilder
      2. Panggil OllamaGeneratorProvider.generate_stream()
      3. Stream token ke frontend via SSE
      4. Post-process
      5. Cache & persist
  → TOR selesai (fully local, zero cost)
```

### 5.2 Flow: Auto Mode (Gemini untuk TOR kompleks)

```
User chat → DecisionEngine.route()
  → ChatService.process_message() → Ollama
  → Status: READY_TO_GENERATE (completeness=0.45)
  → DecisionEngine:
      1. generator = "auto"
      2. completeness < 0.8 → pilih Gemini (escalation)
      3. Panggil GenerateService.generate_tor(generator="gemini", mode="escalation")
  → GenerateService:
      1. Build prompt via GeminiPromptBuilder (escalation)
      2. Panggil GeminiGeneratorProvider.generate_stream()
      3. Stream token ke frontend via SSE
      4. Post-process
      5. Cache & persist
  → TOR selesai (kualitas tinggi, kena biaya Gemini)
```

### 5.3 Flow: Fallback Chain

```
User pilih generator="ollama"
  → GenerateService.generate_tor(generator="ollama")
  → OllamaGeneratorProvider.generate_stream()
  → ERROR: OllamaConnectionError (Ollama tidak jalan)
  → GenerateService:
      1. Log error
      2. Cek apakah Gemini tersedia (API key ada?)
      3. Jika ya → fallback ke GeminiGeneratorProvider
      4. Jika tidak → return error "Ollama offline, Gemini tidak dikonfigurasi"
  → Frontend tampilkan error + opsi "Coba lagi" atau "Ubah ke Gemini"
```

---

## 6. Prompt Design untuk Ollama

### 6.1 Karakteristik Ollama vs Gemini

| Aspek | Gemini | Ollama (qwen2.5, llama3, dll) |
|-------|--------|-------------------------------|
| Format output | Bisa `response_mime_type="application/json"` | Plain text, instruksi format di prompt |
| Context window | 1M tokens (gemini 2.0) | 4096-128K tergantung model |
| Kecepatan | Network latency + processing | Local, lebih cepat untuk teks pendek |
| Kualitas TOR | Sangat baik, struktur rapi | Cukup baik, perlu prompt lebih eksplisit |
| Biaya | Per token | Gratis (listrik + hardware) |

### 6.2 Strategi Prompt Ollama

Ollama butuh prompt yang **lebih eksplisit** dan **lebih terstruktur**:

1. **Instruksi format di awal** — "Kamu akan menghasilkan dokumen TOR dalam format Markdown"
2. **Contoh output** — Berikan template/skeleton yang harus diikuti
3. **Batasan jelas** — "Jangan tambahkan penjelasan di luar dokumen TOR"
4. **Step-by-step** — "Ikuti langkah-langkah ini: 1) Buat judul, 2) Buat latar belakang..."
5. **Format JSON tidak bisa** — Ollama output plain text, kita parse sections dari Markdown

### 6.3 OllamaPromptBuilder

```python
class OllamaPromptBuilder:
    """Build prompt untuk Ollama TOR generation — format chat messages."""

    @staticmethod
    def build_standard_messages(
        data: TORData,
        rag_examples: str | None = None,
        format_spec: str | None = None,
    ) -> list[dict]:
        """Build list of chat messages untuk Ollama standard generate."""
        return [
            {"role": "system", "content": OLLAMA_TOR_SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(data, rag_examples, format_spec)},
        ]

    @staticmethod
    def build_escalation_messages(
        chat_history: list[ChatMessage],
        partial_data: TORData | None = None,
        rag_examples: str | None = None,
        format_spec: str | None = None,
    ) -> list[dict]:
        """Build messages untuk Ollama escalation generate."""
        ...
```

---

## 7. Daftar Tugas (Task Breakdown)

| Kode | Task File | Layer | Deskripsi | Est. |
|------|-----------|-------|-----------|------|
| **T01** | `task01-base-generator-provider.md` | Backend | Abstract `BaseGeneratorProvider` + refactor `GeminiProvider` | 1 jam |
| **T02** | `task02-ollama-generator-provider.md` | Backend | `OllamaGeneratorProvider` — implement `BaseGeneratorProvider` | 2 jam |
| **T03** | `task03-ollama-prompt-builder.md` | Backend | `OllamaPromptBuilder` + prompt templates | 1.5 jam |
| **T04** | `task04-refactor-generate-service.md` | Backend | Update `GenerateService` untuk multi-provider + routing | 2 jam |
| **T05** | `task05-update-decision-engine.md` | Backend | Update `DecisionEngine.route()` untuk generator mode + fallback | 1.5 jam |
| **T06** | `task06-api-models-config.md` | Backend | Tambah field `generator` di models + config | 30 min |
| **T07** | `task07-frontend-generator-mode.md` | Frontend | Tambah generator mode di model-store + api types | 1 jam |
| **T08** | `task08-frontend-generator-selector.md` | Frontend | UI selector generator mode di Settings | 1 jam |
| **T09** | `task09-frontend-generator-badge.md` | Frontend | Badge "Local" / "Gemini" di StreamingResult | 30 min |
| **T10** | `task10-testing.md` | Testing | Unit test + integration test untuk Ollama generator | 2 jam |

**Total estimasi: ~13 jam**

---

## 8. Keputusan Final (Hasil Review User)

| # | Pertanyaan | Keputusan |
|---|-----------|-----------|
| 1 | Model Ollama untuk generate | **Model terpisah** — tambah config `ollama_tor_model` |
| 2 | Threshold auto mode | **0.8** (default) — bisa dijadikan config |
| 3 | UI Generator Selector | **Settings + Chat area** — dropdown cepat di dekat input chat |
| 4 | Streaming support | **Ya, wajib** — konsisten dengan Gemini |
