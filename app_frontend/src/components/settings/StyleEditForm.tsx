import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { updateStyle } from "@/api/styles";
import { useTranslation } from "@/i18n";
import { Loader2, Save } from "lucide-react";
import type { TORStyle, TORStyleSection, TORStyleConfig } from "@/types/api";

interface Props {
  style: TORStyle;
  onSave: () => void;
}

export function StyleEditForm({ style, onSave }: Props) {
  const { t } = useTranslation();
  
  const [name, setName] = useState(style.name);
  const [description, setDescription] = useState(style.description);
  const [config, setConfig] = useState<TORStyleConfig>(style.config);
  const [sections, setSections] = useState<TORStyleSection[]>(style.sections || []);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setError("");
    try {
      await updateStyle(style.id, {
        name,
        description,
        sections,
        config: { ...config },
      });
      onSave();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("format.save_failed"));
    } finally {
      setSaving(false);
    }
  };

  const updateSection = (index: number, attr: keyof TORStyleSection, value: any) => {
    const newSections = [...sections];
    newSections[index] = { ...newSections[index], [attr]: value };
    setSections(newSections);
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-top-2 duration-300 border border-border p-5 rounded-xl bg-muted/10">
      
      {/* 1. Informasi Umum */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold">Informasi Umum</h4>
        <div className="space-y-2">
          <Label className="text-xs">Nama Style</Label>
          <Input value={name} onChange={e => setName(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label className="text-xs">Deskripsi</Label>
          <Textarea value={description} onChange={e => setDescription(e.target.value)} rows={2} />
        </div>
      </div>

      <div className="border-t border-border" />

      {/* 2. Gaya Penulisan */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold">{t("format.writing_style")}</h4>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <Label className="text-xs">{t("format.metric_language")}</Label>
            <Select value={config.language} onValueChange={v => setConfig({ ...config, language: v as any })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="id">Indonesia</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-1.5">
            <Label className="text-xs">{t("format.metric_formality")}</Label>
            <Select value={config.formality} onValueChange={v => setConfig({ ...config, formality: v as any })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="formal">Formal</SelectItem>
                <SelectItem value="semi_formal">Semi Formal</SelectItem>
                <SelectItem value="informal">Informal</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">{t("format.metric_voice")}</Label>
            <Select value={config.voice} onValueChange={v => setConfig({ ...config, voice: v as any })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="passive">Passive</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-1.5">
            <Label className="text-xs">Min. Kata</Label>
            <Input type="number" value={config.min_word_count} onChange={e => setConfig({ ...config, min_word_count: Number(e.target.value) })} />
          </div>
          
          <div className="space-y-1.5">
            <Label className="text-xs">Maks. Kata</Label>
            <Input type="number" value={config.max_word_count} onChange={e => setConfig({ ...config, max_word_count: Number(e.target.value) })} />
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">{t("format.metric_numbering")}</Label>
            <Select value={config.numbering_style} onValueChange={v => setConfig({ ...config, numbering_style: v as any })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="numeric">Angka (1, 1.1)</SelectItem>
                <SelectItem value="roman">Romawi (I, A)</SelectItem>
                <SelectItem value="none">Tanpa Nomor</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs">Instruksi Kustom</Label>
          <Textarea 
             value={config.custom_instructions} 
             onChange={e => setConfig({ ...config, custom_instructions: e.target.value })} 
             rows={3} 
             placeholder="Contoh: Selalu gunakan awalan bismillah." 
          />
        </div>
      </div>

      <div className="border-t border-border" />

      {/* 3. Edit Seksi */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold">{t("format.sections_title")}</h4>
        
        {sections.map((sec, i) => (
          <details key={i} className="border border-border rounded-lg bg-background overflow-hidden marker:hidden" open={i === 0}>
            <summary className="px-4 py-3 cursor-pointer font-medium text-sm flex items-center bg-muted/30 hover:bg-muted/50 transition">
              Seksi {i + 1}: <span className="ml-1 text-primary">{sec.title}</span>
            </summary>
            <div className="p-4 space-y-4 border-t border-border">
              <div className="space-y-2">
                <Label className="text-xs">Judul Seksi</Label>
                <Input value={sec.title} onChange={e => updateSection(i, 'title', e.target.value)} />
              </div>
              
              <div className="space-y-2">
                <Label className="text-xs">Instruksi untuk AI</Label>
                <Textarea value={sec.description} onChange={e => updateSection(i, 'description', e.target.value)} rows={2} />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center space-x-2 pt-1 md:pt-6">
                  <Checkbox 
                     id={`req-${i}`} 
                     checked={sec.required} 
                     onCheckedChange={(c) => updateSection(i, 'required', !!c)} 
                  />
                  <Label htmlFor={`req-${i}`} className="text-xs cursor-pointer">Wajib Ada di Dokumen</Label>
                </div>
                
                <div className="space-y-1.5">
                  <Label className="text-xs">Min. Paragraf</Label>
                  <Input 
                     type="number" 
                     value={sec.min_paragraphs} 
                     onChange={e => updateSection(i, 'min_paragraphs', Number(e.target.value))} 
                  />
                </div>
              </div>
            </div>
          </details>
        ))}
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="pt-2 flex justify-end">
        <Button onClick={handleSubmit} disabled={saving || !name.trim()}>
          {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
          {t("format.save_changes")}
        </Button>
      </div>
    </div>
  );
}
