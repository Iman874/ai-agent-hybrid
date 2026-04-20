import { useUIStore } from "@/stores/ui-store";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useTranslation } from "@/i18n";

export function GeneralSettings() {
  const { t, language, setLanguage } = useTranslation();
  const theme = useUIStore(s => s.theme);
  const setTheme = useUIStore(s => s.setTheme);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <h3 className="text-lg font-medium mb-1">{t("settings.general_title")}</h3>
        <p className="text-sm text-muted-foreground mb-4">{t("settings.general_desc")}</p>
      </div>

      <div className="space-y-4">
        <div className="flex flex-col gap-2">
          <Label className="text-base">{t("settings.theme")}</Label>
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
          <Label className="text-base">{t("settings.language")}</Label>
          <RadioGroup
            value={language}
            onValueChange={(val) => setLanguage(val as "id" | "en")}
            className="flex gap-4 mt-2"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="id" id="lang-id" />
              <Label htmlFor="lang-id" className="font-normal cursor-pointer">
                Bahasa Indonesia
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="en" id="lang-en" />
              <Label htmlFor="lang-en" className="font-normal cursor-pointer">
                English
              </Label>
            </div>
          </RadioGroup>
        </div>
      </div>
    </div>
  );
}
