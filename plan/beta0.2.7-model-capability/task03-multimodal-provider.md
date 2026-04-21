# Task 3: Backend — Multimodal Provider Support

## Deskripsi

Update kedua AI provider (Ollama dan Gemini) agar bisa menerima dan memproses message multimodal — teks + gambar.

## Tujuan Teknis

- `OllamaProvider.chat()` dan `chat_stream()` support field `images` di message
- `GeminiChatProvider.chat()` dan `chat_stream()` support image parts
- Format input standar: `{"role": "user", "content": "text", "images": ["base64..."]}`

## Scope

**Dikerjakan:**
- Update `app/ai/ollama_provider.py` — images field di message
- Update `app/ai/gemini_chat_provider.py` — convert base64 ke Gemini image part
- Kedua provider tetap backward-compatible (messages tanpa images tetap berfungsi)

**Tidak dikerjakan:**
- ChatService integration (Task 4)
- Frontend (Task 5+)
- Endpoint validation (Task 4)

## Langkah Implementasi

### Step 1: Update `OllamaProvider`

File: `app/ai/ollama_provider.py`

Ollama SDK sudah support images secara native. Format message:
```python
{"role": "user", "content": "Apa isi gambar ini?", "images": ["base64data..."]}
```

**Tidak perlu perubahan besar** — Ollama SDK meneruskan field `images` otomatis. Yang perlu dipastikan:

1. Method `chat()` — pastikan messages yang mengandung `images` diteruskan as-is:
   ```python
   async def chat(self, messages: list[dict], think: bool = True) -> dict:
       # messages sudah bisa mengandung {"images": [...]} 
       # Ollama SDK handle otomatis
       chat_kwargs = {
           "model": self.model,
           "messages": messages,  # images ikut terkirim
           ...
       }
   ```

2. Method `chat_stream()` — sama, pastikan messages diteruskan:
   ```python
   async def chat_stream(self, messages: list[dict], think: bool = True):
       chat_kwargs = {
           "model": self.model,
           "messages": messages,  # images ikut terkirim
           "stream": True,
           ...
       }
   ```

3. **PENTING**: Hapus `format: "json"` dari `chat_kwargs` di method `chat()` JIKA ada images — model vision biasanya tidak bisa output strict JSON.
   ```python
   # Cek apakah ada images di messages
   has_images = any(m.get("images") for m in messages)
   if not has_images:
       chat_kwargs["format"] = "json"
   # Jika ada images, JANGAN set format json
   ```

### Step 2: Update `GeminiChatProvider`

File: `app/ai/gemini_chat_provider.py`

Update `_convert_messages()` untuk handle image parts:

```python
import base64

def _convert_messages(self, messages: list[dict]) -> list[dict]:
    """Konversi format Ollama → Gemini chat history format, termasuk images."""
    result = []
    system_text = ""

    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        images = msg.get("images", [])

        if role == "system":
            system_text += content + "\n"
        elif role == "user":
            text = (system_text + "\n" + content) if system_text else content
            system_text = ""
            
            # Build parts: teks + images
            parts = [text]
            for img_b64 in images:
                # Decode base64 → bytes → Gemini Image
                img_bytes = base64.b64decode(img_b64)
                parts.append({
                    "mime_type": "image/jpeg",  # atau detect dari header
                    "data": img_bytes,
                })
            
            result.append({"role": "user", "parts": parts})
        elif role == "assistant":
            result.append({"role": "model", "parts": [content]})

    if system_text and not result:
        result.append({"role": "user", "parts": [system_text.strip()]})

    return result
```

### Step 3: Tambah helper detect MIME type (opsional)

```python
def _detect_mime_type(self, b64_data: str) -> str:
    """Detect MIME type dari base64 header."""
    if b64_data.startswith("/9j/"):
        return "image/jpeg"
    elif b64_data.startswith("iVBOR"):
        return "image/png"
    elif b64_data.startswith("R0lGOD"):
        return "image/gif"
    elif b64_data.startswith("UklGR"):
        return "image/webp"
    return "image/jpeg"  # default
```

## Output yang Diharapkan

```python
# Ollama — images diteruskan ke SDK
messages = [
    {"role": "user", "content": "Apa isi gambar ini?", "images": ["base64data..."]}
]
response = await ollama.chat(messages)
# → Response vision dari LLM

# Gemini — images dikonversi ke parts
messages = [
    {"role": "user", "content": "Jelaskan gambar ini", "images": ["base64data..."]}
]
response = await gemini.chat(messages)
# → Response vision dari Gemini
```

## Dependencies

- Task 1: `ModelCapabilityResolver` (untuk konteks, tapi tidak langsung dipakai)

## Acceptance Criteria

- [ ] `OllamaProvider.chat()` meneruskan images di message ke Ollama SDK
- [ ] `OllamaProvider.chat_stream()` meneruskan images di message
- [ ] `OllamaProvider` skip `format: "json"` jika ada images
- [ ] `GeminiChatProvider._convert_messages()` handle image parts
- [ ] Base64 → bytes conversion untuk Gemini
- [ ] MIME type detection
- [ ] Backward-compatible: messages tanpa images tetap berfungsi normal
- [ ] Tidak ada error saat import/startup

## Estimasi

Medium (1-2 jam)
