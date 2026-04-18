# Task 02 — Config Update: Tambah Escalation & App Settings

## 1. Judul Task

Update `app/config.py` untuk menambahkan settings `app_version`, `app_env`, `escalation_max_idle_turns`, `escalation_absolute_max_turns`. Update `.env.example` dengan semua variable terbaru.

## 2. Deskripsi

Menambahkan beberapa settings yang dibutuhkan oleh API Layer: versi app untuk health check, environment flag untuk debug mode, dan escalation thresholds yang bisa di-override via env vars.

## 3. Tujuan Teknis

- Tambah `app_version`, `app_env` ke Settings
- Tambah `escalation_max_idle_turns`, `escalation_absolute_max_turns` ke Settings
- Update `.env.example` dengan template lengkap semua variabel

## 4. Scope

### Yang dikerjakan
- Update `app/config.py`
- Update `.env.example`

### Yang tidak dikerjakan
- Logic yang menggunakan settings ini

## 5. Langkah Implementasi

### Step 1: Update `app/config.py`

Tambahkan field berikut ke class `Settings`:

```python
# App
app_version: str = "0.1.0"
app_env: str = "development"

# Escalation (override default EscalationConfig)
escalation_max_idle_turns: int = 5
escalation_absolute_max_turns: int = 10
```

### Step 2: Update `.env.example`

Tambahkan semua variabel yang belum ada:

```bash
# === APP ===
APP_NAME=ai-agent-hybrid
APP_VERSION=0.1.0
APP_PORT=8000
APP_ENV=development
LOG_LEVEL=INFO

# === ESCALATION ===
ESCALATION_MAX_IDLE_TURNS=5
ESCALATION_ABSOLUTE_MAX_TURNS=10
```

### Step 3: Verifikasi

```python
from app.config import Settings
s = Settings()
assert s.app_version == "0.1.0"
assert s.app_env == "development"
assert s.escalation_max_idle_turns == 5
assert s.escalation_absolute_max_turns == 10
print("ALL CONFIG TESTS PASSED")
```

## 6. Output yang Diharapkan

Settings class dengan field baru, `.env.example` lengkap.

## 7. Dependencies

- Tidak ada dependency baru

## 8. Acceptance Criteria

- [ ] `Settings.app_version` ada dengan default `"0.1.0"`
- [ ] `Settings.app_env` ada dengan default `"development"`
- [ ] `Settings.escalation_max_idle_turns` ada dengan default `5`
- [ ] `Settings.escalation_absolute_max_turns` ada dengan default `10`
- [ ] `.env.example` mencakup semua variabel

## 9. Estimasi

**Low** — ~20 menit
