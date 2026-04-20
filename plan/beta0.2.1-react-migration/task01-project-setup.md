# Task 01: Project Setup — Vite + React + TypeScript + Tailwind + Shadcn

## 1. Judul Task

Scaffold project React dengan Vite, TypeScript, TailwindCSS, dan Shadcn UI

## 2. Deskripsi

Membuat folder `app_frontend` dengan setup lengkap: Vite sebagai bundler, React 18+, TypeScript strict mode, TailwindCSS v4, dan Shadcn UI sebagai component library. Termasuk install semua dependencies yang dibutuhkan.

## 3. Tujuan Teknis

- Folder `app_frontend/` siap digunakan
- `npm run dev` berjalan di port 5173
- Tailwind + dark mode berfungsi
- Shadcn UI ter-init dan siap pakai
- Semua core dependencies terinstall

## 4. Scope

**Yang dikerjakan:**
- `app_frontend/` — full scaffold
- Vite config
- Tailwind config + dark mode class strategy
- Shadcn UI init + install komponen dasar
- Base CSS tokens (warna, spacing, typography)

**Yang tidak dikerjakan:**
- Komponen aplikasi (task selanjutnya)
- API client (task 03)
- State management (task 04)

## 5. Langkah Implementasi

### 5.1 Create Vite Project

```bash
cd d:\Iman874\Documents\Github\ai-agent-hybrid
npx -y create-vite@latest app_frontend -- --template react-ts
cd app_frontend
npm install
```

### 5.2 Install Core Dependencies

```bash
# Styling
npm install -D tailwindcss @tailwindcss/vite

# State management
npm install zustand

# Routing
npm install react-router-dom

# Markdown rendering
npm install react-markdown remark-gfm rehype-highlight

# Icons
npm install lucide-react

# Utilities
npm install clsx tailwind-merge
```

### 5.3 Setup Tailwind

Update `vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

Update `src/index.css`:
```css
@import "tailwindcss";

@custom-variant dark (&:where(.dark, .dark *));
```

### 5.4 Setup Path Alias

Update `tsconfig.app.json`:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

Install path support:
```bash
npm install -D @types/node
```

Update `vite.config.ts` tambah resolve:
```typescript
import path from "path"

export default defineConfig({
  // ...existing
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
```

### 5.5 Setup Shadcn UI

```bash
npx shadcn@latest init
```

Pilih:
- Style: Default
- Base color: Slate
- CSS variables: Yes

Install komponen dasar:
```bash
npx shadcn@latest add button dialog dropdown-menu input scroll-area separator sheet skeleton tabs textarea tooltip
```

### 5.6 Setup `lib/utils.ts`

Shadcn sudah membuat file ini. Pastikan isinya:
```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### 5.7 Setup Constants

Buat `src/lib/constants.ts`:
```typescript
export const API_BASE_URL = "/api/v1";
export const WS_BASE_URL = `ws://${window.location.host}`;
export const APP_NAME = "Generator TOR";
export const APP_VERSION = "0.2.1";
```

### 5.8 Cleanup Boilerplate

- Hapus `src/App.css`
- Hapus konten default `src/App.tsx`
- Update `src/App.tsx` menjadi minimal:

```tsx
function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <h1 className="text-2xl p-8">Generator TOR v0.2.1</h1>
      <p className="px-8 text-muted-foreground">React migration in progress...</p>
    </div>
  )
}

export default App
```

## 6. Output yang Diharapkan

- `npm run dev` → browser di `http://localhost:5173`
- Tampil "Generator TOR v0.2.1" dengan Tailwind styling
- Dark mode class toggle berfungsi
- `@/` path alias berfungsi
- Shadcn components bisa di-import: `import { Button } from "@/components/ui/button"`

## 7. Dependencies

Tidak ada (task pertama)

## 8. Acceptance Criteria

- [ ] Folder `app_frontend/` ada di root project
- [ ] `npm run dev` berjalan tanpa error
- [ ] `npm run build` menghasilkan bundle tanpa TypeScript error
- [ ] Tailwind classes berfungsi (cek visual)
- [ ] Shadcn Button component bisa di-render
- [ ] Vite proxy ke `localhost:8000` terkonfigurasi
- [ ] Path alias `@/` berfungsi
- [ ] `constants.ts` ada dengan API_BASE_URL

## 9. Estimasi

Low (30-60 menit)
