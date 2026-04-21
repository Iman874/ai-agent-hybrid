# Task 7: Frontend — MessageBubble Image Rendering

## Deskripsi

Update `MessageBubble.tsx` untuk merender gambar di dalam bubble chat user ketika pesan mengandung images.

## Tujuan Teknis

- Render gambar `<img>` di dalam bubble user sebelum teks
- Gambar ditampilkan sebagai rounded thumbnail dengan max-width
- Support multiple images dalam satu pesan (grid/flex layout)

## Scope

**Dikerjakan:**
- Update `app_frontend/src/components/chat/MessageBubble.tsx`

**Tidak dikerjakan:**
- Full-size image preview/lightbox (bisa di versi berikutnya)
- Assistant message image (AI tidak mengirim gambar)

## Langkah Implementasi

### Step 1: Update `MessageBubble.tsx`

Tambah rendering gambar di bagian atas bubble user:

```tsx
export const MessageBubble = memo(function MessageBubble({ message }: Props) {
  const { t } = useTranslation();
  const isUser = message.role === "user";
  const hasImages = message.images && message.images.length > 0;

  return (
    <div className={cn("flex gap-3 py-4", isUser ? "justify-end" : "justify-start")}>
      {/* Bot avatar (existing) */}
      {!isUser && ( ... )}

      <div className={cn(
        "max-w-[85%] sm:max-w-[80%] rounded-2xl px-5 py-3.5 shadow-sm min-w-0 box-border text-sm overflow-hidden",
        isUser ? "bg-primary text-primary-foreground" :
        message.status === "error" ? "bg-destructive/10 border-destructive/20 border text-destructive" :
        "bg-muted",
      )}>
        {/* NEW: Image grid */}
        {hasImages && (
          <div className={cn(
            "mb-2 gap-1.5",
            message.images!.length === 1 ? "flex" : "grid grid-cols-2",
          )}>
            {message.images!.map((img, i) => (
              <img
                key={i}
                src={`data:image/jpeg;base64,${img}`}
                alt={`Attached image ${i + 1}`}
                className={cn(
                  "rounded-lg object-cover border border-white/20",
                  message.images!.length === 1
                    ? "max-w-[240px] max-h-[200px]"
                    : "w-full h-24 sm:h-32",
                )}
              />
            ))}
          </div>
        )}

        {/* Existing content rendering */}
        {message.status === "sending" ? (
          <div className="flex items-center gap-2 text-sm h-5">...</div>
        ) : message.status === "streaming" ? (
          <StreamingText text={message.content} />
        ) : (
          message.content && <MarkdownRenderer content={message.content} />
        )}

        {/* Error section (existing) */}
        {message.status === "error" && ( ... )}
      </div>

      {/* User avatar (existing) */}
      {isUser && ( ... )}
    </div>
  );
});
```

### Step 2: Handle edge case — image-only message (tanpa teks)

Jika user kirim hanya gambar tanpa teks, `content` bisa kosong. Pastikan:
- Bubble tetap render gambar
- Tidak ada blank space di bawah gambar jika content kosong:
  ```tsx
  {message.content && <MarkdownRenderer content={message.content} />}
  ```
  (Check `message.content` sebelum render, karena bisa string kosong)

### Step 3: Styling

- 1 gambar: fluid width, max 240px
- 2-4 gambar: grid 2 kolom, fixed height
- Border halus `border-white/20` pada user bubble (karena bg-primary)
- Rounded corners `rounded-lg`

## Output yang Diharapkan

**1 gambar + teks:**
```
                  ┌───────────────────────────┐
                  │ ┌───────────────────┐     │
                  │ │                   │     │
                  │ │   [foto.jpg]      │     │
                  │ │                   │     │
                  │ └───────────────────┘     │
                  │ Apa yang ada di gambar?   │
                  └───────────────────────────┘
```

**2 gambar + teks:**
```
                  ┌───────────────────────────┐
                  │ ┌──────┐ ┌──────┐         │
                  │ │ img1 │ │ img2 │         │
                  │ └──────┘ └──────┘         │
                  │ Bandingkan kedua gambar   │
                  └───────────────────────────┘
```

**Gambar saja (tanpa teks):**
```
                  ┌───────────────────────────┐
                  │ ┌───────────────────┐     │
                  │ │   [foto.jpg]      │     │
                  │ └───────────────────┘     │
                  └───────────────────────────┘
```

## Dependencies

- Task 5: `Message.images` field di type definition
- Task 6: Images disimpan di message saat send

## Acceptance Criteria

- [ ] Gambar dirender di dalam bubble user
- [ ] 1 gambar: fluid layout, max-width 240px
- [ ] 2-4 gambar: grid 2 kolom
- [ ] Image-only message (tanpa teks) render tanpa blank space
- [ ] Rounded corners pada gambar
- [ ] Tidak ada gambar di bubble assistant (AI tidak kirim gambar)
- [ ] Tidak ada regresi pada bubble tanpa gambar
- [ ] `npm run build` clean

## Estimasi

Low (1 jam)
