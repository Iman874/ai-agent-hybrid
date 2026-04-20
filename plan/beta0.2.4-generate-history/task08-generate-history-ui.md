# Task 8: Komponen `GenerateHistory.tsx`

## 1. Judul Task
Buat komponen tabel riwayat generate yang menampilkan semua dokumen yang pernah di-generate.

## 2. Deskripsi
Komponen ini menampilkan daftar riwayat generate dalam bentuk tabel ringkas. User bisa klik untuk melihat detail atau menghapus record. Tampil di bawah UploadForm saat tidak ada result yang sedang dilihat.

## 3. Tujuan Teknis
- Komponen `GenerateHistory.tsx` yang membaca dari `generate-store`
- Tabel dengan kolom: Nama File, Style, Status, Kata, Tanggal, Aksi
- Tombol "Lihat" dan "Hapus" per row
- Empty state jika belum ada riwayat
- Spinner saat loading

## 4. Scope
### Yang dikerjakan
- Buat `src/components/generate/GenerateHistory.tsx`

### Yang tidak dikerjakan
- Tidak mengubah `GenerateContainer` (task 9)
- Tidak mengubah `UploadForm` atau `GenerateResult`

## 5. Langkah Implementasi

### Step 1: Buat `src/components/generate/GenerateHistory.tsx`

```tsx
import { useEffect } from "react";
import { useGenerateStore } from "@/stores/generate-store";
import { useTranslation } from "@/i18n";
import { Button } from "@/components/ui/button";
import { Eye, Trash2, Loader2, CheckCircle, XCircle, Clock } from "lucide-react";

export function GenerateHistory() {
  const { t } = useTranslation();
  const history = useGenerateStore(s => s.history);
  const isLoading = useGenerateStore(s => s.isLoadingHistory);
  const fetchHistory = useGenerateStore(s => s.fetchHistory);
  const viewResult = useGenerateStore(s => s.viewResult);
  const deleteGeneration = useGenerateStore(s => s.deleteGeneration);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  if (isLoading) {
    return (
      <div className="py-8 flex justify-center text-muted-foreground">
        <Loader2 className="w-5 h-5 animate-spin" />
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-6">
        {t("generate.no_history")}
      </p>
    );
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "failed": return <XCircle className="w-4 h-4 text-destructive" />;
      default: return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        {t("generate.history_title")}
      </h3>
      <div className="border rounded-lg divide-y">
        {history.map(item => (
          <div key={item.id} className="flex items-center justify-between px-4 py-3 hover:bg-muted/30 transition">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              {statusIcon(item.status)}
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{item.filename}</p>
                <p className="text-xs text-muted-foreground">
                  {item.style_name ?? "-"} · {item.word_count ? `${item.word_count} kata` : "-"} · {formatDate(item.created_at)}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1 flex-shrink-0 ml-2">
              {item.status === "completed" && (
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => viewResult(item.id)}>
                  <Eye className="w-4 h-4" />
                </Button>
              )}
              <Button
                variant="ghost" size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                onClick={() => deleteGeneration(item.id)}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## 6. Output yang Diharapkan

Tampil sebagai list items:
```
┌────────────────────────────────────────────────────┐
│ ✓ TOR_a2184d4d.docx                      👁 🗑    │
│   Standar Pemerintah · 1.240 kata · 20 Apr 2026   │
├────────────────────────────────────────────────────┤
│ ✗ proposal.pdf                               🗑    │
│   - · - · 19 Apr 2026                             │
└────────────────────────────────────────────────────┘
```

## 7. Dependencies
- Task 7 (generate-store)

## 8. Acceptance Criteria
- [ ] Komponen fetch history on mount
- [ ] Menampilkan icon status (✓ hijau, ✗ merah, ⏳ kuning)
- [ ] Menampilkan filename, style, word_count, tanggal
- [ ] Tombol "View" hanya muncul untuk status `completed`
- [ ] Tombol "Delete" selalu muncul
- [ ] Empty state saat history kosong
- [ ] `npm run build` sukses

## 9. Estimasi
**Medium** (~1.5 jam)
