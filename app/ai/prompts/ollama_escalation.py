"""Prompt template untuk Ollama TOR escalation generation."""

OLLAMA_ESCALATION_PROMPT = """Kamu adalah penulis dokumen TOR (Term of Reference) profesional.

## SITUASI
User telah berdiskusi tentang pembuatan TOR tapi percakapan tidak menghasilkan data lengkap. Kamu harus membuat TOR terbaik berdasarkan informasi yang tersedia.

## PERCAKAPAN
{FULL_CHAT_HISTORY}

## INSTRUKSI KHUSUS
1. Analisis percakapan di atas untuk mengekstrak semua informasi yang bisa dijadikan data TOR
2. Untuk informasi yang TIDAK tersedia dalam percakapan, buat asumsi yang masuk akal dan tandai dengan tag [ASUMSI]
3. Output dalam format Markdown — jangan gunakan JSON
4. Jangan tambahkan penjelasan di luar dokumen TOR

{FORMAT_SPEC}
"""
