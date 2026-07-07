# Task 08 — Update main.py (Dependency Injection)

## Deskripsi

Update `app/main.py` untuk inisialisasi agent-agent baru dan inject ke DecisionEngine / ChatService.

---

## Perubahan

### Tambahan Init

```python
# Init Agents
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.interviewer_agent import InterviewerAgent
from app.agents.writer_agent import WriterAgent

supervisor_agent = SupervisorAgent(settings)
interviewer_agent = InterviewerAgent(settings)
writer_agent = WriterAgent(settings)

app.state.supervisor_agent = supervisor_agent
app.state.interviewer_agent = interviewer_agent
app.state.writer_agent = writer_agent
```

### Update DecisionEngine Init

```python
app.state.decision_engine = DecisionEngine(
    chat_service=app.state.chat_service,
    generate_service=app.state.generate_service,
    session_mgr=app.state.session_mgr,
    escalation_checker=app.state.escalation_checker,
    progress_tracker=app.state.progress_tracker,
    escalation_logger=app.state.escalation_logger,
    rag_pipeline=app.state.rag_pipeline,
    supervisor_agent=supervisor_agent,       # NEW
    interviewer_agent=interviewer_agent,     # NEW
    writer_agent=writer_agent,               # NEW
)
```

### Update ChatService Init (optional)

Kalo ChatService didelegasikan pake InterviewerAgent:

```python
app.state.chat_service = ChatService(
    ...
    interviewer_agent=interviewer_agent,     # NEW
)
```

---

## Acceptance Criteria

- [ ] Semua agent terinisialisasi di startup
- [ ] Tidak ada circular import
- [ ] DecisionEngine menerima agent-agent baru
- [ ] Graceful degradation: kalo agent gagal init, sistem tetap jalan

---

## Dependencies

- Task 02 (Supervisor Agent)
- Task 03 (Interviewer Agent)
- Task 04 (Writer Agent)
- Task 05 (DecisionEngine)
- Task 06 (ChatService)

---

## Estimasi

**Low** (~30 menit)
