import { useState, useRef, useEffect, ChangeEvent } from "react";
import { Send, Loader2, Image as ImageIcon, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";
import { useModelStore } from "@/stores/model-store";
import { useTranslation } from "@/i18n";

export function ChatInput() {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const [images, setImages] = useState<string[]>([]); // base64 images tanpa header
  const [previews, setPreviews] = useState<string[]>([]); // base64 images dengan header untuk preview
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Use specific selectors to avoid re-renders
  const sendMessage = useChatStore(s => s.sendMessage);
  const isStreaming = useChatStore(s => s.stream.isStreaming);
  const activeSessionId = useSessionStore(s => s.activeSessionId);
  const activeCapabilities = useModelStore(s => s.activeCapabilities);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    // Reset to single-row first so scrollHeight reflects actual content
    el.style.height = "0px";
    const newHeight = text.trim() ? Math.min(el.scrollHeight, 200) : 52;
    el.style.height = newHeight + "px";
  }, [text]);

  const handleSend = () => {
    if ((!text.trim() && images.length === 0) || isStreaming) return;
    sendMessage(text.trim(), activeSessionId, images.length > 0 ? images : undefined);
    setText("");
    setImages([]);
    setPreviews([]);
    
    // Reset height
    if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    // Limit to max 3 images
    const currentCount = images.length;
    const allowedNewCount = 3 - currentCount;
    const filesToProcess = Array.from(files).slice(0, allowedNewCount);

    filesToProcess.forEach(file => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const result = event.target?.result as string;
        if (result) {
          // result format: data:image/jpeg;base64,/9j/4AAQSkZJRg...
          setPreviews(prev => [...prev, result]);
          
          // Pisahkan header untuk dikirim ke backend
          const base64Data = result.split(',')[1];
          setImages(prev => [...prev, base64Data]);
        }
      };
      reader.readAsDataURL(file);
    });

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const clearImage = (index: number) => {
    setImages(prev => prev.filter((_, i) => i !== index));
    setPreviews(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="p-4 bg-background px-4 sm:px-8 max-w-4xl mx-auto w-full">
      <div className="relative shadow-sm rounded-xl border bg-background focus-within:ring-1 focus-within:ring-ring transition-shadow flex flex-col">
        {/* Strip Image Preview */}
        {previews.length > 0 && (
          <div className="flex gap-2 p-3 pb-0 overflow-x-auto">
            {previews.map((preview, idx) => (
              <div key={idx} className="relative group shrink-0">
                <img 
                  src={preview} 
                  alt="upload preview" 
                  className="h-16 w-16 object-cover rounded-md border"
                />
                <button
                  type="button"
                  onClick={() => clearImage(idx)}
                  className="absolute -top-2 -right-2 bg-destructive text-destructive-foreground rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        <Textarea
          ref={textareaRef}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t("chat.input_placeholder")}
          className="!min-h-0 h-[52px] max-h-[200px] resize-none pr-20 pl-4 border-0 focus-visible:ring-0 shadow-none rounded-xl py-3.5 text-[0.95rem] leading-relaxed"
          rows={1}
        />
        
        <div className="absolute right-2 bottom-2 flex items-center gap-1">
          {/* Tombol Upload Gambar kondisional */}
          {activeCapabilities.supports_image_input && (
            <>
              <input 
                type="file" 
                ref={fileInputRef}
                className="hidden" 
                accept="image/jpeg,image/png,image/gif,image/webp"
                multiple
                onChange={handleFileChange}
                disabled={isStreaming || images.length >= 3}
              />
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 rounded-lg text-muted-foreground hover:text-foreground"
                onClick={() => fileInputRef.current?.click()}
                disabled={isStreaming || images.length >= 3}
                title={images.length >= 3 ? "Maksimal 3 gambar" : "Unggah gambar"}
              >
                <ImageIcon className="w-5 h-5" />
              </Button>
            </>
          )}

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
      <p className="text-center text-[0.65rem] text-muted-foreground mt-2">
        {t("chat.disclaimer")}
      </p>
    </div>
  );
}
