import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export function FormatTORSettings() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="flex items-center justify-between">
        <div>
            <h3 className="text-lg font-medium mb-1">Format TOR</h3>
            <p className="text-sm text-muted-foreground">Manajemen gaya dan struktur Term of Reference.</p>
        </div>
        <Button size="sm">
            <Plus className="w-4 h-4 mr-2" /> Format Baru
        </Button>
      </div>

      <div className="border rounded-lg divide-y">
          <div className="p-4 flex items-center justify-between">
              <div>
                  <h4 className="font-medium">Standar Akademik</h4>
                  <p className="text-sm text-muted-foreground">Format default untuk kegiatan akademik dasar.</p>
              </div>
              <div className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">Aktif</div>
          </div>
          <div className="p-4 flex items-center justify-between">
              <div>
                  <h4 className="font-medium">Proyek Nasional</h4>
                  <p className="text-sm text-muted-foreground">Struktur komprehensif untuk pengadaan skala besar.</p>
              </div>
              <Button variant="outline" size="sm">Aktifkan</Button>
          </div>
      </div>
    </div>
  );
}
