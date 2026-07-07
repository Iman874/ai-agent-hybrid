# Task 07 — Update API Streaming (SSE Agent Events)

## Deskripsi

Streaming endpoint (`POST /api/v1/hybrid/stream`) perlu di-update buat nambahin SSE event `agent_switch`. Ini biar frontend bisa nunjukkin ke user agent mana yang sedang aktif.

---

## SSE Event Baru

### `agent_switch`

Dikirim pas agent berubah. Frontend pake event ini buat nampilin indikator.

```json
{
    "type": "agent_switch",
    "data": {
        "agent": "supervisor",
        "action": "Menganalisis percakapan..."
    }
}
```

### Flow Streaming (New)

```
1. User send message
    → SSE: {"type": "status", "session_id": "..."}
    → SSE: {"type": "agent_switch", "agent": "supervisor", ...}
    → (Supervisor LLM thinking)

2. Decision: INTERVIEW
    → SSE: {"type": "agent_switch", "agent": "interviewer", ...}
    → (Interviewer LLM streaming)
    → SSE: {"type": "token", "token": "Baik, ..."}
    → SSE: {"type": "token", "token": "berapa hari..."}
    → SSE: {"type": "done", ...}

3. Decision: GENERATE
    → SSE: {"type": "agent_switch", "agent": "writer", ...}
    → (Writer LLM streaming)
    → SSE: {"type": "token", "token": "# Term of Reference..."}
    → SSE: {"type": "done", ...}
```

---

## Acceptance Criteria

- [ ] SSE event `agent_switch` terkirim sebelum agent mulai
- [ ] Frontend bisa parse event `agent_switch`
- [ ] Backward compatible: client lama ignore event baru
- [ ] Streaming tetap jalan normal

---

## Dependencies

- Task 05 (DecisionEngine)

---

## Estimasi

**Low** (~1 jam)
