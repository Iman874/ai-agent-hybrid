CONTINUE_TOR_PROMPT = """# INSTRUKSI
Kamu sedang MELANJUTKAN pembuatan dokumen TOR (Term of Reference) yang terputus.

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
"""
