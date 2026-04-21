# Task 17: Provider Streaming — Ollama Fix + Gemini `chat_stream()`

## Deskripsi

Memperbaiki `OllamaProvider.chat_stream()` yang sudah ada agar production-ready, dan menambahkan `chat_stream()` ke `GeminiChatProvider` sehingga kedua provider memiliki interface streaming identik.

## Tujuan Teknis

- `OllamaProvider.chat_stream()` → production-ready (hapus `format: "json"`, tambah timeout)
- `GeminiChatProvider.chat_stream()` → async generator baru dengan output format identik
- Interface standar: `{"token": str, "thinking": str, "done": bool}`

## Scope

**Dikerjakan:**
- Fix `OllamaProvider.chat_stream()` di `app/ai/ollama_provider.py`
- Tambah `GeminiChatProvider.chat_stream()` di `app/ai/gemini_chat_provider.py`
- Pastikan output format identik antar provider

**Tidak dikerjakan:**
- Integrasi ke ChatService (Task 18)
- SSE endpoint (Task 19)
- Frontend (Task 20-21)

## Langkah Implementasi

### Step 1: Fix `OllamaProvider.chat_stream()`

File: `app/ai/ollama_provider.py`

1. Buka method `chat_stream()` (L115-150)
2. **Hapus `format: "json"` dari `chat_kwargs`** — streaming tidak bisa parse JSON per-chunk, JSON hanya untuk response final setelah semua token terkumpul
3. **Tambah timeout wrapper**:
   ```python
   async def chat_stream(self, messages: list[dict], think: bool = True):
       chat_kwargs = {
           "model": self.model,
           "messages": messages,
           # TIDAK ADA format: "json" di sini
           "stream": True,
           "options": {
               "temperature": self.temperature,
               "num_ctx": self.num_ctx,
           },
       }
       
       if not think and self.is_cloud and len(messages) > 0:
           if not messages[-1]["content"].startswith("/nothink "):
               messages[-1]["content"] = "/nothink " + messages[-1]["content"]
       
       try:
           stream = await asyncio.wait_for(
               self.client.chat(**chat_kwargs),
               timeout=self.timeout,
           )
           async for chunk in stream:
               msg = chunk.get("message", {})
               yield {
                   "token": msg.get("content", ""),
                   "thinking": msg.get("thinking", ""),
                   "done": chunk.get("done", False),
               }
       except asyncio.TimeoutError:
           raise OllamaTimeoutError(timeout_seconds=self.timeout)
       except Exception as e:
           error_msg = str(e).lower()
           if "connect" in error_msg or "refused" in error_msg:
               raise OllamaConnectionError(details=str(e))
           raise
   ```

### Step 2: Tambah `GeminiChatProvider.chat_stream()`

File: `app/ai/gemini_chat_provider.py`

1. Tambah method `chat_stream()` setelah `chat()`:
   ```python
   async def chat_stream(self, messages: list[dict], think: bool = True):
       """
       Streaming chat via Gemini API.
       Yield format identik OllamaProvider: {"token": str, "thinking": str, "done": bool}
       Gemini TIDAK support thinking → thinking selalu "".
       """
       gemini_messages = self._convert_messages(messages)
       
       try:
           if len(gemini_messages) > 1:
               chat_session = self.model.start_chat(history=gemini_messages[:-1])
               last_msg = gemini_messages[-1]["parts"][0]
               response = await asyncio.wait_for(
                   asyncio.to_thread(
                       chat_session.send_message, last_msg, stream=True
                   ),
                   timeout=self.timeout,
               )
           else:
               prompt = gemini_messages[0]["parts"][0]
               response = await asyncio.wait_for(
                   asyncio.to_thread(
                       self.model.generate_content, prompt, stream=True
                   ),
                   timeout=self.timeout,
               )
           
           # Iterate streaming response
           for chunk in response:
               text = chunk.text if hasattr(chunk, 'text') else ""
               if text:
                   yield {
                       "token": text,
                       "thinking": "",  # Gemini tidak support thinking
                       "done": False,
                   }
           
           # Final done signal
           yield {"token": "", "thinking": "", "done": True}
       
       except asyncio.TimeoutError:
           raise GeminiTimeoutError(self.timeout)
       except Exception as e:
           raise GeminiAPIError(details=str(e)[:200])
   ```

2. Pastikan `import asyncio` ada di file header

### Step 3: Verifikasi interface identik

Bandingkan output kedua provider:

```python
# Ollama yield:
{"token": "Berdasarkan", "thinking": "", "done": False}
{"token": " informasi", "thinking": "", "done": False}
{"token": "", "thinking": "", "done": True}

# Gemini yield (identik):
{"token": "Berdasarkan", "thinking": "", "done": False}
{"token": " informasi", "thinking": "", "done": False}
{"token": "", "thinking": "", "done": True}

# Ollama dengan thinking:
{"token": "", "thinking": "Analisis...", "done": False}  ← fase thinking
{"token": "Berdasarkan", "thinking": "", "done": False}   ← fase output
{"token": "", "thinking": "", "done": True}
```

## Output yang Diharapkan

Kedua provider memiliki `chat_stream()` yang:
- Yield token demi token secara real-time
- Format output `{"token": str, "thinking": str, "done": bool}` identik
- Timeout protection
- Error handling konsisten

## Dependencies

Tidak ada — ini task pertama Beta 0.2.6.

## Acceptance Criteria

- [ ] `OllamaProvider.chat_stream()` tidak lagi menggunakan `format: "json"`
- [ ] `OllamaProvider.chat_stream()` memiliki timeout wrapper
- [ ] `GeminiChatProvider.chat_stream()` baru ditambahkan
- [ ] Output format kedua provider identik: `{"token", "thinking", "done"}`
- [ ] Gemini `chat_stream()` yield `thinking: ""` (tidak memalsukan thinking)
- [ ] Error handling: timeout, connection error

## Estimasi

Medium (1-2 jam)
