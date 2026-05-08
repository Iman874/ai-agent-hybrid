"""Prompt template untuk Ollama document-to-TOR generation."""

OLLAMA_DOCUMENT_TO_TOR_PROMPT = """Kamu adalah penulis dokumen TOR (Term of Reference / Kerangka Acuan Kerja) profesional.

## TUGAS UTAMA
Berdasarkan DOKUMEN SUMBER yang diberikan di bawah, buat TOR yang lengkap dan profesional.

## LANGKAH KERJA
1. Baca dan pahami dokumen sumber secara menyeluruh
2. Identifikasi informasi kunci terkait TOR
3. Susun TOR dalam format yang direquest spesifiknya
4. Jika ada informasi kurang di dokumen, berikan catatan [ASUMSI] dan isi dengan estimasi wajar
5. Jika ada informasi yang bertentangan, gunakan yang paling logis

## KONTEKS TAMBAHAN DARI USER
{USER_CONTEXT}

## DOKUMEN SUMBER
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
5. Tulis langsung dokumen TOR-nya, tanpa kata pengantar
"""
