import json
import logging

from app.ai.base import BaseLLMProvider
from app.agents.agent_context import AgentContext, AgentResult, AgentType
from app.agents.base_agent import BaseAgent

logger = logging.getLogger("ai-agent-hybrid.agent.writer")

WRITER_SYSTEM_PROMPT = """Kamu adalah Writer Agent yang bertugas menulis dokumen TOR (Term of Reference) profesional.

Gunakan data yang diberikan untuk membuat TOR yang lengkap, formal, dan siap pakai.

## STRUKTUR TOR
1. **Latar Belakang** — Konteks, urgensi, dan relevansi kegiatan
2. **Tujuan** — Tujuan umum dan tujuan khusus
3. **Ruang Lingkup** — Cakupan pekerjaan
4. **Output/Deliverable** — Hasil yang diharapkan
5. **Timeline Pelaksanaan** — Jadwal
6. **Estimasi Biaya** (jika ada data) — Perkiraan anggaran
7. **Penutup**

## ATURAN
- Bahasa Indonesia formal
- Format Markdown
- Jika data kurang, gunakan asumsi masuk akal dan tandai [ASUMSI]
- Minimal 300 kata
- Jangan gunakan placeholder kosong

Langsung tulis dokumen TOR, tanpa tambahan di luar dokumen."""

REVISE_SYSTEM_PROMPT = """Kamu adalah Writer Agent yang bertugas merevisi dokumen TOR.

TOR SAAT INI:
{existing_tor}

PERMINTAAN REVISI:
{revision_request}

Buat TOR yang sudah direvisi sesuai permintaan. Format Markdown, bahasa Indonesia formal."""


class WriterAgent(BaseAgent):
    name = "writer"
    description = "Tulis dan revisi dokumen TOR"
    system_prompt = WRITER_SYSTEM_PROMPT

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def process(self, context: AgentContext) -> AgentResult:
        try:
            messages = self.build_messages(context)
            raw = await self.provider.chat(messages)
            content = raw.get("content", "")

            return AgentResult(
                agent=AgentType.WRITER,
                tor_content=content,
                message="TOR berhasil dibuat.",
                confidence=0.9,
            )
        except Exception as e:
            logger.error(f"Writer agent failed: {e}")
            return AgentResult(
                agent=AgentType.WRITER,
                message="Maaf, gagal membuat TOR. Silakan coba lagi.",
                confidence=0.0,
                error=str(e)[:500],
            )

    def build_messages(self, context: AgentContext) -> list[dict]:
        if context.generated_tor and self._is_revision_request(context):
            prompt = REVISE_SYSTEM_PROMPT.format(
                existing_tor=context.generated_tor[:2000],
                revision_request=context.user_message or "",
            )
            return [
                {"role": "system", "content": prompt},
            ]
        prompt = self._build_generate_prompt(context)
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

    def _build_generate_prompt(self, context: AgentContext) -> str:
        data_json = context.extracted_data.model_dump_json(indent=2, exclude_none=True)
        filled = context.extracted_data.filled_fields()
        missing = context.extracted_data.missing_fields()

        parts = [
            "## Data TOR",
            data_json,
            "",
            f"Field terisi: {filled}",
            f"Field belum terisi: {missing} (isi dengan asumsi jika perlu)",
        ]

        if context.rag_context:
            parts.extend([
                "",
                "## Referensi Tambahan",
                context.rag_context[:1000],
            ])

        if context.user_message:
            parts.extend([
                "",
                "## Instruksi Tambahan dari User",
                context.user_message,
            ])

        return "\n".join(parts)

    def _is_revision_request(self, context: AgentContext) -> bool:
        msg = (context.user_message or "").lower()
        keywords = ["revisi", "ubah", "tambah", "kurang", "edit", "perbaiki",
                     "ganti", "update", "koreksi", "betulin"]
        return any(k in msg for k in keywords)
