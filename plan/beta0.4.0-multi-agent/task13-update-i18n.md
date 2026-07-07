# Task 13 — Update i18n (Internationalization)

## Deskripsi

Tambah key-key baru buat agent system di file i18n.

---

## File yang Diubah

### `app_frontend/src/i18n/locales/id.ts`

```typescript
export const id = {
  // ... existing keys
  agent: {
    supervisor: "Supervisor",
    interviewer: "Interviewer",
    writer: "Writer",
    supervisor_action: "Menganalisis percakapan...",
    interviewer_action: "Menggali data TOR...",
    writer_action: "Menulis dokumen TOR...",
    switching: "Beralih ke {{agent}}...",
  },
};
```

### `app_frontend/src/i18n/locales/en.ts`

```typescript
export const en = {
  // ... existing keys
  agent: {
    supervisor: "Supervisor",
    interviewer: "Interviewer",
    writer: "Writer",
    supervisor_action: "Analyzing conversation...",
    interviewer_action: "Gathering TOR data...",
    writer_action: "Writing TOR document...",
    switching: "Switching to {{agent}}...",
  },
};
```

### Usage di Komponen

```typescript
const { t } = useTranslation();

// Di AgentIndicator:
t(`agent.${agent}_action`)
// Output: "Menggali data TOR..."
```

---

## Acceptance Criteria

- [ ] Semua agent labels ada di id.ts dan en.ts
- [ ] Agent action descriptions ada
- [ ] Template string `{{agent}}` berfungsi
- [ ] Backward compatible — key lama tidak berubah

---

## Dependencies

- Task 09 (Agent Types) — untuk tau nama agent yang perlu di-i18n

---

## Estimasi

**Low** (~15 menit)
