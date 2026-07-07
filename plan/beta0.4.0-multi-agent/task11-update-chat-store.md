# Task 11 — Update Chat Store

## Deskripsi

Update Zustand chat store (`app_frontend/src/stores/chat-store.ts`) untuk handle `agent_switch` SSE events dan track active agent.

---

## Perubahan State

```typescript
interface ChatState {
  // Existing
  messages: Message[];
  isStreaming: boolean;
  partialContent: string;
  // ...

  // NEW
  activeAgent: AgentType | null;
  agentAction: string;
}
```

## Perubahan Actions

```typescript
interface ChatActions {
  // ...
  // NEW
  setActiveAgent: (agent: AgentType | null, action: string) => void;
}
```

## Perubahan sendMessageStream

Di `sendMessageStream()`, tambah handler buat event `agent_switch`:

```typescript
// Di event handler SSE reader:
if (event.type === "agent_switch") {
  set({ activeAgent: event.data.agent, agentAction: event.data.action });
  continue;
}
```

## Perubahan finalizeStream

Pas streaming selesai (`onDone`), reset active agent:

```typescript
set({ activeAgent: null, agentAction: "" });
```

---

## Acceptance Criteria

- [ ] `activeAgent` state terupdate dari SSE event `agent_switch`
- [ ] `agentAction` menyimpan deskripsi aksi agent
- [ ] State di-reset pas streaming selesai
- [ ] Komponen lain bisa akses `activeAgent` dari store

---

## Dependencies

- Task 09 (Agent Types)

---

## Estimasi

**Low** (~30 menit)
