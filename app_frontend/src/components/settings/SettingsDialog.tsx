import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";
import { GeneralSettings } from "./GeneralSettings";
import { FormatTORSettings } from "./FormatTORSettings";
import { AdvancedSettings } from "./AdvancedSettings";

const NAV_ITEMS = [
  { key: "umum" as const, label: "Umum" },
  { key: "format_tor" as const, label: "Format TOR" },
  { key: "lanjutan" as const, label: "Lanjutan" },
];

export function SettingsDialog() {
  const open = useUIStore(s => s.settingsOpen);
  const section = useUIStore(s => s.settingsSection);
  const closeSettings = useUIStore(s => s.closeSettings);
  const openSettings = useUIStore(s => s.openSettings);

  return (
    <Dialog open={open} onOpenChange={(v) => !v && closeSettings()}>
      <DialogContent className="max-w-3xl h-[85vh] sm:h-[600px] p-0 gap-0 overflow-hidden rounded-xl">
        <div className="flex h-full flex-col sm:flex-row">
          {/* Nav sidebar */}
          <div className="sm:w-48 border-b sm:border-b-0 sm:border-r border-border p-4 space-y-1 flex-shrink-0 bg-muted/20">
            <DialogHeader className="pb-4">
              <DialogTitle className="text-base font-semibold">Pengaturan</DialogTitle>
            </DialogHeader>
            <div className="flex sm:flex-col gap-1 overflow-x-auto pb-2 sm:pb-0">
                {NAV_ITEMS.map(item => (
                <Button
                    key={item.key}
                    variant="ghost"
                    size="sm"
                    className={cn(
                    "justify-start text-sm font-normal sm:w-full flex-shrink-0",
                    section === item.key && "bg-primary/10 font-medium text-foreground",
                    section !== item.key && "text-muted-foreground"
                    )}
                    onClick={() => openSettings(item.key)}
                >
                    {item.label}
                </Button>
                ))}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {section === "umum" && <GeneralSettings />}
            {section === "format_tor" && <FormatTORSettings />}
            {section === "lanjutan" && <AdvancedSettings />}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
