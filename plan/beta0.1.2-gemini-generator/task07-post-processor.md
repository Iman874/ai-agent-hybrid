# Task 07 — PostProcessor: Validasi & Clean TOR Output

## 1. Judul Task

Implementasikan `PostProcessor` — class untuk validasi struktur TOR output, word count, check asumsi, dan clean formatting dari Gemini.

## 2. Deskripsi

Gemini bisa mengeluarkan output yang wrapped dalam code block, memiliki whitespace berlebih, atau missing sections. PostProcessor membersihkan dan memvalidasi output sebelum disimpan.

## 3. Tujuan Teknis

- `process(raw_tor) → ProcessedTOR` — single entry point
- `_clean_formatting()` — remove code block wrapper, normalize whitespace
- `_check_structure()` — cek keberadaan section ##1 s/d ##5 minimal
- `_count_words()` — hitung word count
- Check tag `[ASUMSI]` untuk flag `has_assumptions`

## 4. Scope

### Yang dikerjakan
- `app/core/post_processor.py` — class `PostProcessor`

### Yang tidak dikerjakan
- Reject/re-generate jika TOR kurang bagus (hanya warning log)

## 5. Langkah Implementasi

### Step 1: Buat `app/core/post_processor.py`

```python
import re
import logging
from app.models.generate import ProcessedTOR

logger = logging.getLogger("ai-agent-hybrid.gemini.postprocessor")


class PostProcessor:
    """Validasi dan clean output TOR dari Gemini."""

    EXPECTED_SECTIONS = [
        "Latar Belakang",
        "Tujuan",
        "Ruang Lingkup",
        "Output",
        "Timeline",
    ]
    MIN_WORD_COUNT = 300

    @staticmethod
    def process(raw_tor: str) -> ProcessedTOR:
        """Validate dan clean TOR output."""
        content = PostProcessor._clean_formatting(raw_tor)
        word_count = len(content.split())
        has_assumptions = "[ASUMSI]" in content
        missing_sections = PostProcessor._check_structure(content)

        if word_count < PostProcessor.MIN_WORD_COUNT:
            logger.warning(f"TOR pendek: {word_count} kata (min: {PostProcessor.MIN_WORD_COUNT})")

        if missing_sections:
            logger.warning(f"TOR missing sections: {missing_sections}")

        return ProcessedTOR(
            content=content,
            word_count=word_count,
            has_assumptions=has_assumptions,
            missing_sections=missing_sections,
        )

    @staticmethod
    def _clean_formatting(text: str) -> str:
        """Remove wrapping code blocks, normalize whitespace."""
        # Remove ```markdown ... ``` wrapper
        text = re.sub(r'^```(?:markdown)?\s*\n', '', text)
        text = re.sub(r'\n```\s*$', '', text)
        # Normalize multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def _check_structure(content: str) -> list[str]:
        """Check apakah semua expected sections ada."""
        missing = []
        for section in PostProcessor.EXPECTED_SECTIONS:
            if section.lower() not in content.lower():
                missing.append(section)
        return missing
```

### Step 2: Verifikasi

```python
from app.core.post_processor import PostProcessor

# Test 1: Clean formatting (remove code block wrapper)
raw = "```markdown\n# TOR\n\n## 1. Latar Belakang\nIni konten.\n```"
result = PostProcessor.process(raw)
assert not result.content.startswith("```")
assert not result.content.endswith("```")
print("Test 1: clean formatting OK")

# Test 2: Check structure
full_tor = """# TERM OF REFERENCE
## 1. Latar Belakang
Konteks kegiatan.
## 2. Tujuan
Meningkatkan kompetensi.
## 3. Ruang Lingkup
30 peserta ASN.
## 4. Output
Sertifikat.
## 5. Timeline
Juli 2026.
## 6. Estimasi Biaya
Rp 50 juta.
## 7. Penutup
Demikian."""
result2 = PostProcessor.process(full_tor)
assert result2.missing_sections == []
print("Test 2: structure check OK (no missing)")

# Test 3: Missing sections
partial = "# TOR\n\n## 1. Latar Belakang\nIni saja."
result3 = PostProcessor.process(partial)
assert "Tujuan" in result3.missing_sections
print(f"Test 3: missing sections = {result3.missing_sections}")

# Test 4: has_assumptions
asumsi_tor = "## 1. Latar Belakang\n[ASUMSI] Ini asumsi kami."
result4 = PostProcessor.process(asumsi_tor)
assert result4.has_assumptions is True
print("Test 4: has_assumptions OK")

# Test 5: word count
result5 = PostProcessor.process("satu dua tiga empat lima")
assert result5.word_count == 5
print("Test 5: word count OK")

print("ALL POST PROCESSOR TESTS PASSED")
```

## 6. Output yang Diharapkan

```
Test 1: clean formatting OK
Test 2: structure check OK (no missing)
Test 3: missing sections = ['Tujuan', 'Ruang Lingkup', 'Output', 'Timeline']
Test 4: has_assumptions OK
Test 5: word count OK
ALL POST PROCESSOR TESTS PASSED
```

## 7. Dependencies

- **Task 01** — `ProcessedTOR` model

## 8. Acceptance Criteria

- [ ] `process()` return `ProcessedTOR` dengan `content`, `word_count`, `has_assumptions`, `missing_sections`
- [ ] Code block wrapper (`\`\`\`markdown ... \`\`\``) ter-remove
- [ ] Multiple blank lines di-normalize ke max 2
- [ ] Deteksi `[ASUMSI]` tag dalam konten
- [ ] Section check mengembalikan list section yang missing
- [ ] Warning log jika word count < 300

## 9. Estimasi

**Low** — ~1 jam
