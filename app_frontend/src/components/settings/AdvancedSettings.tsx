import { Button } from "@/components/ui/button";

export function AdvancedSettings() {
  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <h3 className="text-lg font-medium mb-1">Lanjutan</h3>
        <p className="text-sm text-muted-foreground">Pengaturan teknis dan manajemen cache.</p>
      </div>

      <div className="space-y-4">
          <div className="flex items-center justify-between py-2 border-b">
              <div>
                  <h4 className="text-sm font-medium">Clear Cache Memory</h4>
                  <p className="text-sm text-muted-foreground">Menghapus sesi cache untuk model AI lokal.</p>
              </div>
              <Button variant="outline" size="sm" className="text-destructive hover:text-destructive">Bersihkan</Button>
          </div>
      </div>
    </div>
  );
}
