import json
import logging
import re

from app.ai.base import BaseLLMProvider
from app.agents.agent_context import AgentContext, AgentResult, AgentType
from app.agents.base_agent import BaseAgent
from app.models.tor import TORData

logger = logging.getLogger("ai-agent-hybrid.agent.interviewer")

INTERVIEWER_SYSTEM_PROMPT = """Kamu adalah Interviewer Agent yang bertugas mengumpulkan data untuk membuat dokumen TOR (Term of Reference).

Tugasmu HANYA menggali informasi — JANGAN membuat TOR atau menentukan kapan generate.

Data yang harus dikumpulkan:
Field WAJIB:
- judul: Nama/judul kegiatan
- latar_belakang: Alasan dan konteks mengapa kegiatan ini diperlukan
- tujuan: Apa yang ingin dicapai dari kegiatan ini
- ruang_lingkup: Cakupan kegiatan (durasi, peserta, lokasi, dll)
- output: Hasil/deliverable yang diharapkan
- timeline: Jadwal pelaksanaan

Field OPSIONAL:
- estimasi_biaya: Perkiraan anggaran

ATURAN INTERAKSI:
1. Mulai dengan menyapa dan bertanya tentang kegiatan umum
2. Tanyakan MAKSIMAL 2-3 pertanyaan per turn
3. Jangan tanya ulang field yang sudah terisi
4. Gunakan bahasa Indonesia yang sopan dan profesional

Output HARUS JSON (tanpa teks lain):
{
    "message": "Pesan natural ke user (pertanyaan lanjutan atau konfirmasi)",
    "extracted_so_far": {
        "judul": "..." atau null,
        "latar_belakang": "..." atau null,
        "tujuan": "..." atau null,
        "ruang_lingkup": "..." atau null,
        "output": "..." atau null,
        "timeline": "..." atau null,
        "estimasi_biaya": "..." atau null
    },
    "missing_fields": ["field1", "field2"],
    "confidence": 0.0-1.0
}"""


class InterviewerAgent(BaseAgent):
    name = "interviewer"
    description = "Gali data TOR dari user"
    system_prompt = INTERVIEWER_SYSTEM_PROMPT

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def process(self, context: AgentContext) -> AgentResult:
        try:
            messages = self.build_messages(context)
            raw = await self.provider.chat(messages)
            content = raw.get("content", "")

            parsed = self._parse_response(content)
            data = TORData(**parsed.get("extracted_so_far", {}))
            missing = parsed.get("missing_fields", context.missing_fields)

            return AgentResult(
                agent=AgentType.INTERVIEWER,
                message=parsed.get("message", ""),
                data=data,
                confidence=parsed.get("confidence", 0.5),
            )
        except Exception as e:
            logger.error(f"Interviewer agent failed: {e}")
            return AgentResult(
                agent=AgentType.INTERVIEWER,
                message="Maaf, saya mengalami kesulitan memproses pesan Anda. Bisa diulangi?",
                data=context.extracted_data,
                confidence=0.0,
                error=str(e)[:500],
            )

    def build_messages(self, context: AgentContext) -> list[dict]:
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]

        if context.rag_context:
            messages.append({
                "role": "system",
                "content": f"## Referensi\n{context.rag_context}",
            })

        if context.conversation_history:
            for msg in context.conversation_history[-20:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        messages.append({
            "role": "user",
            "content": context.user_message or "",
        })

        return messages

    def _parse_response(self, content: str) -> dict:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(pattern, cleaned, re.DOTALL)
        for match in sorted(matches, key=len, reverse=True):
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        return {"message": content[:500], "extracted_so_far": {}, "missing_fields": [], "confidence": 0.0}
