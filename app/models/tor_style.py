from pydantic import BaseModel, Field
from typing import Literal

class TORSection(BaseModel):
    """Satu seksi dalam dokumen TOR."""
    id: str
    title: str
    heading_level: int = 2
    required: bool = True
    description: str = ""
    min_paragraphs: int = 1
    subsections: list[str] = Field(default_factory=list)
    format_hint: Literal["paragraphs", "bullet_points", "table", "mixed", ""] = ""

class TORStyleConfig(BaseModel):
    """Konfigurasi gaya penulisan TOR."""
    language: Literal["id", "en"] = "id"
    formality: Literal["formal", "semi_formal", "informal"] = "formal"
    voice: Literal["active", "passive"] = "active"
    perspective: Literal["first_person", "third_person"] = "third_person"
    min_word_count: int = 500
    max_word_count: int = 3000
    numbering_style: Literal["numeric", "roman", "none"] = "numeric"
    custom_instructions: str = ""

class TORStyle(BaseModel):
    """Definisi lengkap satu TOR style."""
    id: str
    name: str
    description: str = ""
    is_default: bool = False
    is_active: bool = False
    created_at: str
    updated_at: str
    source: Literal["manual", "extracted", "default"] = "manual"
    source_filename: str | None = None

    sections: list[TORSection]
    config: TORStyleConfig

    def to_prompt_spec(self) -> str:
        """Serialize menjadi string instruksi siap inject ke prompt."""
        spec_lines = [
            "## FORMAT DOKUMEN TOR (WAJIB DIIKUTI)",
            "",
            "Gunakan TEPAT struktur berikut dalam urutan ini:",
            ""
        ]

        # 1. Iterate over sections
        for idx, section in enumerate(self.sections, start=1):
            heading_prefix = "#" * section.heading_level
            spec_lines.append(f"### Seksi {idx}: {section.title} (heading: {heading_prefix} {section.title})")
            
            req_str = "WAJIB ada" if section.required else "Opsional"
            spec_lines.append(f"- {req_str}")
            
            if section.min_paragraphs > 0:
                spec_lines.append(f"- Minimal {section.min_paragraphs} paragraf")
            
            if section.subsections:
                subs = ", ".join(section.subsections)
                spec_lines.append(f"- Sub-heading: {subs}")
                
            if section.format_hint:
                format_map = {
                    "paragraphs": "naratif paragraf",
                    "bullet_points": "bullet points",
                    "table": "tabel",
                    "mixed": "campuran (paragraf + bullet points/tabel)"
                }
                format_desc = format_map.get(section.format_hint, section.format_hint)
                spec_lines.append(f"- Format: {format_desc}")
                
            if section.description:
                spec_lines.append(f"- Instruksi: {section.description}")
                
            spec_lines.append("") # padding after section

        # 2. Iterate over config
        spec_lines.extend([
            "## GAYA PENULISAN (WAJIB DIIKUTI)",
            f"- Bahasa: {'Indonesia' if self.config.language == 'id' else 'Inggris'}",
            f"- Formalitas: {self.config.formality.replace('_', ' ').title()}",
            f"- Kalimat: {'Aktif' if self.config.voice == 'active' else 'Pasif'}",
            f"- Sudut pandang: {'Orang ketiga' if self.config.perspective == 'third_person' else 'Orang pertama'}",
        ])

        num_style = "Numerik (1. 2. 3.)"
        if self.config.numbering_style == "roman":
            num_style = "Romawi (I. II. III.)"
        elif self.config.numbering_style == "none":
            num_style = "Tanpa penomoran"
            
        spec_lines.append(f"- Penomoran: {num_style}")
        spec_lines.append(f"- Panjang dokumen: Minimal {self.config.min_word_count} kata, maksimal {self.config.max_word_count} kata")
        
        if self.config.custom_instructions:
            spec_lines.append(f"- Instruksi tambahan: {self.config.custom_instructions}")
            
        spec_lines.append("")

        return "\n".join(spec_lines)
