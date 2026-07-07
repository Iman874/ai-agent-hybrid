import json
import logging

from app.ai.base import BaseLLMProvider
from app.agents.agent_context import AgentContext, AgentResult, AgentType
from app.agents.base_agent import BaseAgent

logger = logging.getLogger("ai-agent-hybrid.agent.supervisor")

SUPERVISOR_SYSTEM_PROMPT = """Kamu adalah Supervisor Agent yang mengoordinasikan pembuatan dokumen TOR (Term of Reference).

Tugasmu:
1. Analisis input user + state session + riwayat percakapan
2. Tentukan action terbaik dari pilihan berikut

PILIHAN ACTION:
- INTERVIEW: Data TOR belum lengkap, perlu menggali informasi lebih lanjut dari user
- GENERATE: Semua field wajib TOR sudah terisi dengan cukup detail, siap untuk dibuat dokumen
- REVISE: User meminta revisi/ perubahan pada TOR yang sudah ada
- CLARIFY: Input user tidak jelas/ambigu, perlu klarifikasi sebelum bisa lanjut

FIELD WAJIB TOR:
- judul: Nama/judul kegiatan
- latar_belakang: Alasan dan konteks kegiatan
- tujuan: Apa yang ingin dicapai
- ruang_lingkup: Cakupan kegiatan
- output: Hasil/deliverable yang diharapkan
- timeline: Jadwal pelaksanaan

FIELD OPSIONAL:
- estimasi_biaya: Perkiraan anggaran

ATURAN:
- Jika user berkata "karang saja", "buatkan saja", "isi asumsi", atau setara → GENERATE (anggap user izin data dikarang)
- Jika user meminta revisi dan TOR sudah ada → REVISE
- Jika data belum lengkap dan user tidak memberikan izin asumsi → INTERVIEW
- Jika input tidak jelas → CLARIFY

Output HARUS JSON (tanpa teks lain):
{
    "decision": "INTERVIEW | GENERATE | REVISE | CLARIFY",
    "reason": "Penjelasan singkat kenapa ambil keputusan ini"
}"""


class SupervisorAgent(BaseAgent):
    name = "supervisor"
    description = "Koordinasi agent dan tentukan next action"
    system_prompt = SUPERVISOR_SYSTEM_PROMPT

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def process(self, context: AgentContext) -> AgentResult:
        try:
            messages = self.build_messages(context)
            raw = await self.provider.chat(messages)
            content = raw.get("content", "")

            decision = self._parse_decision(content)
            return AgentResult(
                agent=AgentType.SUPERVISOR,
                decision=decision["decision"],
                message=decision.get("reason", ""),
                confidence=0.9,
            )
        except Exception as e:
            logger.error(f"Supervisor agent failed: {e}")
            return AgentResult(
                agent=AgentType.SUPERVISOR,
                decision="INTERVIEW",
                message=str(e)[:200],
                confidence=0.3,
                error=str(e)[:500],
            )

    def build_messages(self, context: AgentContext) -> list[dict]:
        prompt = self._build_prompt(context)
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

    def _build_prompt(self, context: AgentContext) -> str:
        filled = context.extracted_data.filled_fields()
        missing = context.extracted_data.missing_fields()
        data_json = context.extracted_data.model_dump_json(indent=2)

        parts = [
            "## State Session Saat Ini",
            f"Turn: {context.turn_count}",
            f"Completeness: {context.completeness:.0%}",
            f"Filled fields: {filled}",
            f"Missing fields: {missing}",
            "",
            "## Data TOR Terkumpul",
            data_json,
        ]

        if context.conversation_summary:
            parts.extend([
                "",
                "## Ringkasan Percakapan",
                context.conversation_summary,
            ])

        if context.generated_tor:
            parts.extend([
                "",
                "## TOR yang Sudah Ada (untuk REVISE)",
                context.generated_tor[:500] + "...",
            ])

        parts.extend([
            "",
            "## Pesan User",
            context.user_message or "",
        ])

        return "\n".join(parts)

    def _parse_decision(self, content: str) -> dict:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        data = json.loads(cleaned.strip())
        decision = data.get("decision", "INTERVIEW")
        if decision not in ("INTERVIEW", "GENERATE", "REVISE", "CLARIFY"):
            raise ValueError(f"Unknown decision: {decision}")
        return {"decision": decision, "reason": data.get("reason", "")}
