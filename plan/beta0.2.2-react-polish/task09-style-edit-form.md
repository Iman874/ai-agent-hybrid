# Task 09: StyleEditForm Component — Full Inline Edit Form

## 1. Judul Task

Membuat form edit inline untuk custom styles: metadata, konfigurasi penulisan, dan seksi-seksi TOR

## 2. Deskripsi

Form lengkap yang muncul saat user klik "Edit Style" pada style non-default. Terdiri dari 3 bagian: Informasi Umum (nama, deskripsi), Gaya Penulisan (bahasa, formalitas, voice, perspektif, word counts, penomoran, instruksi kustom), dan Edit Seksi (accordion per-seksi).

## 3. Tujuan Teknis

- `src/components/settings/StyleEditForm.tsx`
- Form state dikelola lokal (`useState`)
- Submit → `updateStyle()` → callback refresh

## 4. Scope

**Yang dikerjakan:**
- `StyleEditForm.tsx` — form lengkap dengan 3 sections
- Validasi dasar (nama wajib diisi)

**Yang tidak dikerjakan:**
- Menambah/menghapus seksi (hanya edit properties yang ada)

## 5. Langkah Implementasi

### 5.1 Buat `src/components/settings/StyleEditForm.tsx`

Struktur form:

```
┌─ Informasi Umum ──────────────────────────┐
│ Nama Style:      [_______________]         │
│ Deskripsi:       [_______________]         │
├─ Gaya Penulisan ──────────────────────────┤
│ Bahasa:    [id ▼]    Formalitas: [formal ▼]│
│ Voice:     [active▼] Perspektif: [third ▼] │
│ Min Kata:  [500]     Max Kata:   [3000]    │
│ Penomoran: [numeric ▼]                     │
│ Instruksi Kustom: [________________]       │
├─ Edit Seksi ──────────────────────────────┤
│ ▶ Seksi 1: Latar Belakang                 │
│ ▶ Seksi 2: Tujuan                         │
│ ▶ Seksi 3: Ruang Lingkup                  │
│   ...                                      │
├────────────────────────────────────────────┤
│ [Simpan Perubahan]                         │
└────────────────────────────────────────────┘
```

Key Implementation:

```tsx
interface Props {
  style: TORStyle;
  onSave: () => void;
}

export function StyleEditForm({ style, onSave }: Props) {
  const { t } = useTranslation();
  
  // Local state initialized from style props
  const [name, setName] = useState(style.name);
  const [description, setDescription] = useState(style.description);
  const [config, setConfig] = useState(style.config);
  const [sections, setSections] = useState(style.sections);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setError("");
    try {
      await updateStyle(style.id, {
        name, description, sections,
        config: { ...config },
      });
      onSave(); // refresh parent
    } catch (e) {
      setError(e instanceof Error ? e.message : t("format.save_failed"));
    } finally {
      setSaving(false);
    }
  };

  // ... render form fields using select/input/textarea ...
}
```

### 5.2 Config field options

```typescript
const langOptions = ["id", "en"];
const formalityOptions = ["formal", "semi_formal", "informal"];
const voiceOptions = ["active", "passive"];
const perspectiveOptions = ["first_person", "third_person"];
const numberingOptions = ["numeric", "roman", "none"];
```

### 5.3 Sections accordion

Each section expandable with fields:
- **Judul Seksi** — text input
- **Instruksi untuk AI** — textarea
- **Wajib Ada di Dokumen** — checkbox
- **Format Hint** — select (paragraphs, bullet_points, table, mixed)
- **Min. Paragraf** — number input

```tsx
{sections.map((sec, i) => (
  <details key={i} className="border rounded-md">
    <summary className="px-3 py-2 cursor-pointer font-medium text-sm">
      Seksi {i + 1}: {sec.title}
    </summary>
    <div className="p-3 space-y-3 border-t">
      <Input value={sec.title} onChange={...} />
      <Textarea value={sec.description} onChange={...} />
      <Checkbox checked={sec.required} onChange={...} />
      <Select value={sec.format_hint} onChange={...} />
      <Input type="number" value={sec.min_paragraphs} onChange={...} />
    </div>
  </details>
))}
```

## 6. Output yang Diharapkan

- Form pre-filled dengan data style saat ini
- Edit nama → ubah → klik Simpan → API call → style updated
- Edit config fields (bahasa, formalitas, dll) → semua terupdate
- Edit seksi properties → terupdate per-section
- Error handling jika gagal simpan

## 7. Dependencies

- Task 01 (i18n)
- Task 04 (API: updateStyle)
- Task 05 (TORStyleSection, TORStyleConfig types)

## 8. Acceptance Criteria

- [ ] Form menampilkan semua field dari style
- [ ] Perubahan tersimpan via PUT API
- [ ] Loading state saat saving
- [ ] Error message jika gagal
- [ ] Form TIDAK muncul untuk style `is_default=true`
- [ ] Semua select/input type-safe dengan opsi yang benar
- [ ] Accordion seksi bisa expand/collapse per-seksi

## 9. Estimasi

High (2 jam)
