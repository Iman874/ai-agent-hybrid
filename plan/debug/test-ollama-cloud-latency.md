# Laporan Debug (Post-Mortem): Ollama Cloud Model Latency & Streaming

## Latar Belakang Masalah
Model Qwen 397B versi cloud (melalui REST proxy/Ollama lokal) berjalan sangat pelan (lebih dari 1 menit) saat digunakan di aplikasi Streamlit, padahal berjalan sangat cepat (1–3 detik) saat dipanggil via terminal / CMD (`ollama run`).

Dokumen ini mencatat seluruh eksperimen, penemuan *bug* teknis, dan kesimpulan arsitektur agar bisa menjadi rujukan saat akan melakukan refactor ke arsitektur *Streaming* di masa depan.

---

## 1. Temuan Bug Spesifik Saat Debugging

Selama percobaan mematikan "Thinking Mode" secara dinamis, kami menemukan masalah pada lapisan integrasi:

1. **Python Ollama SDK Belum Mendukung Parameter `think` (TypeError)**
   * **Masalah:** Saat kami mencoba memasukkan `chat_kwargs["think"] = False` ke `ollama.AsyncClient`, library melempar error `TypeError: chat() got an unexpected keyword argument 'think'`.
   * **Analisis:** Library `ollama-python` di *environment* belum mendapatkan jembatan abstraksi penuh untuk update terbaru API Ollama (walaupun core Ollama di server sudah mendukungnya).
   * **Solusi Workaround:** Kami mencoba melakukan manipulasi *prompt* dengan menambahkan instruksi `"/nothink "` langsung di depan `user_message`.

2. **Custom Cloud Provider Menolak Request Tanpa Batas Token (`num_predict: -1`)**
   * **Masalah:** Untuk memaksa keluarannya cepat, kami menyetel `num_predict = -1`. Backend melemparkan `Internal server error` yang pada log API tertulis: `ollama._types.ResponseError: max_tokens must be positive, got: -1 (status code: 400)`.
   * **Analisis:** Layanan proksi cloud memiliki lapisan validasi yang mencegah panjang output tak terhingga.
   * **Solusi:** Kami menghapus pemaksaan `-1` dari *payload* konfigurasi model.

---

## 2. Kesimpulan Inti: Mengapa Tetap Lambat Tanpa Thinking? 

Meskipun _workaround_ di atas menyelesaikan *error*, respons generasi teks tetap memakan waktu sekitar **40 - 60 detik**. Setelah dicoba mengeksekusi *raw test streaming pipeline* di terminal, berikut temuan utamanya:

1. **Kebohongan `/nothink` di API Cloud**
   Instruksi *nothink* kadang dihiraukan. Model Qwen berukuran raksasa tetap memproduksi `&lt;think&gt;...&lt;/think&gt;` token internal yang berjumlah ratusan kata di balik API sebelum mengeluarkan JSON.

2. **Perbedaan Mendasar Arsitektur (UX "Cepat" vs UX "Lambat")**
   * **Di CMD (Cepat 1-3 detik):** CMD menggunakan mekanisme **Streaming**. Model langsung melemparkan kata pertama ke layar begitu diproses (mulai membaca teks `<think>`). Otak manusia merasa seolah-olah "cepat" karena tidak ada titik kosong. Padahal total waktu menyelesaikannya tetap puluhan detik.
   * **Di Aplikasi Streamlit (Lambat 60 detik):** Arsitektur backend kita (`DecisionEngine`) mengandalkan `await provider.chat()`. Ini adalah pemanggilan fungsi **Blocking (Tidak Streaming)**. Frontend kita terpaksa membeku menunggu seluruh pemikiran (`think`) dan struktur JSON (`message`, `status`) dicetak secara penuh 100% dari awan. Setelah dikonfirmasi format JSON-nya benar via `ResponseParser`, barulah dikirimkan utuh ke UI secara serentak. Waktu kosong *freeze* ini yang membuat kesan lambat.

---

## 3. Catatan Untuk Eksekusi Masa Depan (Rencana Streaming Mode)

Sistem saat ini dituntut membalas dengan struktur kompleks seperti:
```json
{
  "status": "CHATTING",
  "missing_fields": ["latar_belakang", "tujuan"],
  "message": "Halo! Tentu saya bisa membantu..."
}
```

Jika fitur ini ingin dikerjakan di proyek selanjutnya, melakukan _streaming_ langsung ke UI menjadi hal yang sangat rumit karena Front-End tidak akan bisa membaca string "message" yang belum ditutup *kurung kurawal* atau *quote* JSON-nya. 

**Opsi Refactor Arsitektur yang Direkomendasikan Nanti:**
1. **Pisahkan LLM Parser dan Chatter:**
   Berikan tugas membalas sapaan chat biasa (`message` saja tanpa JSON) secara Streaming SSE. Sambil user membaca, *Agent / Tool* bekerja di *background* untuk mengekstrak data JSON tanpa mengganggu *loading text* dari _user interface_.
2. **Streaming JSON Parser:**
   Menggunakan *library* seperti `jiter` yang mampu mengekstrak nilai variabel `"message"` meski blok JSON baris selanjuntya belum ter-stream tuntas.
