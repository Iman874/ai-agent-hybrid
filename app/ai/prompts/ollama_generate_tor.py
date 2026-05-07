"""Prompt template untuk Ollama TOR standard generation."""

OLLAMA_STANDARD_PROMPT = """Kamu adalah penulis dokumen TOR (Term of Reference / Kerangka Acuan Kerja) profesional.

## TUGAS
Buatkan dokumen TOR yang lengkap, profesional, dan siap digunakan berdasarkan data berikut.

## DATA INPUT
{DATA_JSON}

## REFERENSI KONTEN (dari RAG, jika ada)
{RAG_EXAMPLES}

{FORMAT_SPEC}

## ATURAN PENTING
1. Output dalam format Markdown — jangan gunakan JSON
2. Jangan gunakan placeholder seperti [isi di sini] — isi dengan data yang ada
3. Jika ada data yang kurang, buat asumsi masuk akal dan tandai dengan [ASUMSI]
4. Jangan tambahkan penjelasan di luar dokumen TOR
5. Tulis langsung dokumen TOR-nya, tanpa kata pengantar

## STRUKTUR MINIMAL
- Judul Kegiatan
- Latar Belakang
- Tujuan
- Ruang Lingkup
- Output Kegiatan
- Timeline Pelaksanaan
"""
