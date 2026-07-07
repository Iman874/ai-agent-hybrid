# Task 10 — Agent Indicator Component

## Deskripsi

Buat komponen UI yang nunjukkin agent mana yang lagi aktif. Ini muncul di chat area selama proses streaming.

---

## File Baru

**`app_frontend/src/components/chat/AgentIndicator.tsx`**:

```
┌──────────────────────────────────────┐
│  ● Supervisor — Menganalisis...      │
│  ● Interviewer — Menggali data...    │
│  ● Writer — Menulis TOR...           │
└──────────────────────────────────────┘

(Agent yang aktif di-highlight, yang lain lebih gelap)
```

### Props

```typescript
interface AgentIndicatorProps {
  activeAgent: AgentType | null;
  agentAction: string;
  isStreaming: boolean;
}
```

### States

- **Idle**: no indicator shown (null)
- **Active**: indicator shown dengan agent name + action text
- **Transition**: animasi agent switching

### Posisi di Layout

Di atas streaming text / message bubble:

```
[AgentIndicator: Interviewer aktif]
│
▼
"Baik, saya akan menggali data TOR yang dibutuhkan..."
```

## Acceptance Criteria

- [ ] Indicator muncul pas streaming aktif
- [ ] Nunjukkin nama agent yang aktif
- [ ] Animasi switching antar agent
- [ ] Hilang pas streaming selesai
- [ ] Styling sesuai tema (light/dark mode)

## Dependencies

- Task 09 (Agent Types)

## Estimasi

**Low** (~1 jam)
