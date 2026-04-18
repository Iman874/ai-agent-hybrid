# 📘 Blueprint & Implementation Plan v2.0
# Hybrid AI Agent — TOR Generation System

> **Codename**: `ai-agent-hybrid`
> **Versi Dokumen**: 2.0
> **Tanggal**: 2026-04-18
> **Status**: Draft — Menunggu Review

---

## Daftar Isi

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Goals](#2-problem-statement--goals)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Component Deep Dive](#4-component-deep-dive)
5. [Data Flow & Sequence Diagrams](#5-data-flow--sequence-diagrams)
6. [API Specification](#6-api-specification)
7. [Prompt Engineering](#7-prompt-engineering)
8. [RAG Pipeline Detail](#8-rag-pipeline-detail)
9. [Decision Engine & Routing Logic](#9-decision-engine--routing-logic)
10. [Data Models & Schema](#10-data-models--schema)
11. [Session & Conversation Management](#11-session--conversation-management)
12. [Error Handling & Resilience](#12-error-handling--resilience)
13. [Configuration & Environment](#13-configuration--environment)
14. [Project Structure (Directory Tree)](#14-project-structure-directory-tree)
15. [Phased Implementation Timeline](#15-phased-implementation-timeline)
16. [Cost Optimization Strategy](#16-cost-optimization-strategy)
17. [Verification & Testing Plan](#17-verification--testing-plan)
18. [Future Roadmap](#18-future-roadmap)
19. [Open Questions (User Review Required)](#19-open-questions-user-review-required)

---

## 1. Executive Summary

Sistem ini membangun **AI Agent Hybrid** yang menggabungkan dua "otak":

| Komponen | Peran | Teknologi |
|---|---|---|
| **Otak Kiri** (Local LLM) | Interviewer — menggali kebutuhan user secara iteratif | Ollama (local) |
| **Otak Kanan** (Gemini) | Generator — menyusun dokumen TOR profesional | Google Gemini API |
| **Memori** (RAG) | Referensi — membisikkan contoh & best-practice | Vector DB + Embedding |
| **Decision Engine** | Router — menentukan kapan local LLM cukup, kapan harus eskalasi ke Gemini | Python logic layer |

**Hasil akhir**: User cukup "ngobrol" dengan AI, lalu mendapatkan dokumen TOR (Term of Reference) berkualitas proposal resmi — tanpa harus tahu cara menulis TOR.

---

## 2. Problem Statement & Goals

### 2.1 Masalah

- Membuat TOR membutuhkan keahlian menulis formal yang tidak semua orang miliki.
- Jika langsung dilempar ke LLM tanpa konteks cukup, hasilnya generik dan tidak bisa dipakai.
- Menggunakan Gemini untuk seluruh proses = mahal dan tidak efisien.

### 2.2 Goals

| # | Goal | Measurable Target |
|---|---|---|
| G1 | User bisa membuat TOR hanya lewat percakapan | Dari "ide samar" → dokumen TOR dalam ≤10 turn chat |
| G2 | Dokumen TOR setara kualitas proposal resmi | Struktur lengkap, bahasa formal, detail realistis |
| G3 | Biaya Gemini minimal | Gemini dipanggil maksimal 1-2x per sesi, bukan setiap turn |
| G4 | Sistem bisa belajar dari TOR lama | RAG menyediakan referensi dari dokumen historis |
| G5 | Arsitektur modular & extensible | Bisa ditambah domain lain (proposal, surat, laporan) di masa depan |

---

## 3. System Architecture Overview

### 3.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  Streamlit UI │    │  REST Client │    │  Future: Web │          │
│  │  (Chat UI)    │    │  (Postman)   │    │  Frontend    │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
│         │                   │                   │                   │
└─────────┼───────────────────┼───────────────────┼───────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY LAYER                            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │              FastAPI Application Server                  │       │
│  │                                                         │       │
│  │  POST /api/v1/chat      → Chat Controller               │       │
│  │  POST /api/v1/generate  → Generate Controller            │       │
│  │  POST /api/v1/hybrid    → Hybrid Controller (auto-route) │       │
│  │  GET  /api/v1/session/{id}  → Session State              │       │
│  │  POST /api/v1/rag/ingest    → RAG Document Ingestion     │       │
│  │  GET  /api/v1/health        → Health Check               │       │
│  └──────────────────────┬──────────────────────────────────┘       │
│                         │                                           │
└─────────────────────────┼───────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  DECISION    │ │  SESSION     │ │  RAG             │
│  ENGINE      │ │  MANAGER     │ │  PIPELINE        │
│              │ │              │ │                  │
│ - Parse JSON │ │ - Chat hist  │ │ - Embedding      │
│ - Route      │ │ - State      │ │ - Retrieval      │
│ - Escalate   │ │ - Metadata   │ │ - Context inject │
└──────┬───────┘ └──────┬───────┘ └────────┬─────────┘
       │                │                   │
       ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AI PROVIDER LAYER                            │
│                                                                     │
│  ┌──────────────────────┐    ┌──────────────────────┐              │
│  │   Ollama Client      │    │   Gemini Client      │              │
│  │                      │    │                      │              │
│  │  - Local inference   │    │  - REST API call     │              │
│  │  - Chat completion   │    │  - generateContent   │              │
│  │  - Embedding gen     │    │  - Safety settings   │              │
│  │                      │    │                      │              │
│  │  Model: qwen2.5/     │    │  Model: gemini-2.0-  │              │
│  │  llama3-instruct     │    │  flash / pro         │              │
│  └──────────────────────┘    └──────────────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA / STORAGE LAYER                         │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐         │
│  │  ChromaDB /  │  │  SQLite      │  │  File Storage    │         │
│  │  FAISS       │  │              │  │                  │         │
│  │              │  │  - sessions  │  │  - TOR templates │         │
│  │  - vectors   │  │  - history   │  │  - Generated docs│         │
│  │  - metadata  │  │  - cache     │  │  - Exports (PDF) │         │
│  └──────────────┘  └──────────────┘  └──────────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Prinsip Arsitektur

1. **Separation of Concerns**: Setiap layer punya tanggung jawab tunggal.
2. **Provider Agnostic**: AI Provider layer di-abstraksi — bisa swap Ollama → vLLM, atau Gemini → GPT tanpa ubah logic.
3. **Stateful Conversation**: Session manager menyimpan konteks percakapan agar multi-turn chat berjalan koheren.
4. **RAG-Augmented**: Setiap prompt ke local LLM diperkaya dengan konteks relevan dari vector DB.
5. **Cost-Aware Routing**: Gemini hanya dipanggil saat benar-benar diperlukan.

---

## 4. Component Deep Dive

### 4.1 Chat Controller (`/api/v1/chat`)

**Tanggung jawab**: Menerima pesan user, memperkaya dengan RAG context, mengirim ke local LLM, dan mem-parse respons JSON.

**Flow Internal**:
```
Input (user_message, session_id)
    │
    ├─► SessionManager.get_or_create(session_id)
    │       → Ambil chat history
    │
    ├─► RAGPipeline.retrieve(user_message, top_k=3)
    │       → Ambil konteks relevan dari vector DB
    │
    ├─► PromptBuilder.build_chat_prompt(
    │       system_prompt,
    │       chat_history,
    │       rag_context,
    │       user_message
    │   )
    │
    ├─► OllamaClient.chat(prompt)
    │       → Dapat respons raw dari LLM
    │
    ├─► ResponseParser.extract_json(raw_response)
    │       → Parse status: READY_TO_GENERATE | NEED_MORE_INFO | ESCALATE_TO_GEMINI
    │
    ├─► SessionManager.append(user_msg, assistant_msg, parsed_status)
    │
    └─► Return response to client
```

**Retry Logic**: Jika LLM gagal mengeluarkan JSON valid, retry hingga 2x dengan prompt tambahan "Harap jawab dalam format JSON yang diminta."

---

### 4.2 Generate Controller (`/api/v1/generate`)

**Tanggung jawab**: Menerima data JSON lengkap dari chat phase, mengirim ke Gemini untuk generate TOR final.

**Flow Internal**:
```
Input (session_id, mode: "standard" | "escalation")
    │
    ├─► SessionManager.get(session_id)
    │       → Ambil extracted data JSON (jika standard)
    │       → Ambil full chat history (jika escalation)
    │
    ├─► PromptBuilder.build_gemini_prompt(mode, data)
    │       → Standard: inject structured data JSON
    │       → Escalation: inject full conversation + instruksi asumsi
    │
    ├─► RAGPipeline.retrieve(data.judul, top_k=2)
    │       → Ambil contoh TOR serupa sebagai referensi style
    │
    ├─► GeminiClient.generate(prompt + rag_examples)
    │
    ├─► PostProcessor.format_tor(raw_output)
    │       → Validasi struktur, formatting, numbering
    │
    ├─► Cache.store(session_id, final_tor)
    │
    └─► Return TOR document (Markdown + optional PDF)
```

---

### 4.3 Hybrid Controller (`/api/v1/hybrid`)

**Tanggung jawab**: Single endpoint yang secara otomatis merutekan antara Chat dan Generate berdasarkan state sesi.

**Flow Internal**:
```
Input (user_message, session_id)
    │
    ├─► SessionManager.get_state(session_id)
    │
    ├─► IF state == NEW or NEED_MORE_INFO:
    │       → Forward ke Chat Controller
    │       → Parse response status
    │
    ├─► IF response.status == "READY_TO_GENERATE":
    │       → Auto-trigger Generate Controller (mode: standard)
    │       → Return TOR + chat response
    │
    ├─► IF response.status == "ESCALATE_TO_GEMINI":
    │       → Auto-trigger Generate Controller (mode: escalation)
    │       → Return TOR + explanation
    │
    ├─► IF response.status == "NEED_MORE_INFO":
    │       → Return question to user
    │
    ├─► SMART ESCALATION CHECK:
    │       → IF turn_count > MAX_TURNS (default: 8):
    │           → Force escalation
    │       → IF user_message matches LAZY_PATTERNS:
    │           → ["terserah", "gak tau", "pokoknya buat", "bebas"...]
    │           → Force escalation
    │
    └─► Return response
```

---

### 4.4 RAG Pipeline

**Tanggung jawab**: Mengindeks dokumen referensi dan menyediakan konteks relevan untuk setiap prompt.

**Sub-komponen**:

| Sub-komponen | Detail |
|---|---|
| **Document Loader** | Membaca file dari `data/documents/` (format: `.md`, `.txt`, `.pdf`) |
| **Text Splitter** | Chunking dengan `RecursiveCharacterTextSplitter` (chunk_size=500, overlap=50) |
| **Embedding Model** | Via Ollama: `nomic-embed-text` atau `bge-m3` (multilingual) |
| **Vector Store** | ChromaDB (persistent) atau FAISS (in-memory) |
| **Retriever** | Similarity search, top_k=3, dengan threshold score > 0.7 |
| **Context Formatter** | Format hasil retrieval menjadi blok teks untuk di-inject ke prompt |

**Ingestion Flow**:
```
documents/*.md
    │
    ├─► DocumentLoader.load()
    │       → List[Document] with metadata (filename, type, date)
    │
    ├─► TextSplitter.split(documents)
    │       → List[Chunk] (id, text, metadata)
    │
    ├─► EmbeddingModel.embed(chunks)
    │       → List[Vector]
    │
    └─► VectorStore.upsert(vectors, chunks, metadata)
```

**Retrieval Flow**:
```
user_query
    │
    ├─► EmbeddingModel.embed(query)
    │       → query_vector
    │
    ├─► VectorStore.similarity_search(query_vector, top_k=3)
    │       → List[(chunk, score, metadata)]
    │
    ├─► Filter: score > SIMILARITY_THRESHOLD (0.7)
    │
    └─► ContextFormatter.format(filtered_chunks)
            → formatted_context_string
```

---

### 4.5 Session Manager

**Tanggung jawab**: Mengelola state percakapan per user/sesi.

**Data yang disimpan per session**:
```python
{
    "session_id": "uuid-v4",
    "created_at": "2026-04-18T12:00:00Z",
    "updated_at": "2026-04-18T12:05:00Z",
    "state": "CHATTING",  # CHATTING | READY | ESCALATED | COMPLETED
    "turn_count": 3,
    "chat_history": [
        {"role": "user", "content": "...", "timestamp": "..."},
        {"role": "assistant", "content": "...", "parsed_status": "NEED_MORE_INFO", "timestamp": "..."}
    ],
    "extracted_data": {
        "judul": null,
        "latar_belakang": "...",
        "tujuan": null,
        "ruang_lingkup": null,
        "output": null,
        "timeline": null,
        "estimasi_biaya": null
    },
    "completeness_score": 0.28,  # 2 dari 7 field terisi
    "generated_tor": null,       # diisi setelah generate
    "metadata": {
        "escalation_reason": null,
        "gemini_calls_count": 0,
        "total_tokens_local": 1250,
        "total_tokens_gemini": 0
    }
}
```

**Completeness Score Calculation**:
```python
REQUIRED_FIELDS = ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
OPTIONAL_FIELDS = ["estimasi_biaya"]

score = filled_required / len(REQUIRED_FIELDS)
# 1.0 = semua required terisi → auto READY_TO_GENERATE
# < 0.5 = masih sangat kurang
# Optional fields menambah bonus 0.05 per field
```

---

### 4.6 AI Provider Abstraction

**Interface**:
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[Message], **kwargs) -> LLMResponse:
        """Send chat completion request."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector."""
        pass

class OllamaProvider(BaseLLMProvider):
    """Local LLM via Ollama REST API (localhost:11434)"""
    # model: qwen2.5:7b-instruct / llama3:8b-instruct
    # temperature: 0.3 (low untuk JSON consistency)
    # format: json (Ollama native JSON mode)

class GeminiProvider(BaseLLMProvider):
    """Google Gemini via google-generativeai SDK"""
    # model: gemini-2.0-flash (cost-effective) / gemini-2.0-pro (quality)
    # temperature: 0.7 (natural language generation)
    # safety_settings: configured for professional content
```

---

## 5. Data Flow & Sequence Diagrams

### 5.1 Happy Path: User → Chat → Chat → Generate → TOR

```
User              Hybrid API          Local LLM         RAG           Gemini
 │                    │                   │               │              │
 │ "Saya mau buat    │                   │               │              │
 │  TOR untuk        │                   │               │              │
 │  workshop AI"     │                   │               │              │
 ├───────────────────►│                   │               │              │
 │                    │ retrieve context  │               │              │
 │                    ├───────────────────┼──────────────►│              │
 │                    │◄──────────────────┼───────────────┤              │
 │                    │                   │               │              │
 │                    │ chat(prompt+ctx)  │               │              │
 │                    ├──────────────────►│               │              │
 │                    │◄─────────────────┤               │              │
 │                    │ {NEED_MORE_INFO,  │               │              │
 │                    │  "Berapa hari     │               │              │
 │  ◄─────────────────┤  workshopnya?"}  │               │              │
 │                    │                   │               │              │
 │ "3 hari, budget   │                   │               │              │
 │  50jt, peserta    │                   │               │              │
 │  30 orang"        │                   │               │              │
 ├───────────────────►│                   │               │              │
 │                    │ chat(prompt+ctx)  │               │              │
 │                    ├──────────────────►│               │              │
 │                    │◄─────────────────┤               │              │
 │                    │ {READY_TO_GENERATE│               │              │
 │                    │  data: {...}}     │               │              │
 │                    │                   │               │              │
 │                    │ generate(data)    │               │              │
 │                    ├──────────────────┼───────────────┼─────────────►│
 │                    │◄─────────────────┼───────────────┼──────────────┤
 │                    │                   │               │              │
 │  ◄─────────────────┤ TOR Document     │               │              │
 │                    │ (Markdown)        │               │              │
```

### 5.2 Escalation Path: User Tidak Jelas → Gemini Ambil Alih

```
User              Hybrid API          Local LLM                     Gemini
 │                    │                   │                            │
 │ "buat TOR AI"     │                   │                            │
 ├───────────────────►│                   │                            │
 │                    ├──────────────────►│                            │
 │                    │◄─────────────────┤                            │
 │  ◄─────────────────┤ "Bisa jelaskan   │                            │
 │                    │  lebih detail?"   │                            │
 │                    │                   │                            │
 │ "terserah aja"    │                   │                            │
 ├───────────────────►│                   │                            │
 │                    │                   │                            │
 │                    │ SMART ESCALATION  │                            │
 │                    │ detected: lazy    │                            │
 │                    │ pattern match     │                            │
 │                    │                   │                            │
 │                    │ generate(full_history, mode=escalation)        │
 │                    ├────────────────────────────────────────────────►│
 │                    │◄───────────────────────────────────────────────┤
 │                    │                   │                            │
 │  ◄─────────────────┤ TOR (best-guess) │                            │
 │                    │ + disclaimer      │                            │
```

---

## 6. API Specification

### 6.1 `POST /api/v1/hybrid`

**Deskripsi**: Endpoint utama. Auto-routing antara chat dan generate.

**Request Body**:
```json
{
    "session_id": "string | null",       // null = buat session baru
    "message": "string",                 // pesan dari user
    "options": {                          // opsional
        "force_generate": false,          // paksa generate tanpa validasi
        "language": "id"                  // bahasa output (default: id)
    }
}
```

**Response — Chat Mode** (status `NEED_MORE_INFO`):
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "chat",
    "message": "Baik, saya mengerti Anda ingin membuat TOR untuk workshop AI. Beberapa hal yang perlu saya ketahui:\n1. Berapa lama workshopnya?\n2. Siapa target pesertanya?",
    "state": {
        "status": "NEED_MORE_INFO",
        "turn_count": 1,
        "completeness_score": 0.14,
        "filled_fields": ["judul"],
        "missing_fields": ["latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
    }
}
```

**Response — Generate Mode** (status `READY_TO_GENERATE` atau `ESCALATE`):
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "generate",
    "message": "TOR telah berhasil dibuat berdasarkan informasi yang Anda berikan.",
    "tor_document": {
        "format": "markdown",
        "content": "# Term of Reference\n## Workshop Penerapan AI...",
        "metadata": {
            "generated_by": "gemini-2.0-flash",
            "mode": "standard",
            "word_count": 850,
            "generation_time_ms": 3200
        }
    },
    "state": {
        "status": "COMPLETED",
        "turn_count": 4,
        "completeness_score": 1.0,
        "gemini_calls": 1
    }
}
```

---

### 6.2 `POST /api/v1/chat`

**Deskripsi**: Chat langsung dengan local LLM. Tidak auto-generate.

**Request Body**:
```json
{
    "session_id": "string | null",
    "message": "string"
}
```

**Response**: Sama seperti Response Chat Mode di atas.

---

### 6.3 `POST /api/v1/generate`

**Deskripsi**: Trigger Gemini secara manual.

**Request Body**:
```json
{
    "session_id": "string",
    "mode": "standard | escalation",
    "data_override": { ... }             // opsional: override data dari session
}
```

**Response**: Sama seperti Response Generate Mode di atas.

---

### 6.4 `POST /api/v1/rag/ingest`

**Deskripsi**: Upload dan index dokumen ke vector DB.

**Request**: `multipart/form-data`

| Field | Type | Keterangan |
|---|---|---|
| `files` | File[] | File dokumen (.md, .txt, .pdf) |
| `category` | string | Kategori: `tor_template`, `tor_example`, `guideline` |

**Response**:
```json
{
    "status": "success",
    "ingested": 3,
    "total_chunks": 42,
    "vector_db_size": 156
}
```

---

### 6.5 `GET /api/v1/session/{session_id}`

**Deskripsi**: Retrieve state lengkap sesi.

**Response**: Full session object (lihat Session Manager schema di Section 11).

---

### 6.6 `GET /api/v1/health`

**Deskripsi**: Health check semua dependencies.

**Response**:
```json
{
    "status": "healthy",
    "components": {
        "api": {"status": "up", "version": "0.1.0"},
        "ollama": {"status": "up", "model": "qwen2.5:7b-instruct", "latency_ms": 45},
        "gemini": {"status": "up", "model": "gemini-2.0-flash", "quota_remaining": 1450},
        "vector_db": {"status": "up", "type": "chromadb", "documents": 156},
        "session_db": {"status": "up", "type": "sqlite", "active_sessions": 3}
    }
}
```

---

## 7. Prompt Engineering

### 7.1 System Prompt — Local LLM (Chat + Analisis)

```
Kamu adalah AI asisten profesional yang bertugas membantu menyusun TOR (Term of Reference).

## IDENTITAS
- Nama: TOR Assistant
- Gaya komunikasi: Santai tapi profesional
- Bahasa: Indonesia

## TUGAS UTAMA
1. Menggali kebutuhan user secara bertahap dan natural
2. Mengidentifikasi apakah informasi sudah cukup untuk membuat TOR
3. JANGAN langsung membuat TOR lengkap — tugasmu hanya mengumpulkan informasi
4. Fokus bertanya jika data belum lengkap
5. Gunakan informasi referensi (jika disediakan) untuk memberikan saran konkret

## STRUKTUR TOR YANG HARUS DIPENUHI
Field WAJIB:
- judul: Judul kegiatan
- latar_belakang: Konteks dan alasan kegiatan ini diperlukan
- tujuan: Apa yang ingin dicapai
- ruang_lingkup: Batasan dan cakupan pekerjaan
- output: Deliverable yang diharapkan
- timeline: Jadwal pelaksanaan

Field OPSIONAL:
- estimasi_biaya: Perkiraan anggaran (jika user menyebutkan)

## STRATEGI BERTANYA
- Tanyakan 1-2 hal per turn, jangan bombardir pertanyaan
- Jika user sudah menyebutkan sesuatu, jangan tanya ulang
- Jika user memberikan info parsial, konfirmasi dan lanjutkan ke field berikutnya
- Berikan contoh atau saran jika user tampak bingung

## FORMAT RESPONSE
Kamu WAJIB menjawab dalam format JSON berikut (TANPA markdown code block, pure JSON):

### Jika informasi belum lengkap:
{
    "status": "NEED_MORE_INFO",
    "message": "Pesan natural ke user (pertanyaan/konfirmasi)",
    "extracted_so_far": {
        "judul": "... atau null",
        "latar_belakang": "... atau null",
        "tujuan": "... atau null",
        "ruang_lingkup": "... atau null",
        "output": "... atau null",
        "timeline": "... atau null",
        "estimasi_biaya": "... atau null"
    },
    "missing_fields": ["field1", "field2"],
    "confidence": 0.0 - 1.0
}

### Jika informasi sudah cukup untuk generate TOR:
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
        "estimasi_biaya": "... atau null"
    },
    "confidence": 0.85 - 1.0
}

### Jika user tidak kooperatif / terlalu ambigu:
{
    "status": "ESCALATE_TO_GEMINI",
    "message": "Pesan ke user bahwa akan dibuatkan versi draft",
    "reason": "Alasan eskalasi",
    "partial_data": { ... },
    "confidence": 0.0 - 0.3
}
```

### 7.2 System Prompt — Gemini (Final TOR Generation, Standard Mode)

```
Kamu adalah AI profesional pembuat dokumen TOR (Term of Reference).

## INSTRUKSI
Buat dokumen TOR yang:
- Formal, jelas, dan siap digunakan dalam proposal resmi
- Menggunakan bahasa Indonesia baku
- Memiliki detail yang realistis dan kontekstual
- Tidak generik — harus spesifik sesuai data yang diberikan

## STRUKTUR DOKUMEN OUTPUT

# TERM OF REFERENCE (TOR)
# [Judul Kegiatan]

## 1. Latar Belakang
[2-3 paragraf, jelaskan konteks, urgensi, dan relevansi kegiatan]

## 2. Tujuan
### 2.1 Tujuan Umum
[1 paragraf]
### 2.2 Tujuan Khusus
[Bullet points, 3-5 item]

## 3. Ruang Lingkup Pekerjaan
[Bullet points dengan penjelasan per item]

## 4. Output / Deliverable
[Tabel: No | Output | Keterangan | Deadline]

## 5. Timeline Pelaksanaan
[Tabel Gantt sederhana atau list fase dengan durasi]

## 6. Estimasi Biaya (jika data tersedia)
[Tabel: No | Komponen | Volume | Satuan | Total]

## 7. Penutup
[1 paragraf penutup formal]

## ATURAN PENULISAN
- Gunakan paragraf yang rapi, bukan kalimat pendek
- Jika data kurang detail, perkaya dengan asumsi yang masuk akal (tandai dengan catatan)
- Gunakan numbering yang konsisten
- Tambahkan konteks industri/domain yang relevan
- Minimal 500 kata untuk TOR yang berkualitas

## DATA INPUT
{DATA_JSON}

## REFERENSI STYLE (dari RAG, jika ada)
{RAG_EXAMPLES}
```

### 7.3 System Prompt — Gemini (Escalation Mode)

```
Kamu adalah AI profesional pembuat dokumen TOR (Term of Reference).

## SITUASI
User ingin membuat TOR tetapi TIDAK memberikan informasi yang cukup meskipun sudah ditanya berulang kali. Kamu harus membuat TOR terbaik yang mungkin berdasarkan informasi minimal yang ada.

## PERCAKAPAN SEBELUMNYA
{FULL_CHAT_HISTORY}

## INSTRUKSI
1. Analisis percakapan di atas untuk mengekstrak setiap potongan informasi yang tersedia
2. Gunakan asumsi TERBAIK dan PALING REALISTIS untuk melengkapi kekurangan data
3. Tandai setiap asumsi dengan [ASUMSI] agar user bisa mengedit
4. Buat TOR yang tetap profesional dan tidak terlalu generik
5. Tambahkan catatan di akhir: "Bagian yang ditandai [ASUMSI] dapat disesuaikan sesuai kebutuhan Anda."

## FORMAT OUTPUT
Sama seperti format TOR standard (lihat struktur di atas).
```

### 7.4 RAG Context Injection Template

Ditambahkan ke prompt local LLM sebelum user message:

```
## REFERENSI (Gunakan sebagai inspirasi jika relevan, abaikan jika tidak)

Berikut adalah contoh/template TOR yang mungkin relevan dengan kebutuhan user:

---
[Referensi 1: {chunk.metadata.source}]
{chunk.text}
---
[Referensi 2: {chunk.metadata.source}]
{chunk.text}
---

Catatan: Referensi di atas hanya sebagai panduan style dan detail. Sesuaikan dengan kebutuhan spesifik user.
```

---

## 8. RAG Pipeline Detail

### 8.1 Document Preparation

**Lokasi**: `data/documents/`

**Struktur folder**:
```
data/
└── documents/
    ├── templates/          # Template TOR kosong
    │   ├── template_workshop.md
    │   ├── template_procurement.md
    │   └── template_research.md
    ├── examples/           # Contoh TOR yang sudah jadi
    │   ├── tor_workshop_ai_2025.md
    │   ├── tor_pengadaan_server.md
    │   └── tor_penelitian_nlp.md
    └── guidelines/         # Panduan penulisan TOR
        ├── guideline_format_instansi.md
        └── guideline_bahasa_formal.md
```

### 8.2 Chunking Strategy

```python
CHUNK_CONFIG = {
    "chunk_size": 500,          # karakter per chunk
    "chunk_overlap": 50,        # overlap antar chunk
    "separators": ["\n## ", "\n### ", "\n\n", "\n", ". "],  # prioritas split
    "metadata_fields": ["source", "category", "date_created"]
}
```

**Kenapa 500 karakter?**
- Cukup panjang untuk menyimpan konteks satu section TOR
- Cukup pendek agar retrieval tidak terlalu noisy
- Overlap 50 memastikan tidak ada informasi yang terpotong di boundary

### 8.3 Embedding Model Options

| Model | Dimensi | Bahasa | Kecepatan | Rekomendasi |
|---|---|---|---|---|
| `nomic-embed-text` | 768 | EN-centric | Cepat | ✅ Jika TOR dominan English |
| `bge-m3` | 1024 | Multilingual | Sedang | ✅✅ **Rekomendasi** (support ID) |
| `snowflake-arctic-embed` | 1024 | Multilingual | Sedang | Alternatif |

### 8.4 Vector DB Comparison

| Fitur | FAISS | ChromaDB |
|---|---|---|
| Persistence | ❌ In-memory (manual save/load) | ✅ Auto-persist ke disk |
| Setup complexity | Rendah | Rendah |
| Metadata filtering | ❌ Manual | ✅ Built-in |
| API | Low-level numpy | High-level Python |
| Skalabilitas | Baik (jutaan vektor) | Cukup (ratusan ribu) |
| **Rekomendasi** | Untuk produksi besar | **✅ Untuk proyek ini** |

---

## 9. Decision Engine & Routing Logic

### 9.1 State Machine

```
                  ┌───────────────────────────┐
                  │        NEW_SESSION        │
                  └─────────────┬─────────────┘
                                │ user sends first message
                                ▼
                  ┌───────────────────────────┐
             ┌───►│        CHATTING           │◄────┐
             │    └─────────────┬─────────────┘     │
             │                  │                    │
             │    ┌─────────────┼─────────────┐     │
             │    ▼             ▼             ▼     │
        ┌─────────┐    ┌──────────────┐  ┌────────┐│
        │  NEED   │    │   READY_TO   │  │ESCALATE││
        │  MORE   │    │   GENERATE   │  │   TO   ││
        │  INFO   │    │              │  │ GEMINI ││
        └────┬────┘    └──────┬───────┘  └───┬────┘│
             │                │              │      │
             └────────────────┤              │      │
            (user replies)    │              │      │
                              ▼              ▼      │
                  ┌───────────────────────────┐     │
                  │      GENERATING           │     │
                  │   (Gemini processing)     │     │
                  └─────────────┬─────────────┘     │
                                │                    │
                                ▼                    │
                  ┌───────────────────────────┐     │
                  │       COMPLETED           │     │
                  │   (TOR generated)         │─────┘
                  └───────────────────────────┘
                       (user requests revision)
```

### 9.2 Smart Escalation Rules

```python
ESCALATION_RULES = {
    # Rule 1: Terlalu banyak turn tanpa progress
    "max_turns_without_progress": {
        "threshold": 5,  # 5 turn tanpa field baru terisi
        "action": "ESCALATE_TO_GEMINI"
    },

    # Rule 2: Absolute max turns
    "absolute_max_turns": {
        "threshold": 10,
        "action": "ESCALATE_TO_GEMINI"
    },

    # Rule 3: Lazy/ambiguous user patterns
    "lazy_patterns": [
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
    ],

    # Rule 4: Ultra-short input setelah ditanya detail
    "short_input_after_question": {
        "max_chars": 15,
        "consecutive_count": 2,  # 2x berturut-turut jawab pendek
        "action": "ESCALATE_TO_GEMINI"
    },

    # Rule 5: Completeness score stagnant
    "stagnant_score": {
        "no_increase_for_turns": 3,
        "action": "ESCALATE_TO_GEMINI"
    }
}
```

### 9.3 Routing Decision Pseudocode

```python
async def route_message(session: Session, message: str) -> Response:
    # Step 1: Check smart escalation triggers
    if should_force_escalate(session, message):
        return await generate_tor(session, mode="escalation")

    # Step 2: Chat with local LLM
    chat_response = await chat_with_local_llm(session, message)

    # Step 3: Parse and route
    parsed = parse_llm_response(chat_response)

    match parsed.status:
        case "READY_TO_GENERATE":
            session.extracted_data = parsed.data
            tor = await generate_tor(session, mode="standard")
            return HybridResponse(type="generate", tor=tor, chat=parsed.message)

        case "ESCALATE_TO_GEMINI":
            tor = await generate_tor(session, mode="escalation")
            return HybridResponse(type="generate", tor=tor, chat=parsed.message)

        case "NEED_MORE_INFO":
            session.update_extracted(parsed.extracted_so_far)
            return HybridResponse(type="chat", message=parsed.message)

        case _:
            # Fallback: treat as NEED_MORE_INFO
            return HybridResponse(type="chat", message=chat_response.raw)
```

---

## 10. Data Models & Schema

### 10.1 Pydantic Models (FastAPI)

```python
# === Request Models ===

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(..., min_length=1, max_length=5000)

class HybridRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(..., min_length=1, max_length=5000)
    options: HybridOptions | None = None

class HybridOptions(BaseModel):
    force_generate: bool = False
    language: str = "id"

class GenerateRequest(BaseModel):
    session_id: str
    mode: Literal["standard", "escalation"] = "standard"
    data_override: TORData | None = None

# === Data Models ===

class TORData(BaseModel):
    judul: str | None = None
    latar_belakang: str | None = None
    tujuan: str | None = None
    ruang_lingkup: str | None = None
    output: str | None = None
    timeline: str | None = None
    estimasi_biaya: str | None = None

class LLMParsedResponse(BaseModel):
    status: Literal["NEED_MORE_INFO", "READY_TO_GENERATE", "ESCALATE_TO_GEMINI"]
    message: str
    data: TORData | None = None
    extracted_so_far: TORData | None = None
    missing_fields: list[str] | None = None
    reason: str | None = None
    confidence: float = 0.0

# === Response Models ===

class SessionState(BaseModel):
    status: str
    turn_count: int
    completeness_score: float
    filled_fields: list[str]
    missing_fields: list[str]

class TORDocument(BaseModel):
    format: str = "markdown"
    content: str
    metadata: TORMetadata

class TORMetadata(BaseModel):
    generated_by: str
    mode: str
    word_count: int
    generation_time_ms: int

class HybridResponse(BaseModel):
    session_id: str
    type: Literal["chat", "generate"]
    message: str
    tor_document: TORDocument | None = None
    state: SessionState
```

### 10.2 SQLite Schema (Session Storage)

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    state TEXT DEFAULT 'NEW',          -- NEW, CHATTING, READY, ESCALATED, COMPLETED
    turn_count INTEGER DEFAULT 0,
    completeness_score REAL DEFAULT 0.0,
    extracted_data_json TEXT,          -- JSON string of TORData
    generated_tor TEXT,                -- Final TOR markdown
    escalation_reason TEXT,
    gemini_calls_count INTEGER DEFAULT 0,
    total_tokens_local INTEGER DEFAULT 0,
    total_tokens_gemini INTEGER DEFAULT 0
);

CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,                -- 'user' or 'assistant'
    content TEXT NOT NULL,
    parsed_status TEXT,                -- status dari response LLM
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE rag_documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    category TEXT,                     -- tor_template, tor_example, guideline
    chunk_count INTEGER,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tor_cache (
    session_id TEXT PRIMARY KEY,
    tor_content TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_used TEXT,
    mode TEXT,                         -- standard, escalation
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_messages_session ON chat_messages(session_id);
CREATE INDEX idx_sessions_state ON sessions(state);
```

---

## 11. Session & Conversation Management

### 11.1 Session Lifecycle

| Phase | State | Deskripsi | Trigger Transisi |
|---|---|---|---|
| 1 | `NEW` | Session baru dibuat | User mengirim pesan pertama |
| 2 | `CHATTING` | Sedang mengumpulkan info | Setiap turn chat |
| 3 | `READY` | Data cukup, siap generate | LLM return `READY_TO_GENERATE` |
| 4 | `ESCALATED` | User tidak kooperatif | Smart Escalation trigger |
| 5 | `GENERATING` | Gemini sedang memproses | Generate dimulai |
| 6 | `COMPLETED` | TOR sudah jadi | Generate selesai |

### 11.2 Chat History Formatting untuk Prompt

```python
def format_chat_history(messages: list[ChatMessage], max_turns: int = 10) -> str:
    """Format chat history for LLM prompt injection."""
    recent = messages[-max_turns * 2:]  # last N turns (user + assistant)
    formatted = []
    for msg in recent:
        role_label = "User" if msg.role == "user" else "Assistant"
        formatted.append(f"[{role_label}]: {msg.content}")
    return "\n\n".join(formatted)
```

### 11.3 Session Expiry & Cleanup

- Sessions idle > 24 jam → auto-archive
- Sessions COMPLETED > 7 hari → soft delete (data tersimpan tapi tidak muncul di listing)
- Background task cron cleanup setiap 6 jam

---

## 12. Error Handling & Resilience

### 12.1 Error Taxonomy

| Error Code | Kategori | Contoh | Handling |
|---|---|---|---|
| `E001` | LLM Connection | Ollama tidak berjalan | Return friendly error + instruksi start Ollama |
| `E002` | LLM Response Parse | JSON invalid dari LLM | Retry 2x dengan prompt tambahan, fallback ke raw text |
| `E003` | Gemini API | Rate limit / quota habis | Queue request, retry dengan exponential backoff |
| `E004` | Gemini API | API key invalid | Return error, log alert |
| `E005` | RAG | Vector DB tidak accessible | Graceful degradation: lanjut tanpa RAG context |
| `E006` | Session | Session not found | Buat session baru, inform user |
| `E007` | Input | Message terlalu panjang | Return validation error |
| `E008` | Timeout | LLM response timeout (>60s) | Retry 1x, lalu return timeout error |

### 12.2 Retry Strategy

```python
RETRY_CONFIG = {
    "ollama": {
        "max_retries": 2,
        "backoff_seconds": [1, 3],
        "on_json_parse_fail": {
            "retry_with_prompt_suffix": "PENTING: Jawab HANYA dalam format JSON yang diminta. Tidak ada teks lain.",
            "max_retries": 2
        }
    },
    "gemini": {
        "max_retries": 3,
        "backoff_seconds": [2, 5, 10],  # exponential
        "on_rate_limit": {
            "wait_seconds": 60,
            "fallback": "queue"
        }
    },
    "rag": {
        "max_retries": 1,
        "fallback": "continue_without_context"
    }
}
```

### 12.3 Graceful Degradation Table

| Komponen Gagal | Dampak | Fallback |
|---|---|---|
| Ollama down | Chat tidak bisa | Redirect semua ke Gemini (mahal tapi fungsional) |
| Gemini down | Generate tidak bisa | Queue request + notify user "akan diproses nanti" |
| RAG down | Tidak ada referensi | Chat tetap jalan tanpa RAG context |
| SQLite down | Session hilang | In-memory session (tanpa persistence) |

---

## 13. Configuration & Environment

### 13.1 Environment Variables (`.env`)

```bash
# === APP ===
APP_NAME=ai-agent-hybrid
APP_VERSION=0.1.0
APP_PORT=8000
APP_ENV=development             # development | staging | production
LOG_LEVEL=INFO                  # DEBUG | INFO | WARNING | ERROR

# === OLLAMA ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen2.5:7b-instruct
OLLAMA_EMBED_MODEL=bge-m3
OLLAMA_TIMEOUT_SECONDS=60
OLLAMA_TEMPERATURE=0.3
OLLAMA_NUM_CTX=4096             # context window size

# === GEMINI ===
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_OUTPUT_TOKENS=4096
GEMINI_TIMEOUT_SECONDS=120

# === RAG ===
VECTOR_DB_TYPE=chromadb         # chromadb | faiss
VECTOR_DB_PATH=./data/chroma_db
EMBEDDING_MODEL=bge-m3
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RETRIEVAL_TOP_K=3
SIMILARITY_THRESHOLD=0.7

# === SESSION ===
SESSION_DB_PATH=./data/sessions.db
SESSION_EXPIRY_HOURS=24
SESSION_CLEANUP_INTERVAL_HOURS=6

# === COST CONTROL ===
MAX_GEMINI_CALLS_PER_SESSION=3
MAX_GEMINI_CALLS_PER_HOUR=20
MAX_CHAT_TURNS_PER_SESSION=15

# === ESCALATION ===
ESCALATION_MAX_IDLE_TURNS=5
ESCALATION_ABSOLUTE_MAX_TURNS=10
```

### 13.2 Config File (`config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "ai-agent-hybrid"
    app_port: int = 8000

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen2.5:7b-instruct"
    ollama_embed_model: str = "bge-m3"
    ollama_timeout: int = 60
    ollama_temperature: float = 0.3

    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 4096

    vector_db_type: str = "chromadb"
    vector_db_path: str = "./data/chroma_db"
    retrieval_top_k: int = 3
    similarity_threshold: float = 0.7

    max_gemini_calls_per_session: int = 3
    max_gemini_calls_per_hour: int = 20
    max_chat_turns: int = 15

    class Config:
        env_file = ".env"
```

---

## 14. Project Structure (Directory Tree)

```
ai-agent-hybrid/
│
├── plan/                          # 📘 Dokumentasi & rencana
│   └── hybrid_agent_blueprint.md  # Dokumen ini
│
├── app/                           # 🏗️ Source code utama
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Pydantic Settings
│   │
│   ├── api/                       # 🌐 API Layer
│   │   ├── __init__.py
│   │   ├── router.py              # Central router (include semua routes)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── chat.py            # POST /api/v1/chat
│   │       ├── generate.py        # POST /api/v1/generate
│   │       ├── hybrid.py          # POST /api/v1/hybrid
│   │       ├── session.py         # GET  /api/v1/session/{id}
│   │       ├── rag.py             # POST /api/v1/rag/ingest
│   │       └── health.py          # GET  /api/v1/health
│   │
│   ├── core/                      # ⚙️ Core Business Logic
│   │   ├── __init__.py
│   │   ├── decision_engine.py     # Routing & escalation logic
│   │   ├── session_manager.py     # Session CRUD & state machine
│   │   ├── response_parser.py     # Parse LLM JSON responses
│   │   └── post_processor.py      # Format & validate final TOR
│   │
│   ├── ai/                        # 🧠 AI Provider Layer
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract BaseLLMProvider
│   │   ├── ollama_provider.py     # Ollama client implementation
│   │   ├── gemini_provider.py     # Gemini client implementation
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── chat_system.py     # Local LLM system prompt
│   │       ├── generate_tor.py    # Gemini TOR generation prompt
│   │       ├── escalation.py      # Gemini escalation prompt
│   │       └── rag_injection.py   # RAG context template
│   │
│   ├── rag/                       # 📚 RAG Pipeline
│   │   ├── __init__.py
│   │   ├── document_loader.py     # Load .md, .txt, .pdf files
│   │   ├── text_splitter.py       # Chunk documents
│   │   ├── embedder.py            # Generate embeddings via Ollama
│   │   ├── vector_store.py        # ChromaDB / FAISS wrapper
│   │   └── retriever.py           # Similarity search + filtering
│   │
│   ├── models/                    # 📦 Data Models (Pydantic)
│   │   ├── __init__.py
│   │   ├── requests.py            # Request schemas
│   │   ├── responses.py           # Response schemas
│   │   ├── session.py             # Session data model
│   │   └── tor.py                 # TOR data model
│   │
│   ├── db/                        # 💾 Database Layer
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite connection & setup
│   │   ├── migrations/            # Schema migrations
│   │   │   └── 001_initial.sql
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── session_repo.py    # Session CRUD queries
│   │       └── message_repo.py    # Chat message queries
│   │
│   └── utils/                     # 🔧 Utilities
│       ├── __init__.py
│       ├── logger.py              # Structured logging
│       └── validators.py          # Input validation helpers
│
├── data/                          # 📂 Data & Storage
│   ├── documents/                 # RAG source documents
│   │   ├── templates/
│   │   ├── examples/
│   │   └── guidelines/
│   ├── chroma_db/                 # Vector DB storage (auto-created)
│   └── sessions.db                # SQLite database (auto-created)
│
├── tests/                         # 🧪 Test Suite
│   ├── __init__.py
│   ├── conftest.py                # Shared fixtures
│   ├── test_chat.py               # Chat endpoint tests
│   ├── test_generate.py           # Generate endpoint tests
│   ├── test_hybrid.py             # Hybrid routing tests
│   ├── test_decision_engine.py    # Escalation logic tests
│   ├── test_rag.py                # RAG pipeline tests
│   └── test_response_parser.py    # JSON parsing tests
│
├── scripts/                       # 🛠️ Utility Scripts
│   ├── ingest_documents.py        # Batch ingest RAG documents
│   ├── seed_examples.py           # Seed contoh TOR
│   └── benchmark_llm.py          # Benchmark response quality
│
├── .env.example                   # 📝 Env template
├── .gitignore
├── requirements.txt               # 📦 Python dependencies
├── pyproject.toml                 # ⚙️ Project config
├── Dockerfile                     # 🐳 Container build
├── docker-compose.yml             # 🐳 Multi-service orchestration
├── Makefile                       # 🔨 Dev shortcuts
├── LICENSE
└── README.md
```

---

## 15. Phased Implementation Timeline

### Phase 0: Foundation (Hari 1-2)
- [ ] Setup project structure (directory tree di atas)
- [ ] Setup virtual environment + install dependencies
- [ ] Config management (`.env` + `config.py`)
- [ ] FastAPI app skeleton + health endpoint
- [ ] SQLite schema setup + migration script
- [ ] Logger setup
- [ ] Pastikan Ollama berjalan dengan model yang dipilih

### Phase 1: Chat Engine (Hari 3-5)
- [ ] Implement `OllamaProvider` (chat + embed)
- [ ] Implement `PromptBuilder` untuk chat system prompt
- [ ] Implement `ResponseParser` (JSON extraction dari LLM output)
- [ ] Implement `SessionManager` (create, get, update, append message)
- [ ] Implement `POST /api/v1/chat` endpoint
- [ ] Test: Skenario multi-turn chat, validasi JSON output

### Phase 2: RAG Pipeline (Hari 6-8)
- [ ] Implement `DocumentLoader` (markdown + txt reader)
- [ ] Implement `TextSplitter`
- [ ] Implement `Embedder` (via Ollama)
- [ ] Implement `VectorStore` (ChromaDB wrapper)
- [ ] Implement `Retriever` (similarity search)
- [ ] Implement `POST /api/v1/rag/ingest` endpoint
- [ ] Siapkan 3-5 contoh dokumen TOR untuk seed data
- [ ] Test: Ingest → retrieve → verify relevance

### Phase 3: Gemini Integration (Hari 9-10)
- [ ] Implement `GeminiProvider`
- [ ] Implement TOR generation prompt
- [ ] Implement escalation prompt
- [ ] Implement `PostProcessor` (format validation)
- [ ] Implement `POST /api/v1/generate` endpoint
- [ ] Test: Generate TOR dari mock data JSON

### Phase 4: Decision Engine & Hybrid (Hari 11-13)
- [ ] Implement `DecisionEngine` (state machine + escalation rules)
- [ ] Implement smart escalation pattern matching
- [ ] Implement `POST /api/v1/hybrid` endpoint
- [ ] Implement completeness score calculation
- [ ] Test: Full flow — chat → auto-detect ready → generate
- [ ] Test: Escalation scenarios

### Phase 5: Polish & Testing (Hari 14-15)
- [ ] Error handling untuk semua edge cases
- [ ] Rate limiting (Gemini calls)
- [ ] Session cleanup background task
- [ ] Write comprehensive test suite
- [ ] API documentation (auto-generated Swagger via FastAPI)
- [ ] README update

### Phase 6: Frontend (Optional, Hari 16-18)
- [ ] Streamlit chat UI
- [ ] Session selector
- [ ] TOR preview panel (Markdown rendered)
- [ ] RAG document manager UI
- [ ] Export TOR ke PDF

---

## 16. Cost Optimization Strategy

### 16.1 Gemini Call Budget

| Skenario | Gemini Calls | Biaya (est.) |
|---|---|---|
| Happy path (info lengkap) | 1x generate | ~$0.001 (flash) |
| Normal path (3-5 turn chat) | 1x generate | ~$0.001 |
| Escalation path | 1x escalation | ~$0.002 (lebih banyak input) |
| Worst case (revision) | 2x generate | ~$0.003 |

### 16.2 Cost Control Measures

1. **Gemini hanya untuk generate, BUKAN chat** → bulk token saving
2. **Max 3 Gemini calls per session** → hard limit
3. **Global rate limit**: max 20 calls/hour → prevent abuse
4. **Cache TOR results** → jika user request ulang session yang sama, serve dari cache
5. **Use `gemini-2.0-flash`** → 10x lebih murah dari Pro, kualitas masih sangat baik
6. **RAG reduces Gemini input** → Gemini dapat data terstruktur, bukan raw conversation

### 16.3 Token Estimation per Session

| Component | Est. Tokens | Provider |
|---|---|---|
| System prompt (per turn) | ~800 | Local (free) |
| Chat history (avg 5 turns) | ~1500 | Local (free) |
| RAG context (3 chunks) | ~600 | Local (free) |
| User messages total | ~400 | Local (free) |
| **Subtotal Local** | **~3300/session** | **$0** |
| Gemini input (data + prompt) | ~1500 | Gemini |
| Gemini output (TOR) | ~1000 | Gemini |
| **Subtotal Gemini** | **~2500/session** | **~$0.001** |

---

## 17. Verification & Testing Plan

### 17.1 Unit Tests

| Test File | Cakupan |
|---|---|
| `test_response_parser.py` | Parse JSON valid, invalid, mixed text+JSON, missing fields |
| `test_decision_engine.py` | State transitions, escalation rules, lazy pattern detection |
| `test_rag.py` | Chunking, embedding dimension, retrieval accuracy |
| `test_session_manager.py` | CRUD, completeness score, history formatting |

### 17.2 Integration Tests

| Skenario | Deskripsi | Expected |
|---|---|---|
| Happy Path | User jawab lengkap dalam 3 turn | TOR generated, completeness=1.0 |
| Lazy User | User jawab "terserah" di turn ke-2 | Escalation triggered, TOR with [ASUMSI] |
| Ambiguous | User berikan info parsial, lalu diam | Max turn reached, escalation |
| RAG-Boosted | TOR tentang topic yang ada di contoh | RAG context ditemukan, kualitas TOR lebih baik |
| Ollama Down | Ollama mati saat chat | Error E001, pesan informatif |
| Invalid JSON | LLM keluarkan non-JSON | Retry 2x, fallback graceful |

### 17.3 Manual Testing Checklist

- [ ] `curl` test semua endpoint
- [ ] Postman collection untuk API regression
- [ ] Full conversation flow via Streamlit UI (jika diimplementasi)
- [ ] Verifikasi kualitas TOR output oleh manusia (readability, struktur, realism)
- [ ] Load test sederhana: 10 concurrent sessions

### 17.4 Quality Metrics untuk TOR Output

| Metric | Target |
|---|---|
| Struktur lengkap (7 section) | 100% |
| Bahasa formal & konsisten | Subjective review ≥ 4/5 |
| Word count | ≥ 500 kata |
| Tidak generik (ada detail spesifik) | Subjective review ≥ 4/5 |
| Asumsi ditandai dengan jelas (eskalasi mode) | 100% |

---

## 18. Future Roadmap

### v0.2 — Multi-Document Support
- Support output selain TOR: Proposal, Surat Dinas, Laporan Kegiatan
- Template selector di awal percakapan
- Domain-specific RAG collections

### v0.3 — User Feedback Loop
- User bisa edit TOR dan generate ulang bagian tertentu
- Feedback rating disimpan untuk improve prompt
- A/B testing prompt variants

### v0.4 — Multi-User & Auth
- User authentication (JWT)
- Per-user session management
- Usage quota per user

### v1.0 — Production Readiness
- Docker deployment
- Monitoring & alerting (Prometheus + Grafana)
- Gemini fallback ke model lain (GPT-4o, Claude)
- PDF export dengan template instansi
- Admin dashboard untuk RAG management

---

## 19. Open Questions (User Review Required)

Sebelum memulai implementasi, mohon jawab pertanyaan berikut:

> [!IMPORTANT]
> ### Q1. Framework Backend
> Plan ini menggunakan **FastAPI** (async-native, auto-docs Swagger, Pydantic validation).
> Apakah Anda setuju, atau lebih prefer **Flask**?

> [!IMPORTANT]
> ### Q2. Model Lokal di Ollama
> Model yang direkomendasikan: **`qwen2.5:7b-instruct`** (bagus untuk structured JSON output dalam Bahasa Indonesia).
> Alternatif: `llama3:8b-instruct`, `mistral:7b-instruct`.
> Model mana yang sudah Anda install / preferkan?
> Apakah spesifikasi hardware Anda mendukung 7B model? (minimal RAM 8GB, disarankan 16GB).

> [!IMPORTANT]
> ### Q3. Vector Database
> Rekomendasi: **ChromaDB** (persistent, mudah, dan support metadata filtering).
> Apakah Anda setuju, atau prefer FAISS?

> [!NOTE]
> ### Q4. Format Dokumen untuk RAG
> Untuk contoh/template TOR yang akan di-ingest ke vector DB, format apa yang Anda punya?
> - Markdown (`.md`) — paling mudah diproses
> - Plain text (`.txt`)
> - PDF (`.pdf`) — perlu library tambahan `pypdf` / `pdfplumber`
> - Campuran semua?

> [!NOTE]
> ### Q5. Frontend
> Apakah perlu UI chat (**Streamlit**) di Phase 6, atau cukup API-only dulu?
> Streamlit bisa sangat mempercepat demo & testing.

> [!NOTE]
> ### Q6. Deployment Target
> Apakah ini akan berjalan di:
> - **Lokal saja** (laptop/PC Anda) — setup sederhana
> - **Server/VPS** — perlu Docker
> - **Cloud** (GCP/AWS) — perlu infra config

> [!NOTE]
> ### Q7. Bahasa TOR
> Apakah TOR output **selalu Bahasa Indonesia**, atau perlu support Bahasa Inggris juga?

---

## Dependencies (`requirements.txt`)

```
# Framework
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0
pydantic-settings>=2.0

# AI Providers
ollama>=0.4.0                 # Ollama Python client
google-generativeai>=0.8.0    # Gemini SDK

# RAG
chromadb>=0.5.0               # Vector database
langchain-text-splitters>=0.3.0  # Text chunking

# Database
aiosqlite>=0.20.0             # Async SQLite

# Utilities
python-dotenv>=1.0
python-multipart>=0.0.9       # File upload support
httpx>=0.27.0                 # Async HTTP client

# Testing
pytest>=8.0
pytest-asyncio>=0.24.0
httpx                         # For TestClient

# Optional: Frontend
# streamlit>=1.38.0
# Optional: PDF
# pypdf>=4.0
```

---

> **Dokumen ini adalah living document.** Update sesuai dengan jawaban atas Open Questions dan progress implementasi.
