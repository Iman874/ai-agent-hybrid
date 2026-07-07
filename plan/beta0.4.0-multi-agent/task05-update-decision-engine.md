# Task 05 — Update DecisionEngine

## Deskripsi

DecisionEngine yang sekarang pake Python if-else buat routing (`chat_service.process_message()` → cek status → `generate_service.generate_tor()`). Di-refactor jadi pake **Supervisor Agent** buat mutusin next action.

## Perubahan

### Sekarang (if-else):
```
chat_service.process_message()
  → parsed.status == "READY_TO_GENERATE"
    → generate_service.generate_tor()
  → parsed.status == "NEED_MORE_INFO"
    → return chat
  → fallback
```

### Nanti (Supervisor):
```
supervisor.process(context)
  → decision == "INTERVIEW"
    → interviewer.process()
  → decision == "GENERATE"
    → writer.process()
  → decision == "REVISE"
    → writer.process(existing_tor, revisi)
  → decision == "CLARIFY"
    → return message ke user
```

### File yang Diubah

**`app/core/decision_engine.py`**:
- Tambah injection: `supervisor_agent`, `interviewer_agent`, `writer_agent`
- Refactor method `route()`:
  - STEP 1-3: session + RAG (same)
  - STEP 4: **Supervisor Agent** → decide action
  - STEP 5: Delegate ke agent sesuai decision
  - STEP 6: Return hasil
- Hapus/comment logic lama yang pake `chat_service.process_message()` langsung
- Keep streaming route (`hybrid_stream_endpoint`) separate for now

## Catatan Penting

- Backward compatibility: Session state machine masih sama (NEW → CHATTING → READY → COMPLETED)
- Tapi transisi state diatur oleh Supervisor + agent result
- Error handling: kalo Supervisor gagal, fallback ke logic lama

## Acceptance Criteria

- [ ] DecisionEngine.route() pake Supervisor Agent
- [ ] INTERVIEW → Interviewer Agent
- [ ] GENERATE → Writer Agent
- [ ] REVISE → Writer Agent dengan existing tor
- [ ] CLARIFY → return message ke user tanpa agent call
- [ ] Fallback: kalo Supervisor gagal, pake logic lama
- [ ] Session state masih berfungsi normal

## Dependencies

- Task 02 (Supervisor Agent)
- Task 03 (Interviewer Agent)
- Task 04 (Writer Agent)

## Estimasi

**Medium** (~3 jam)
