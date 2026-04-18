from pydantic import BaseModel, Field
from typing import Literal

REQUIRED_FIELDS = ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
OPTIONAL_FIELDS = ["estimasi_biaya"]


class TORData(BaseModel):
    """Schema data TOR yang dikumpulkan selama chat."""
    judul: str | None = None
    latar_belakang: str | None = None
    tujuan: str | None = None
    ruang_lingkup: str | None = None
    output: str | None = None
    timeline: str | None = None
    estimasi_biaya: str | None = None

    def filled_fields(self) -> list[str]:
        """Return list field required yang sudah terisi."""
        return [f for f in REQUIRED_FIELDS if getattr(self, f) is not None]

    def missing_fields(self) -> list[str]:
        """Return list field required yang masih kosong."""
        return [f for f in REQUIRED_FIELDS if getattr(self, f) is None]


class LLMParsedResponse(BaseModel):
    """Schema respons JSON yang diharapkan dari local LLM."""
    status: Literal["NEED_MORE_INFO", "READY_TO_GENERATE", "ESCALATE_TO_GEMINI"]
    message: str
    data: TORData | None = None
    extracted_so_far: TORData | None = None
    partial_data: TORData | None = None
    missing_fields: list[str] | None = None
    reason: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
