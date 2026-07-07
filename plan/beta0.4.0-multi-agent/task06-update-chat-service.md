# Task 06 — Update ChatService

## Deskripsi

`ChatService.process_message()` yang sekarang nanganin semua (build prompt, call LLM, parse, merge data) perlu di-refactor karena logika interviewnya pindah ke **Interviewer Agent**.

ChatService tetap ada sebagai **orchestrator session** (session management, history, RAG) tapi logika LLM call-nya didelegasikan ke agent.

---

## Perubahan

### Sekarang:
```
ChatService.process_message()
  ├── SessionManager (get/create)
  ├── RAG retrieval
  ├── PromptBuilder.build_chat_messages()
  ├── LLM call (provider.chat())
  ├── ResponseParser.extract_json()
  ├── Completeness.calculate()
  ├── SessionManager.append_message()
  └── Return ChatResult
```

### Nanti:
```
ChatService.process_message()
  ├── SessionManager (get/create)         ← SAME
  ├── RAG retrieval                       ← SAME
  ├── Build AgentContext                  ← NEW
  ├── Call InterviewerAgent.process()     ← DELEGATED
  ├── Completeness.calculate()            ← SAME (opsional)
  ├── SessionManager.append_message()     ← SAME
  └── Return ChatResult / AgentResult
```

### File yang Diubah

**`app/services/chat_service.py`**:
- Tambah injection: `interviewer_agent`
- Simplify `process_message()`:
  - Session + RAG tetap
  - Build `AgentContext` dari session data
  - Panggil `interviewer_agent.process(context)`
  - Merge extracted data + update session
  - Return `ChatResult` seperti biasa
- Keep `process_message_stream()` — nanti di-refactor di task terpisah
- `_get_provider()` tetap ada (buat fallback)

### Catatan

- `process_message()` masih dipanggil oleh `decision_engine.route()` — bedanya sekarang DecisionEngine udah pake Supervisor, jadi ChatService cuma dipanggil kalo Supervisor bilang INTERVIEW
- Streaming (`process_message_stream`) belum di-refactor — masih pake logic lama. Nanti di phase berikutnya
- Session management & RAG tetap di ChatService, gak pindah

---

## Acceptance Criteria

- [ ] `process_message()` delegate LLM call ke InterviewerAgent
- [ ] Session management tetap jalan
- [ ] RAG tetap di-inject ke prompt
- [ ] ChatResult return dengan format yang sama (backward compatible)
- [ ] Streaming belum berubah
- [ ] Fallback ke provider langsung kalo InterviewerAgent gagal

---

## Dependencies

- Task 03 (Interviewer Agent)
- Task 05 (DecisionEngine refactor)

---

## Estimasi

**Medium** (~2-3 jam)
