# Task 09 — Frontend Agent Types

## Deskripsi

Buat tipe TypeScript untuk agent system di frontend.

## File Baru

**`app_frontend/src/types/agent.ts`**:

```typescript
export type AgentType = "supervisor" | "interviewer" | "writer";

export interface AgentEvent {
  agent: AgentType;
  action: string;
}

// Mapping untuk display name
export const AGENT_LABELS: Record<AgentType, { name: string; icon: string }> = {
  supervisor: { name: "Supervisor", icon: "M19.5 12c0-1.232-.046-2.453-.138-3.662a4.006 4.006 0 0 0-3.7-3.7 48.678 48.678 0 0 0-7.324 0 4.006 4.006 0 0 0-3.7 3.7c-.017.22-.032.441-.046.662" },
  interviewer: { name: "Interviewer", icon: "M12 20.25c4.97 0 9-3.694 9-8.25s-4.03-8.25-9-8.25S3 7.444 3 12c0 2.104.859 4.023 2.273 5.48.432.447.74 1.04.586 1.641a4.483 4.483 0 0 1-.923 1.785A5.969 5.969 0 0 0 6 21c1.282 0 2.47-.402 3.445-1.087.81.22 1.668.337 2.555.337Z" },
  writer: { name: "Writer", icon: "M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" },
};
```

## Acceptance Criteria

- [ ] `AgentType` type tersedia
- [ ] `AGENT_LABELS` ada mapping untuk name + icon SVG
- [ ] File bisa di-import tanpa error

## Estimasi

**Low** (~15 menit)
