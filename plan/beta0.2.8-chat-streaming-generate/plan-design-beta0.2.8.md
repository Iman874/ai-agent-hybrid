# Beta 0.2.8 — Chat-to-TOR Streaming Generate & Bugfix

## 1. Ringkasan

Menuntaskan isu kegagalan sistem saat beralih dari fase Chat ke fase Pembuatan TOR secara otomatis ("status `READY_TO_GENERATE` diterima dari lokal AI tapi tidak ada pembuatan dokumen"). Bersamaan dengan perbaikan *bug*, pembaruan ini akan menghadirkan pengalaman **Streaming Pembuatan TOR dari sumber Obrolan**, menggunakan standar yang telah ada di generasi dokumen (beta 0.2.5).

**Teknologi Utama**: Endpoint *Server-Sent Events (SSE)* baru, React *State Hooks* untuk pengalihan (transitioning) antarmuka, dan optimasi pemulihan jika jaringan putus secara simetris dengan standar document-generate yang lalu.

---

## 2. Analisis Akar Masalah

### Alur Saat Ini (Buggy)
```
Frontend                              Backend (app/api/routes/hybrid.py)
────────                              ───────
[User Bertanya]
POST /hybrid/stream  ───────────────> process_message_stream()
← SSE: {"type": "token"}              ↓ Chat mode, local ollama
← SSE: {"type": "token"}              ↓ ...
← SSE: {"type": "done",               ← AI merespons READY_TO_GENERATE
      "status": "READY_TO_GENERATE"}  
[UI Diam Saja/Menunggu]               (Backend berhenti karena bypass DecisionEngine)
```

Pada beta sebelumnya (0.2.6 Streaming Chat), endpoint baru dibuat untuk chat *streaming*. Tapi ia tak lagi melewati `DecisionEngine.route()` otomatis yang sebelumnya langsung menjalankan perintah cetak *TOR sinkron (blocking)*. Alhasil, frontend tahu chat sudah berstatus `"READY_TO_GENERATE"`, tetapi backend melepas koneksi begitu blok *chat return* selesai diberikan.

---

## 3. Arsitektur Solusi Target (Two-Stage Streaming)

Menggabungkan *Chat Tokens* dan *Generate Tokens* pada satu saluran stream HTTP akan membingungkan State Management Frontend.
Jadi, solusi ideal adalah **Two-Stage Streaming**:

```
Frontend                              Backend
────────                              ───────
[Tahap 1: Chat Stream]
POST /hybrid/stream  ───────────────> process_message_stream()
←... (chat stream) ...                ↓ Chat processing
← SSE {"type":"done",                 ← Memutuskan status: READY
      "status": "READY_TO_GENERATE", 
      "session_id": "123"}
            ↓
            ↓ (Frontend secara otomatis "menyingkirkan" layar chat 
            ↓ dan memunculkan layar `StreamingResult`)
            ↓
[Tahap 2: Generate Stream]
POST /generate/chat/stream ─────────> generate_tor_from_chat_stream()
← SSE {"type": "status"}              ↓ Ambil Session & History chat
← SSE {"type": "token", "t": "# "}    ↓ Prompt buatan → jalankan Gemini
← SSE {"type": "token", "t": "TOR"}   ↓ Gemini stream yields...
← SSE {"type": "done", "metadata"}    ← Simpan ke DB & Cache
```

### Keuntungan:
1. Kita memisahkan domain API dengan bersih. Chat fokus ke *hybrid chat*, sementara generator khusus mencetak dokumen.
2. Memakai ulang komponen Visual (*Reusability*). File `StreamingResult.tsx` di React tidak perlu di-rewrite; cukup mengubah sedikit sumber *pemanggilnya*.
3. Toleransi kesalahan (Fault tolerance). Chat history akan otomatis tersimpan. Bila generator gagal atau *timeout*, pengguna tinggal memencet tombol "Minta Buat Ulang TOR" yang otomatis menelepon ulang endpoint Generate.

---

## 4. Backend: Perubahan Spesifik

### 4.1 Endpoint Baru di `app/api/routes/generate.py`
Tambahkan satu endpoint khusus di bawah `router` milik *generate API*:

```python
from fastapi.responses import StreamingResponse
from fastapi import Request
from app.utils.sse import sse_event

@router.post("/generate/chat/stream")
async def generate_tor_from_chat_stream(request: Request, body: GenerateRequest):
    generate_service = request.app.state.generate_service
    gemini = request.app.state.gemini_provider
    session_mgr = request.app.state.session_mgr
    cost_ctrl = request.app.state.cost_ctrl
    prompt_builder = request.app.state.prompt_builder
    post_processor = request.app.state.post_processor
    tor_cache = request.app.state.tor_cache

    async def event_stream():
        full_text = ""
        cancelled = False
        
        try:
            if await request.is_disconnected(): return
            yield sse_event("status", {"msg": "Memeriksa data sesi chat..."})
            
            # Step 1: Tarik data
            session = await session_mgr.get(body.session_id)
            history = await session_mgr.get_chat_history(body.session_id)
            data = session.extracted_data

            if await request.is_disconnected(): return
            yield sse_event("status", {"msg": "Menyiapkan instruksi sistem..."})

            # Step 2: RAG dan Format Styles
            # (Silakan mereplika logic pengambilan instruksi pada generate_service.py)
            prompt = prompt_builder.build_standard(data=data, ...) # Handle juga escalation mode bila perlu
            
            if await request.is_disconnected(): return
            yield sse_event("status", {"msg": "Mulai membuat TOR..."})
            
            # Step 3: Stream tokens
            async for chunk in gemini.generate_stream(prompt):
                if await request.is_disconnected():
                    cancelled = True
                    break
                full_text += chunk
                yield sse_event("token", {"t": chunk})

            if cancelled:
                return
            
            # Step 4: Post-processing selesai stream
            yield sse_event("status", {"msg": "Menyelesaikan dokumen dan merapikan format..."})
            processed = post_processor.process(full_text)
            
            # Persist and Logging
            await cost_ctrl.log_call(...)
            await session_mgr.update(body.session_id, state="COMPLETED", generated_tor=processed.content)
            
            # Format return response done
            yield sse_event("done", {
                "session_id": body.session_id,
                "metadata": {
                    "word_count": processed.word_count,
                    "mode": body.mode,
                    # dst...
                }
            })
            
        except Exception as e:
            yield sse_event("error", {"msg": str(e)[:300]})
            
    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

---

## 5. Frontend: Perubahan Spesifik

### 5.1 Update API Client (`src/api/generate.ts`)
Tambahkan utilitas konektor SSE untuk obrolan:
```typescript
export async function streamGenerateFromChat(
  sessionId: string,
  mode: string,  // "standard" | "escalation"
  callbacks: { onStatus, onToken, onDone, onError },
  abortSignal?: AbortSignal
): Promise<void>
```
*Isinya akan sangat identik dengan `streamGenerateFromDocument()`, hanya saja payload body-nya berbeda (pakai JSON bukan FormData, atau sesuaikan dengan interface `GenerateRequest` backend).*

### 5.2 Modifikasi Penguras (*Store Wiring*) di `src/stores/chat-store.ts` 
Ketika menerima event SSE `"done"` dari chat token stream, cek apakah status AI berbunyi siap cetak:
```typescript
// di dalam logic pembacaan chunk chat
case "done":
    const completeData = data as any;
    if (completeData.status === "READY_TO_GENERATE" || completeData.status === "ESCALATE_TO_GEMINI") {
        // Hentikan state Chat Loading
        set({ isChatting: false, sessionState: completeData.status });
        
        // --- INI PENAMBAHAN BARU ---
        // Panggil Generate Store untuk secara auto mulai menyedot streaming TOR
        const mode = completeData.status === "ESCALATE_TO_GEMINI" ? "escalation" : "standard";
        useGenerateStore.getState().generateFromChatStream(completeData.session_id, mode);
    }
```

### 5.3 Modifikasi Transisi UI di `src/components/chat/ChatContainer.tsx`
Ketika Chat sedang beralih status menuju *streaming*, layout container perlu bereaksi dengan mengarahkan layar pindah ke bentuk visual pembuatan dokumen.
* Bila `useGenerateStore.getState().isStreaming === true` (atau state tersendiri): Tampilkan `StreamingResult.tsx` di panel utama menggantikan/menutupi list history obrolan.
* Alternatif lainnya: Lempar langsung navigasi App Router ke `/generate/result?id=...` jika komponen `StreamingResult` difungsikan sebagai page khusus.

---

## 6. Daftar Tugas (Task Breakdown)

| Kode    | Task File                                | Layer     | Deskripsi                                                    | Est.   |
|---------|------------------------------------------|-----------|--------------------------------------------------------------|--------|
| **T01** | `task01-backend-stream-endpoint.md`      | Backend   | Endpoint SSE `POST /generate/chat/stream`                    | 2 jam  |
| **T02** | `task02-frontend-api-client.md`          | Frontend  | API client `streamGenerateFromChat()`                        | 30 min |
| **T03** | `task03-generate-store-action.md`        | Frontend  | Generate store action `generateFromChatStream()`             | 45 min |
| **T04** | `task04-chat-store-auto-trigger.md`      | Frontend  | Auto-trigger di `finalizeStream()` saat status READY         | 30 min |
| **T05** | `task05-ui-transition-feedback.md`       | Frontend  | Visual feedback: source label + transition message           | 45 min |
| **T06** | `task06-chat-generate-button.md`         | Frontend  | Tombol manual "Buat TOR" di chat area                        | 45 min |
| **T07** | `task07-session-state-guard.md`          | Backend   | Guard `GENERATING` state + rollback proteksi                 | 30 min |
| **T08** | `task08-i18n-keys.md`                    | Frontend  | i18n keys ID/EN untuk fitur baru                             | 20 min |
| **T09** | `task09-testing-edge-cases.md`           | QA        | Pengujian E2E 8 skenario + edge cases                        | 2 jam  |

**Total estimasi: ~8 jam kerja**

### Dependency Graph

```
T01 ──→ T02 ──→ T03 ──→ T04 ──→ T05 ──→ T08
  │                       ↑                ↑
  └──→ T07                │                │
                    T06 ──┘                │
                                     T09 ──┘ (semua task selesai)
```

---

## 7. Referensi Integrasi
- Metode koneksi & utilitas timeout menggunakan kode sandi yang diproduksi pada `beta0.2.5` (`app/utils/sse.py`, timeout 120 detik, abort controller di React).
- Pastikan tak ada status silent fail: Seluruh Exception di `/generate/chat/stream` harus tercetak menjadi `yield sse_event("error", ...)` agar *partial generation* memegang peringatan di UI.
