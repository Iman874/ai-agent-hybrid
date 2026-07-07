# Task 07 — Prompt Injection Fallback

## Deskripsi

Membangun mekanisme **fallback universal** untuk model yang **tidak mendukung native tool calling**. Tidak semua model Ollama (terutama model kecil < 3B parameters) mendukung parameter `tools` di chat API. Untuk model-model ini, kita menggunakan teknik **prompt injection** — deskripsi tool disisipkan langsung ke system prompt, dan LLM diminta mengeluarkan format teks khusus `[[TOOL_CALL: ...]]` jika ingin memanggil tool.

Ini adalah **safety net** yang memastikan Tool System bekerja di **semua model**, apapun kemampuannya.

---

## Tujuan Teknis

- Menyediakan fallback universal untuk model yang tidak support native tool calling
- Tool specs di-inject ke system prompt sebagai instruksi yang jelas
- LLM mengembalikan tool call dalam format teks `[[TOOL_CALL: name(args)]]` yang bisa diparsing
- Parser sudah dibuat di Task 04 (`ToolHandler.parse_prompt_injection()`)
- Prompt injection bisa dikombinasikan dengan system prompt yang sudah ada
- Prompt injection hanya aktif jika native tool calling tidak tersedia

---

## Scope

### Termasuk

- Membuat `app/ai/prompts/tool_injection.py`
- Template prompt yang mendeskripsikan tool ke LLM:

  **Struktur prompt:**
  ```
  Anda memiliki akses ke tool berikut:
  
  ## {tool_name}
  Deskripsi: {description}
  Parameter:
    - {param_name} ({type}, {required}): {description}
  
  CARA MENGGUNAKAN TOOL:
  Jika Anda membutuhkan informasi yang tidak Anda ketahui,
  KELUARKAN teks persis dengan format berikut:
  [[TOOL_CALL: tool_name(param1="value", param2="value")]]
  
  Setelah tool dieksekusi, hasilnya akan diberikan ke Anda.
  Gunakan hasil tersebut untuk merespon user.
  JANGAN pernah memanggil tool yang sama dua kali berturut-turut.
  HANYA panggil tool jika benar-benar membutuhkan informasi tambahan.
  ```

- Fungsi `build_tool_injection_prompt(tools_specs: list[ToolSpec]) -> str`:
  - Iterate semua tool specs
  - Format name, description, parameters ke template
  - Tambahkan instruksi cara menggunakan format `[[TOOL_CALL: ...]]`
  - Tambahkan aturan: jangan panggil tool yang sama dua kali
  - Return string lengkap siap di-inject ke system prompt

- Fungsi `has_native_tool_support(model_name: str, provider: str) -> bool`:
  - Cek apakah model mendukung native tool calling
  - Rules:
    - Gemini: selalu True (semua model support function calling)
    - Ollama: True untuk model >= 7B parameters (qwen2.5, llama3.2, mistral)
    - Ollama: False untuk model kecil (< 3B)
    - Unknown: False (fail-safe)
  - Pattern matching berdasarkan nama model

- Integrasi: prompt injection siap digunakan oleh `ChatService` (Task 08) ketika native tool calling tidak tersedia

### Tidak Termasuk

- Native tool calling (Task 05, 06)
- Tool execution loop (Task 04)
- Integrasi ke ChatService (Task 08)
- Parser untuk prompt injection (sudah di Task 04)

---

## Langkah Implementasi

### Langkah 1: Buat `app/ai/prompts/tool_injection.py`

```python
"""Prompt injection templates untuk tool calling fallback.

Untuk model yang tidak mendukung native tool calling (tools parameter),
kita inject deskripsi tool ke system prompt dan LLM mengembalikan
tool call dalam format [[TOOL_CALL: name(args)]].
"""

from typing import Any

from app.tools.base import ToolSpec

# Template untuk satu tool
TOOL_TEMPLATE = """
## {name}
Deskripsi: {description}
Parameter:
{parameters}

CARA MENGGUNAKAN:
[[TOOL_CALL: {name}(param1="value", param2="value")]]
"""

# Template untuk parameter
PARAM_TEMPLATE = '  - {name} ({type}{required_hint}): {description}'

# Instruksi global yang ditambahkan setelah daftar tool
TOOL_USAGE_INSTRUCTIONS = """
CARAMENGGUNAKAN TOOL:
Jika Anda membutuhkan informasi yang tidak Anda ketahui atau data real-time,
KELUARKAN teks persis dengan format berikut:
[[TOOL_CALL: nama_tool(param1="value", param2="value")]]

Contoh:
[[TOOL_CALL: web_search(query="AI Indonesia 2025", max_results=5)]]

ATURAN PENTING:
1. HANYA panggil tool jika benar-benar membutuhkan informasi tambahan.
2. JANGAN memanggil tool yang sama dua kali berturut-turut.
3. Setelah tool dieksekusi, hasilnya akan diberikan ke Anda.
4. Gunakan hasil tool untuk merespon user dengan informatif.
5. Jika tool gagal, gunakan pengetahuan yang Anda miliki.
6. JANGAN pernah memanggil tool hanya karena bisa — panggil hanya jika perlu.
"""


def build_tool_injection_prompt(tools_specs: list[ToolSpec]) -> str:
    """Bangun prompt injection untuk tool calling.

    Args:
        tools_specs: List spesifikasi tool yang akan di-inject.

    Returns:
        str: Prompt lengkap yang siap ditambahkan ke system prompt.

    Contoh:
        >>> specs = [ToolSpec(name="web_search", description="...", parameters={...})]
        >>> prompt = build_tool_injection_prompt(specs)
        >>> print(prompt)
        Anda memiliki akses ke tool berikut:
        ...
    """
    if not tools_specs:
        return ""

    lines = ["Anda memiliki akses ke tool berikut:\n"]

    for spec in tools_specs:
        lines.append(f"## {spec.name}")
        lines.append(f"Deskripsi: {spec.description}")
        lines.append("Parameter:")

        props = spec.parameters.get("properties", {})
        required = spec.parameters.get("required", [])

        for param_name, param_info in props.items():
            param_type = param_info.get("type", "string")
            param_desc = param_info.get("description", "")
            is_required = param_name in required
            required_hint = ", required" if is_required else ", optional"
            default = param_info.get("default", None)
            if default is not None:
                param_desc += f" (default: {default})"

            lines.append(PARAM_TEMPLATE.format(
                name=param_name,
                type=param_type,
                required_hint=required_hint,
                description=param_desc,
            ))

        # Contoh penggunaan
        example_params = []
        for param_name, param_info in props.items():
            param_type = param_info.get("type", "string")
            if param_type == "string":
                example_params.append(f'{param_name}="..."')
            elif param_type == "integer":
                example_params.append(f"{param_name}=5")
            elif param_type == "boolean":
                example_params.append(f"{param_name}=true")
            else:
                example_params.append(f'{param_name}="..."')

        lines.append(f'\nContoh:\n[[TOOL_CALL: {spec.name}({", ".join(example_params)})]]')
        lines.append("")

    lines.append(TOOL_USAGE_INSTRUCTIONS)

    return "\n".join(lines).strip()


def has_native_tool_support(model_name: str, provider: str) -> bool:
    """Cek apakah model mendukung native tool calling.

    Args:
        model_name: Nama model (contoh: "qwen2.5:7b-instruct", "gemini-2.0-flash").
        provider: Nama provider ("ollama" atau "google").

    Returns:
        bool: True jika model mendukung native tool calling.

    Rules:
        - Gemini: selalu True (semua model support function calling).
        - Ollama: True untuk model >= 7B parameters.
        - Ollama: False untuk model kecil (< 3B).
        - Unknown: False (fail-safe).
    """
    if provider == "google":
        return True

    if provider == "ollama":
        model_lower = model_name.lower()

        # Model yang dikenal support tools
        known_support = [
            "qwen2.5", "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b",
            "llama3.2", "llama3.2:3b",  # 3B juga support
            "llama3.1", "llama3.1:8b", "llama3.1:70b",
            "mistral", "mistral:7b", "mistral-nemo",
            "mixtral", "mixtral:8x7b",
            "command-r", "command-r:35b",
            "deepseek", "deepseek-coder",
            "phi-3", "phi-3:14b",
            "nemotron",
            "dbrx",
        ]

        # Model yang dikenal TIDAK support tools
        known_no_support = [
            "llama3.2:1b", "llama3.2:1b-instruct",
            "phi-3:mini", "phi-3:3.8b",
            "tinyllama", "tinylama",
            "gemma:2b", "gemma2:2b",
        ]

        for pattern in known_support:
            if pattern in model_lower:
                return True

        for pattern in known_no_support:
            if pattern in model_lower:
                return False

        # Fallback: jika model >= 7B, assume support
        # Parse parameter count dari model name
        import re
        param_match = re.search(r':(\d+)b', model_lower)
        if param_match:
            param_count = int(param_match.group(1))
            return param_count >= 3  # 3B ke atas support

        # Unknown model — fail-safe: False
        return False

    # Unknown provider — fail-safe
    return False
```

### Langkah 2: Validasi

```python
from app.tools.base import ToolSpec
from app.ai.prompts.tool_injection import build_tool_injection_prompt, has_native_tool_support


# Test build_tool_injection_prompt
specs = [
    ToolSpec(
        name="web_search",
        description="Cari informasi terbaru dari internet",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Kata kunci pencarian",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Jumlah hasil maksimal",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    )
]

prompt = build_tool_injection_prompt(specs)
print(prompt)
print("---")

# Test has_native_tool_support
assert has_native_tool_support("gemini-2.0-flash", "google") is True
assert has_native_tool_support("qwen2.5:7b-instruct", "ollama") is True
assert has_native_tool_support("llama3.2:1b", "ollama") is False
assert has_native_tool_support("unknown-model:1b", "ollama") is False
assert has_native_tool_support("unknown-provider", "unknown") is False

print("All validations passed!")
```

---

## Output yang Diharapkan

```
app/ai/prompts/
├── tool_injection.py     # Baru — prompt injection builder
└── ... (existing prompts)
```

- `build_tool_injection_prompt()` menghasilkan prompt yang jelas dan terstruktur
- `has_native_tool_support()` bisa membedakan model yang support native tool calling
- Prompt injection siap digunakan oleh ChatService

---

## Dependencies

- **Task 01 (Tool Abstraction)** — `ToolSpec`
- **Task 04 (Tool Handler)** — `parse_prompt_injection()` sebagai parser

---

## Acceptance Criteria

### Functional
- [ ] `build_tool_injection_prompt()` menerima list `ToolSpec` dan mengembalikan string
- [ ] Output prompt mencakup semua tool specs dengan format yang jelas
- [ ] Setiap tool memiliki: nama, deskripsi, daftar parameter, dan contoh penggunaan
- [ ] Parameter memiliki: nama, tipe, required/optional, deskripsi, default value
- [ ] Format `[[TOOL_CALL: ...]]` mudah diparsing oleh regex di Task 04
- [ ] Ada instruksi untuk tidak memanggil tool yang sama dua kali
- [ ] Ada instruksi untuk fallback ke pengetahuan sendiri jika tool gagal
- [ ] Prompt injection bisa ditambahkan ke system prompt yang sudah ada

### Native Tool Support Detection
- [ ] `has_native_tool_support("gemini-*", "google")` → True
- [ ] `has_native_tool_support("qwen2.5:7b", "ollama")` → True
- [ ] `has_native_tool_support("llama3.2:1b", "ollama")` → False
- [ ] `has_native_tool_support("unknown:1b", "ollama")` → False
- [ ] `has_native_tool_support("unknown", "unknown")` → False

### Edge Cases
- [ ] Empty list → return empty string
- [ ] Tool tanpa parameter → tetap tampil dengan "Parameter:" kosong
- [ ] Tool dengan banyak parameter → semua terformat dengan benar
- [ ] Model name dengan format tidak standar → fail-safe False

---

## Estimasi

**Low-Medium** (~1.5 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Implementasi build_tool_injection_prompt | 30 menit |
| Implementasi has_native_tool_support | 30 menit |
| Testing berbagai skenario model | 20 menit |
| Validasi & testing | 10 menit |
