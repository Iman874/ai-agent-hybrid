"""Prompt template untuk Ollama continue TOR generation."""

OLLAMA_CONTINUE_TOR_PROMPT = """Kamu sedang MELANJUTKAN pembuatan dokumen TOR (Term of Reference) yang terputus.

## TOR YANG SUDAH DIHASILKAN (JANGAN ULANGI INI)
---
{PARTIAL_TOR}
---

## TUGAS UTAMA
Lanjutkan penulisan TOR di atas TEPAT dari titik terakhir. 
JANGAN MENGULANGI bagian, kalimat, atau poin yang SUDAH TERTULIS di bagian atas.
Tulis HANYA kelanjutannya saja dan pastikan transisinya mengalir dengan alami.

## DOKUMEN SUMBER (UNTUK REFERENSI)
---
{DOCUMENT_TEXT}
---

{RAG_EXAMPLES}

{FORMAT_SPEC}

## ATURAN PENTING
1. Output dalam format Markdown — jangan gunakan JSON
2. Jangan gunakan placeholder seperti [isi di sini] — isi dengan data yang ada
3. Jika ada data yang kurang, buat asumsi masuk akal dan tandai dengan [ASUMSI]
4. Jangan tambahkan penjelasan di luar dokumen TOR
5. Tulis langsung kelanjutan TOR-nya, tanpa kata pengantar
"""
