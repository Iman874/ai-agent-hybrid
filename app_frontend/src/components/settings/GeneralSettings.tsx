import { useUIStore } from "@/stores/ui-store";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

export function GeneralSettings() {
  const theme = useUIStore(s => s.theme);
  const setTheme = useUIStore(s => s.setTheme);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <h3 className="text-lg font-medium mb-1">Umum</h3>
        <p className="text-sm text-muted-foreground mb-4">Pengaturan tampilan dan pengalaman pengguna.</p>
      </div>

      <div className="space-y-4">
        <div className="flex flex-col gap-2">
          <Label className="text-base">Tema</Label>
          <RadioGroup
            value={theme}
            onValueChange={(val: any) => setTheme(val)}
            className="flex gap-4 mt-2"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="light" id="light" />
              <Label htmlFor="light" className="font-normal cursor-pointer">Light</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="dark" id="dark" />
              <Label htmlFor="dark" className="font-normal cursor-pointer">Dark</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="system" id="system" />
              <Label htmlFor="system" className="font-normal cursor-pointer">System</Label>
            </div>
          </RadioGroup>
        </div>
      </div>
      
      <div className="space-y-4 pt-4 border-t">
        <div className="flex flex-col gap-2">
          <Label className="text-base">Bahasa</Label>
          <div className="text-sm text-muted-foreground">
             Bahasa Indonesia (Default)
          </div>
        </div>
      </div>
    </div>
  );
}
