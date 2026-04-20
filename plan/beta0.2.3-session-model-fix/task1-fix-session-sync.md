# Task 1: Fix Session ID Sync di finalizeStream

## 1. Judul Task
Sinkronisasi `session_id` dari response server ke `session-store` setelah pesan pertama berhasil dikirim.

## 2. Deskripsi
Saat ini `finalizeStream()` di `chat-store.ts` menerima response dari backend yang mengandung `session_id`, tetapi **tidak pernah menyimpan** session_id tersebut ke `session-store`. Akibatnya `activeSessionId` selalu `null`, dan setiap pesan berikutnya membuat session baru di server.

## 3. Tujuan Teknis
- `finalizeStream()` harus membaca `data.session_id` dari `HybridResponse`
- Jika `activeSessionId` saat ini `null` dan `data.session_id` ada, panggil `useSessionStore.getState().setActiveSession(data.session_id)`
- Setelah sync, panggil `useSessionStore.getState().fetchSessions()` agar sidebar ter-refresh

## 4. Scope
### Yang dikerjakan
- Modifikasi `finalizeStream()` di `src/stores/chat-store.ts`
- Import `useSessionStore` di file tersebut (sudah di-import sebagian untuk retry)

### Yang tidak dikerjakan
- Tidak mengubah backend
- Tidak mengubah session-store.ts (sudah punya `setActiveSession`)
- Tidak mengubah WebSocket flow (hanya HTTP fallback dulu)

## 5. Langkah Implementasi

### Step 1: Buka `src/stores/chat-store.ts`
Pastikan `useSessionStore` sudah di-import. Saat ini **tidak** di-import di top-level, hanya digunakan inline di `retryMessage`. Tambahkan import jika belum ada:

```typescript
import { useSessionStore } from "./session-store";
```

### Step 2: Modifikasi `finalizeStream()`
Setelah blok `set(state => { ... })`, tambahkan logika sync:

```typescript
finalizeStream: (data) => {
  set(state => {
    // ... existing logic tetap sama ...
  });

  // === TAMBAHAN BARU ===
  // Sync session_id dari server ke session-store
  const currentActiveId = useSessionStore.getState().activeSessionId;
  if (data.session_id && !currentActiveId) {
    useSessionStore.getState().setActiveSession(data.session_id);
    // Refresh sidebar agar session baru muncul
    useSessionStore.getState().fetchSessions();
  }
},
```

### Step 3: Verifikasi di browser
1. Buka React app
2. Kirim pesan pertama
3. Buka DevTools → Application → masuk ke Zustand state
4. Pastikan `activeSessionId` sudah terisi setelah response balik
5. Kirim pesan kedua → cek Network tab → request body harus mengandung `session_id` yang sama

## 6. Output yang Diharapkan

**Sebelum fix:**
```
Pesan 1 → session_id: null → server buat session "abc"
Pesan 2 → session_id: null → server buat session "def" (BUG!)
```

**Setelah fix:**
```
Pesan 1 → session_id: null → server buat session "abc" → sync ke store
Pesan 2 → session_id: "abc" → server lanjut session "abc" ✓
```

## 7. Dependencies
Tidak ada (task pertama)

## 8. Acceptance Criteria
- [ ] `finalizeStream()` memanggil `setActiveSession(data.session_id)` saat `activeSessionId` null
- [ ] `fetchSessions()` dipanggil setelah sync agar sidebar refresh
- [ ] Kirim 2 pesan berturutan → di Network tab, pesan ke-2 harus mengandung `session_id` yang sama dengan pesan pertama
- [ ] `npm run build` sukses tanpa error

## 9. Estimasi
**Low** (~30 menit)
