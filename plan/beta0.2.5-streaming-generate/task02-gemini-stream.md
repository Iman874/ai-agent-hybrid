# Task 2: GeminiProvider `generate_stream()` + Timeout

## 1. Judul Task
Tambah method `generate_stream()` di `GeminiProvider` untuk streaming output Gemini chunk per chunk dengan timeout protection.

## 2. Deskripsi
Method baru ini memanggil `generate_content(prompt, stream=True)` dari Gemini SDK dan yield setiap text chunk sebagai `AsyncGenerator`. Dilengkapi timeout per-stream agar tidak hang selamanya.

## 3. Tujuan Teknis
- Method `generate_stream(prompt, timeout)` → `AsyncGenerator[str, None]`
- Yield setiap `chunk.text` yang non-empty
- Timeout check setiap chunk (elapsed > timeout → raise `GeminiTimeoutError`)
- Error handling konsisten dengan method `generate()` yang sudah ada

## 4. Scope
### Yang dikerjakan
- Tambah method `generate_stream()` di `app/ai/gemini_provider.py`
- Import `AsyncGenerator` dari `typing`

### Yang tidak dikerjakan
- Tidak membuat endpoint SSE (task 3)
- Tidak mengubah method `generate()` yang sudah ada

## 5. Langkah Implementasi

### Step 1: Buka `app/ai/gemini_provider.py`

### Step 2: Tambahkan import

```python
from typing import AsyncGenerator
```

### Step 3: Tambahkan method setelah `generate()`

```python
async def generate_stream(
    self, prompt: str, timeout: float | None = None
) -> AsyncGenerator[str, None]:
    """Stream generate content — yield text chunks.

    Args:
        prompt: Prompt text to send to Gemini.
        timeout: Max seconds for entire stream. Defaults to self.timeout.

    Yields:
        str: Text chunks from Gemini response.

    Raises:
        GeminiTimeoutError: If stream exceeds timeout.
        GeminiAPIError: If API call fails.
    """
    effective_timeout = timeout or self.timeout
    start = time.monotonic()

    try:
        # generate_content with stream=True → returns sync iterable of chunks
        response = await asyncio.to_thread(
            self.model.generate_content, prompt, stream=True
        )
    except Exception as e:
        error_str = str(e)
        if "API_KEY" in error_str.upper() or "INVALID" in error_str.upper():
            raise GeminiAPIError(
                details=f"API key mungkin tidak valid: {error_str[:200]}"
            )
        raise GeminiAPIError(details=error_str[:200])

    # Iterate chunks — sync iterable from Gemini SDK
    for chunk in response:
        # Timeout check setiap chunk
        elapsed = time.monotonic() - start
        if elapsed > effective_timeout:
            logger.warning(
                f"Gemini stream timeout: {elapsed:.1f}s > {effective_timeout}s"
            )
            raise GeminiTimeoutError(effective_timeout)

        if chunk.text:
            yield chunk.text

    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info(f"Gemini stream completed: {duration_ms}ms")
```

## 6. Output yang Diharapkan

```python
gemini = GeminiProvider(settings)

# Streaming chunks
async for chunk in gemini.generate_stream("Buatkan TOR..."):
    print(chunk, end="", flush=True)
# Output: "# TOR" " Kegiatan" " Pelatihan" " AI\n\n" "## 1." " Latar" ...

# Timeout scenario
async for chunk in gemini.generate_stream("...", timeout=5):
    # Raises GeminiTimeoutError after 5 seconds
```

## 7. Dependencies
- Tidak ada (bisa dikerjakan paralel dengan Task 1)

## 8. Acceptance Criteria
- [ ] Method `generate_stream()` ada di `GeminiProvider`
- [ ] Return type: `AsyncGenerator[str, None]`
- [ ] Parameter `timeout` optional, default ke `self.timeout`
- [ ] Timeout check per-chunk via `time.monotonic()`
- [ ] `GeminiTimeoutError` di-raise jika timeout
- [ ] `GeminiAPIError` di-raise jika API error (API key, network, dll)
- [ ] Method `generate()` yang sudah ada TIDAK berubah
- [ ] Backend restart tanpa error

## 9. Estimasi
**Medium** (~45 menit)
