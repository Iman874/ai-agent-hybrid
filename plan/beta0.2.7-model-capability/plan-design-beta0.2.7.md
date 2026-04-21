# Beta 0.2.7 — Model Capability System

## Latar Belakang

Saat ini sistem model sangat sederhana — hanya mengembalikan `id`, `type`, `provider`, `status`. Tidak ada informasi tentang **kemampuan** masing-masing model. Akibatnya:

| # | Problem | Dampak |
|---|---------|--------|
| 1 | Frontend tidak tahu model mana yang support image input | Tidak bisa menampilkan/sembunyikan tombol upload gambar |
| 2 | Tidak ada validasi backend untuk image vs text-only | Jika user kirim gambar ke model text-only → crash/error tidak jelas |
| 3 | Semua model ditampilkan sama di UI | User tidak tahu kapabilitas model yang dipilih |
| 4 | Tidak ada metadata streaming support per model | Asumsi semua model bisa streaming, padahal belum tentu |

### Kondisi Saat Ini

**Backend** (`GET /models`):  
```json
{
  "models": [
    {"id": "qwen2.5:7b-instruct", "type": "local", "provider": "ollama", "status": "available"},
    {"id": "gemini-2.0-flash", "type": "gemini", "provider": "google", "status": "available"}
  ]
}
```

**Frontend** (`ModelInfo`):
```typescript
interface ModelInfo {
  id: string;
  type: "local" | "gemini";
  provider: string;
  status: "available" | "offline";
}
```

**Tidak ada**: capability, image support, streaming support.

---

## Keputusan Arsitektur (FINAL — TIDAK BOLEH DIUBAH)

### 1. Backend = Source of Truth

```
Backend MENENTUKAN kemampuan model.
Frontend TIDAK menebak.
Frontend BERTANYA ke backend capabilities → UI adaptif.
```

- Saat `GET /models`, backend return `capabilities` per model
- Frontend **TIDAK BOLEH** hardcode kemampuan berdasarkan nama model
- Semua logic penentuan kapabilitas ada di backend

### 2. Capability Schema

```python
class ModelCapability:
    supports_text: bool          # Chat teks biasa
    supports_image_input: bool   # Input gambar (vision model)
    supports_streaming: bool     # Streaming response
```

**Rules:**
- Gemini: `supports_image_input = True` (hampir semua model Gemini support vision)
- Ollama: **dinamis** — bergantung pada model yang aktif:
  - Model vision (llava, bakllava, moondream, etc): `supports_image_input = True`
  - Model text-only (qwen, llama, mistral, etc): `supports_image_input = False`
  - Unknown model: **`supports_image_input = False`** (fail-safe)

### 3. Model Capability Resolver

```
1. Baca nama/tag model
2. Cocokkan ke daftar known vision models
3. Jika cocok → supports_image_input = True
4. Jika tidak cocok → supports_image_input = False (fail-safe)
5. Nanti bisa ditingkatkan ke probing otomatis
```

**Known vision models** (initial list):
```python
KNOWN_VISION_MODELS = [
    "llava", "bakllava", "moondream", "cogvlm",
    "llama3.2-vision", "minicpm-v", "internvl",
]
```

### 4. UI Adaptif

```
Jika supports_image_input = True:
  → Tampilkan tombol upload gambar di ChatInput
  → User bisa kirim gambar + teks

Jika supports_image_input = False:
  → Sembunyikan tombol upload gambar
  → ATAU tampilkan disabled + tooltip "Model ini belum mendukung input gambar"
```

### 5. Backend Validasi Tetap Berlaku

```
Walau UI sudah filter, endpoint tetap validasi:
  - Ada file gambar tapi model text-only → return error terstruktur
  - Error: {"detail": "Model ini tidak mendukung input gambar", "code": "image_not_supported"}
```

Ini aman dari edge case (direct API call, outdated UI cache, etc).

### 6. Frontend Strategy

```
Saat user pilih model:
  1. setActiveModel(id, type)
  2. capabilities = models.find(m => m.id === id).capabilities
  3. UI update: show/hide upload button berdasarkan capabilities
  4. Store capabilities di model-store untuk akses global
```

---

## Proposed Changes

### Backend

---

#### [NEW] [capability_resolver.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/core/capability_resolver.py)

Model capability resolver — menentukan kemampuan model berdasarkan nama/provider.

```python
class ModelCapabilityResolver:
    KNOWN_VISION_MODELS = ["llava", "bakllava", "moondream", "cogvlm", ...]
    
    def resolve(self, model_id: str, provider: str) -> ModelCapabilities:
        """Resolve capabilities berdasarkan model id dan provider."""
```

- Gemini → hardcode `supports_image_input = True`
- Ollama → pattern match nama model terhadap `KNOWN_VISION_MODELS`
- Unknown → fail-safe `supports_image_input = False`

#### [MODIFY] [models.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/api/routes/models.py)

- Tambah `capabilities` di response `GET /models`
- Gunakan `ModelCapabilityResolver` untuk mendapatkan kapabilitas tiap model
- Response baru:
  ```json
  {
    "models": [
      {
        "id": "qwen2.5:7b-instruct",
        "type": "local",
        "provider": "ollama",
        "status": "available",
        "capabilities": {
          "supports_text": true,
          "supports_image_input": false,
          "supports_streaming": true
        }
      }
    ]
  }
  ```

#### [MODIFY] Pydantic Models

- Tambah `ModelCapabilities` di `app/models/api.py`
- Tambah field `capabilities` di response model

#### [MODIFY] [hybrid.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/api/routes/hybrid.py)

- Tambah validasi: jika request mengandung `images` tapi model text-only → return error terstruktur
- Extend `HybridRequest` untuk support field `images: list[ImageAttachment] | None`

#### [MODIFY] [ollama_provider.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/ai/ollama_provider.py)

- Update `chat()` dan `chat_stream()` untuk support message format multimodal:
  ```python
  # Ollama vision format:
  {"role": "user", "content": "Apa isi gambar ini?", "images": ["base64..."]}
  ```
- Jika ada images di message → sertakan dalam payload ke Ollama API

#### [MODIFY] [gemini_chat_provider.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/ai/gemini_chat_provider.py)

- Update `_convert_messages()` untuk handle image parts:
  ```python
  # Gemini multimodal format:
  {"role": "user", "parts": ["text prompt", Image.from_bytes(base64_data)]}
  ```
- Tambah logic decode base64 → PIL Image untuk Gemini SDK

#### [MODIFY] [chat_service.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/services/chat_service.py)

- Update `process_message()` dan `process_message_stream()` untuk menerima parameter `images`
- Teruskan images ke provider saat build messages

---

### Frontend — Chat UI untuk Image Upload

---

#### [MODIFY] [ChatInput.tsx](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/components/chat/ChatInput.tsx)

Perubahan utama — tambah fitur upload gambar:

**Layout baru ChatInput:**
```
┌─────────────────────────────────────────────────────┐
│ [Preview Strip: gambar1.jpg ✕ | gambar2.png ✕]     │  ← hanya muncul jika ada gambar
├─────────────────────────────────────────────────────┤
│ [📎] Ketik pesan...                          [Send] │
│      ↑ tombol attachment (hanya jika vision model)  │
└─────────────────────────────────────────────────────┘
```

- **Tombol attachment** (ikon `ImagePlus` atau `Paperclip`):
  - Hanya muncul jika `activeCapabilities.supports_image_input === true`
  - Klik → buka file picker (`accept="image/*"`)
  - Bisa multiple files (max 3-4 gambar per pesan)
- **Preview strip** di atas textarea:
  - Thumbnail kecil gambar yang sudah dipilih
  - Tombol `✕` per gambar untuk hapus
  - Muncul hanya jika ada gambar dalam antrian
- **State lokal baru**:
  ```typescript
  const [images, setImages] = useState<File[]>([]);
  ```
- **handleSend()** update:
  - Convert `File[]` → `base64[]`
  - Kirim ke `sendMessage(text, sessionId, base64Images)`

#### [NEW] [ImagePreviewStrip.tsx](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/components/chat/ImagePreviewStrip.tsx)

Komponen thumbnail strip di atas input:

```
┌──────┐ ┌──────┐ ┌──────┐
│ img1 │ │ img2 │ │ img3 │
│  ✕   │ │  ✕   │ │  ✕   │
└──────┘ └──────┘ └──────┘
```

- Props: `images: File[]`, `onRemove: (index) => void`
- Render thumbnail via `URL.createObjectURL(file)`
- Ukuran kecil (48x48 atau 56x56) dengan rounded corners
- Tombol close di corner atas kanan

#### [MODIFY] [MessageBubble.tsx](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/components/chat/MessageBubble.tsx)

- Render gambar di dalam bubble jika pesan mengandung images:
  ```
  ┌───────────────────────────┐
  │ [gambar thumbnail]        │
  │ Apa isi gambar ini?       │  ← teks user + gambar
  └───────────────────────────┘
  
  ┌───────────────────────────┐
  │ Gambar ini menunjukkan... │  ← respons AI
  └───────────────────────────┘
  ```
- Gambar di-render sebagai `<img>` rounded dengan max-width
- Klik gambar → bisa preview full size (opsional, bisa di versi selanjutnya)

#### [MODIFY] [chat.ts (types)](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/types/chat.ts)

Extend `Message` untuk support images:
```typescript
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  status: MessageStatus;
  errorMessage?: string;
  thinkingContent?: string;
  images?: string[];  // NEW — base64 encoded images
}
```

#### [MODIFY] [api.ts (types)](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/types/api.ts)

Extend types:
```typescript
export interface ModelCapabilities {
  supports_text: boolean;
  supports_image_input: boolean;
  supports_streaming: boolean;
}

export interface ModelInfo {
  id: string;
  type: "local" | "gemini";
  provider: string;
  status: "available" | "offline";
  capabilities: ModelCapabilities;  // NEW
}

export interface HybridRequest {
  session_id: string | null;
  message: string;
  images?: string[];  // NEW — base64 encoded
  options?: { ... };
}
```

#### [MODIFY] [model-store.ts](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/stores/model-store.ts)

- Tambah `activeCapabilities` computed dari model aktif:
```typescript
interface ModelStore {
  // ... existing ...
  activeCapabilities: ModelCapabilities | null;
}
```

#### [MODIFY] [chat-store.ts](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/stores/chat-store.ts)

- Update `sendMessage()` signature: tambah parameter `images?: string[]`
- Simpan images di user message object
- Teruskan images ke `sendMessageStream()` / `apiSendMessage()`

#### [MODIFY] [ModelSelector.tsx](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/components/shared/ModelSelector.tsx)

- Tambah badge/icon kecil per model:
  - 👁 untuk vision model
  - 📝 untuk text-only
- Tooltip: "Mendukung input gambar" / "Text only"

---

## Task Breakdown

| Task | Judul | Scope |
|------|-------|-------|
| **1** | Backend: `ModelCapabilityResolver` | `capability_resolver.py` — known vision models + resolve logic |
| **2** | Backend: Extend `GET /models` + Pydantic | `models.py`, `api.py` — capabilities field di response |
| **3** | Backend: Multimodal provider support | `ollama_provider.py`, `gemini_chat_provider.py` — images di chat messages |
| **4** | Backend: Validasi + ChatService images | `hybrid.py`, `chat_service.py` — validasi + teruskan images ke provider |
| **5** | Frontend: Type + Store capabilities | `api.ts`, `chat.ts`, `model-store.ts`, `chat-store.ts` |
| **6** | Frontend: ChatInput image upload UI | `ChatInput.tsx`, `ImagePreviewStrip.tsx` — upload, preview, base64 encode |
| **7** | Frontend: MessageBubble image rendering | `MessageBubble.tsx` — render gambar di bubble user |
| **8** | Frontend: ModelSelector capability badges | `ModelSelector.tsx` — vision/text badge per model |
| **9** | Testing & polish | E2E test, provider switch, edge cases, i18n |

---

## Validation Checklist

Setelah implementasi selesai, SEMUA harus terpenuhi:

- [ ] `GET /models` mengembalikan `capabilities` per model
- [ ] Gemini → `supports_image_input: true`
- [ ] Ollama text-only → `supports_image_input: false`
- [ ] Ollama vision model → `supports_image_input: true`
- [ ] Unknown model → `supports_image_input: false` (fail-safe)
- [ ] Frontend tidak hardcode kemampuan
- [ ] Tombol upload gambar muncul/hilang sesuai capability
- [ ] Preview strip gambar berfungsi (tambah, hapus, kirim)
- [ ] MessageBubble render gambar di bubble user
- [ ] Gambar terkirim ke backend sebagai base64
- [ ] Provider menerima dan proses gambar (Ollama + Gemini)
- [ ] Backend validasi reject gambar ke model text-only
- [ ] ModelSelector menampilkan capability badge
- [ ] TypeScript build clean
- [ ] Tidak ada regresi di fitur chat/generate

---

## Verification Plan

### Automated
- Backend: `curl GET /models` → verifikasi capabilities field
- Frontend: `npm run build` clean

### Manual
- **Switch model**: Pilih Gemini → tombol upload muncul → pilih Ollama text → tombol hilang
- **Upload flow**: Pilih gambar → preview muncul → hapus satu → kirim
- **Image chat (Gemini)**: Upload gambar + teks → AI response relevan dengan gambar
- **Image chat (Ollama vision)**: (jika punya llava) Upload gambar → response vision
- **Message history**: Gambar muncul di bubble user setelah kirim
- **Validation**: Kirim gambar ke model text-only via curl → error `image_not_supported`
- **Badge**: ModelSelector menampilkan ikon vision/text per model
- **Fail-safe**: Model unknown → tombol upload tersembunyi
