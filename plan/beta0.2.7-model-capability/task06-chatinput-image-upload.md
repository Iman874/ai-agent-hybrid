# Task 6: Frontend — ChatInput Image Upload UI

## Deskripsi

Menambahkan tombol upload gambar dan preview strip ke `ChatInput.tsx`, serta membuat komponen `ImagePreviewStrip.tsx` baru.

## Tujuan Teknis

- Tombol attachment (ikon `ImagePlus`) yang muncul/hilang berdasarkan `activeCapabilities.supports_image_input`
- File picker `accept="image/*"` dengan multi-select (max 4 gambar)
- Preview strip thumbnail di atas textarea
- Convert `File[]` → `base64[]` saat kirim
- Komponen `ImagePreviewStrip` reusable

## Scope

**Dikerjakan:**
- Update `app_frontend/src/components/chat/ChatInput.tsx`
- Buat `app_frontend/src/components/chat/ImagePreviewStrip.tsx` (baru)

**Tidak dikerjakan:**
- MessageBubble image render (Task 7)
- ModelSelector badges (Task 8)

## Langkah Implementasi

### Step 1: Buat `ImagePreviewStrip.tsx`

File: `app_frontend/src/components/chat/ImagePreviewStrip.tsx`

```tsx
import { X } from "lucide-react";

interface Props {
  images: File[];
  onRemove: (index: number) => void;
}

export function ImagePreviewStrip({ images, onRemove }: Props) {
  if (images.length === 0) return null;

  return (
    <div className="flex gap-2 px-3 pt-3 pb-1 overflow-x-auto">
      {images.map((file, i) => (
        <div key={i} className="relative flex-shrink-0 group">
          <img
            src={URL.createObjectURL(file)}
            alt={file.name}
            className="w-14 h-14 rounded-lg object-cover border border-border"
          />
          <button
            type="button"
            onClick={() => onRemove(i)}
            className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-destructive text-destructive-foreground rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <X className="w-3 h-3" />
          </button>
          <span className="text-[0.55rem] text-muted-foreground truncate block w-14 text-center mt-0.5">
            {file.name.length > 8 ? file.name.slice(0, 8) + "…" : file.name}
          </span>
        </div>
      ))}
    </div>
  );
}
```

### Step 2: Update `ChatInput.tsx`

```tsx
import { useState, useRef, useEffect } from "react";
import { Send, Loader2, ImagePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";
import { useModelStore } from "@/stores/model-store";
import { useTranslation } from "@/i18n";
import { ImagePreviewStrip } from "./ImagePreviewStrip";

const MAX_IMAGES = 4;

export function ChatInput() {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const [images, setImages] = useState<File[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sendMessage = useChatStore(s => s.sendMessage);
  const isStreaming = useChatStore(s => s.stream.isStreaming);
  const activeSessionId = useSessionStore(s => s.activeSessionId);
  const supportsImage = useModelStore(s => s.activeCapabilities?.supports_image_input ?? false);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }
  }, [text]);

  // Cleanup object URLs saat images berubah
  useEffect(() => {
    return () => {
      // Revoke saat component unmount atau images clear
    };
  }, [images]);

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Hapus prefix "data:image/...;base64,"
        const base64 = result.split(",")[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleSend = async () => {
    if ((!text.trim() && images.length === 0) || isStreaming) return;

    // Convert images ke base64
    let base64Images: string[] | undefined;
    if (images.length > 0) {
      base64Images = await Promise.all(images.map(fileToBase64));
    }

    sendMessage(text.trim(), activeSessionId, base64Images);
    setText("");
    setImages([]);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const remaining = MAX_IMAGES - images.length;
    const toAdd = files.slice(0, remaining);
    setImages(prev => [...prev, ...toAdd]);
    
    // Reset input agar bisa select file yang sama lagi
    e.target.value = "";
  };

  const handleRemoveImage = (index: number) => {
    setImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 bg-background px-4 sm:px-8 max-w-4xl mx-auto w-full">
      <div className="relative shadow-sm rounded-xl border bg-background focus-within:ring-1 focus-within:ring-ring transition-shadow">
        {/* Image preview strip */}
        <ImagePreviewStrip images={images} onRemove={handleRemoveImage} />

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={handleFileSelect}
        />

        <div className="flex items-end">
          {/* Tombol attachment — hanya jika model support image */}
          {supportsImage && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 ml-2 mb-2 text-muted-foreground hover:text-foreground flex-shrink-0"
              onClick={() => fileInputRef.current?.click()}
              disabled={images.length >= MAX_IMAGES || isStreaming}
            >
              <ImagePlus className="w-4 h-4" />
            </Button>
          )}

          <Textarea
            ref={textareaRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t("chat.input_placeholder")}
            className="min-h-[52px] max-h-[200px] resize-none pr-12 border-0 focus-visible:ring-0 shadow-none rounded-xl py-3.5 text-[0.95rem] leading-relaxed"
            rows={1}
          />

          <div className="absolute right-2 bottom-2">
            <Button
              size="icon"
              className="h-8 w-8 rounded-lg"
              onClick={handleSend}
              disabled={(!text.trim() && images.length === 0) || isStreaming}
            >
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4 ml-0.5" />
              )}
            </Button>
          </div>
        </div>
      </div>
      <p className="text-center text-[0.65rem] text-muted-foreground mt-2">
        {t("chat.disclaimer")}
      </p>
    </div>
  );
}
```

## Output yang Diharapkan

**Model vision (Gemini) dipilih:**
```
┌─────────────────────────────────────────────────────┐
│ [img1 ✕] [img2 ✕]                                  │
├─────────────────────────────────────────────────────┤
│ [📎] Jelaskan gambar ini...                  [Send] │
└─────────────────────────────────────────────────────┘
```

**Model text-only (Ollama qwen) dipilih:**
```
┌─────────────────────────────────────────────────────┐
│ Ketik pesan...                               [Send] │
└─────────────────────────────────────────────────────┘
```
(Tombol 📎 tidak muncul)

## Dependencies

- Task 5: `activeCapabilities` di model-store harus sudah ada

## Acceptance Criteria

- [ ] `ImagePreviewStrip.tsx` dibuat dan berfungsi
- [ ] Tombol `ImagePlus` muncul jika `supports_image_input === true`
- [ ] Tombol tersembunyi jika `supports_image_input === false`
- [ ] File picker hanya menerima image files
- [ ] Max 4 gambar per pesan
- [ ] Preview thumbnail 56x56 rounded
- [ ] Tombol ✕ untuk hapus gambar individual
- [ ] `File[]` → `base64[]` conversion saat kirim
- [ ] Send disabled jika tidak ada text DAN tidak ada images
- [ ] Send enabled jika ada images saja (tanpa text) — opsional
- [ ] `npm run build` clean

## Estimasi

Medium (2-3 jam)
