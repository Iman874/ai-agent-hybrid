# Task 08: Unit Test `notify()` + Validation Sweep

> **Status**: [x] Selesai
> **Estimasi**: Low (30 menit – 1 jam)
> **Dependency**: Task 01, Task 02-05

## 1. Deskripsi

Menulis unit test untuk fungsi `notify()` dan melakukan validation sweep bahwa tidak ada lagi `st.error/warning/info/success` langsung di file-file yang sudah dimigrasikan.

## 2. Tujuan Teknis

- Unit test `notify()` dengan 3 method
- Verification script: grep bahwa file-file yang dimigrasikan tidak ada panggilan langsung
- Semua test PASS

## 3. Scope

**Yang dikerjakan:**
- `tests/test_notify.py` — unit test `notify()`
- Validation grep sweep

**Yang tidak dikerjakan:**
- UI testing (dilakukan manual oleh user)

## 4. Langkah Implementasi

### 4.1 Buat Test File

- [x] Buat `tests/test_notify.py`:

```python
"""
Tests untuk Beta 0.1.13: notify() utility function.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNotifyToast:
    """Test notify() dengan method='toast'."""

    @patch("streamlit.toast")
    def test_toast_success(self, mock_toast):
        from streamlit_app.utils.notify import notify
        notify("Berhasil!", "success", method="toast")
        mock_toast.assert_called_once()
        call_arg = mock_toast.call_args[0][0]
        assert "Berhasil!" in call_arg
        assert "✅" in call_arg

    @patch("streamlit.toast")
    def test_toast_error(self, mock_toast):
        from streamlit_app.utils.notify import notify
        notify("Gagal!", "error", method="toast")
        mock_toast.assert_called_once()
        call_arg = mock_toast.call_args[0][0]
        assert "Gagal!" in call_arg
        assert "❌" in call_arg

    @patch("streamlit.toast")
    def test_toast_is_default_method(self, mock_toast):
        from streamlit_app.utils.notify import notify
        notify("Default method test", "info")
        mock_toast.assert_called_once()


class TestNotifyBanner:
    """Test notify() dengan method='banner'."""

    @patch("streamlit.markdown")
    def test_banner_renders_html(self, mock_md):
        from streamlit_app.utils.notify import notify
        notify("Error penting!", "error", method="banner")
        mock_md.assert_called_once()
        call_args = mock_md.call_args
        html = call_args[0][0]
        assert "banner" in html
        assert "Error penting!" in html
        assert call_args[1].get("unsafe_allow_html") is True

    @patch("streamlit.markdown")
    def test_banner_custom_icon(self, mock_md):
        from streamlit_app.utils.notify import notify
        notify("Offline", "error", icon="cloud_off", method="banner")
        html = mock_md.call_args[0][0]
        assert "cloud_off" in html


class TestNotifyInline:
    """Test notify() dengan method='inline'."""

    @patch("streamlit.info")
    def test_inline_info(self, mock_info):
        from streamlit_app.utils.notify import notify
        notify("Informasi", "info", method="inline")
        mock_info.assert_called_once()

    @patch("streamlit.error")
    def test_inline_error(self, mock_error):
        from streamlit_app.utils.notify import notify
        notify("Error inline", "error", method="inline")
        mock_error.assert_called_once()

    @patch("streamlit.warning")
    def test_inline_warning(self, mock_warning):
        from streamlit_app.utils.notify import notify
        notify("Perhatian", "warning", method="inline")
        mock_warning.assert_called_once()

    @patch("streamlit.success")
    def test_inline_success(self, mock_success):
        from streamlit_app.utils.notify import notify
        notify("Sukses", "success", method="inline")
        mock_success.assert_called_once()


class TestAutoDetectIcon:
    """Test auto-detect icon berdasarkan type."""

    @patch("streamlit.markdown")
    def test_success_uses_task_alt(self, mock_md):
        from streamlit_app.utils.notify import notify
        notify("OK", "success", method="banner")
        html = mock_md.call_args[0][0]
        assert "task_alt" in html

    @patch("streamlit.markdown")
    def test_error_uses_error_icon(self, mock_md):
        from streamlit_app.utils.notify import notify
        notify("Fail", "error", method="banner")
        html = mock_md.call_args[0][0]
        assert "error" in html

    @patch("streamlit.markdown")
    def test_warning_uses_warning_icon(self, mock_md):
        from streamlit_app.utils.notify import notify
        notify("Warn", "warning", method="banner")
        html = mock_md.call_args[0][0]
        assert "warning" in html

    @patch("streamlit.markdown")
    def test_custom_icon_overrides_default(self, mock_md):
        from streamlit_app.utils.notify import notify
        notify("Custom", "error", icon="cloud_off", method="banner")
        html = mock_md.call_args[0][0]
        assert "cloud_off" in html
```

### 4.2 Validation Sweep — Grep Check

- [x] Jalankan perintah untuk memastikan file yang dimigrasikan tidak ada `st.error/warning/info/success` langsung:

```bash
# Check sidebar.py (kecuali model selector yang sudah dihapus di task 07):
grep -n "st\.error\|st\.warning\|st\.info\|st\.success" streamlit_app/components/sidebar.py

# Check format_tab.py:
grep -n "st\.error\|st\.warning\|st\.info\|st\.success" streamlit_app/components/format_tab.py

# Check form_document.py:
grep -n "st\.error\|st\.warning\|st\.info\|st\.success" streamlit_app/components/form_document.py

# Check form_direct.py:
grep -n "st\.error\|st\.warning\|st\.info\|st\.success" streamlit_app/components/form_direct.py

# Check tor_preview.py:
grep -n "st\.error\|st\.warning\|st\.info\|st\.success" streamlit_app/components/tor_preview.py

# Check chat.py:
grep -n "st\.error\|st\.warning\|st\.info\|st\.success" streamlit_app/components/chat.py

# Check client.py:
grep -n "st\.error\|st\.warning\|st\.info\|st\.success" streamlit_app/api/client.py
```

**Semua harus return 0 hasil** (tidak ditemukan).

### 4.3 Check Icon Consistency

- [x] Grep untuk fungsi `icon()` lokal yang harusnya sudah dihapus:

```bash
# Check format_tab.py tidak lagi punya fungsi icon() lokal:
grep -n "def icon(" streamlit_app/components/format_tab.py
# Harus return 0 hasil
```

### 4.4 Run All Tests

```bash
venv\Scripts\pytest tests/test_notify.py -v --tb=short

# Juga run existing tests untuk memastikan tidak regresi:
venv\Scripts\pytest tests/ -v --tb=short
```

## 5. Output yang Diharapkan

```
tests/test_notify.py::TestNotifyToast::test_toast_success PASSED
tests/test_notify.py::TestNotifyToast::test_toast_error PASSED
tests/test_notify.py::TestNotifyToast::test_toast_is_default_method PASSED
tests/test_notify.py::TestNotifyBanner::test_banner_renders_html PASSED
tests/test_notify.py::TestNotifyBanner::test_banner_custom_icon PASSED
tests/test_notify.py::TestNotifyInline::test_inline_info PASSED
tests/test_notify.py::TestNotifyInline::test_inline_error PASSED
tests/test_notify.py::TestNotifyInline::test_inline_warning PASSED
tests/test_notify.py::TestNotifyInline::test_inline_success PASSED
tests/test_notify.py::TestAutoDetectIcon::test_success_uses_task_alt PASSED
tests/test_notify.py::TestAutoDetectIcon::test_error_uses_error_icon PASSED
tests/test_notify.py::TestAutoDetectIcon::test_warning_uses_warning_icon PASSED
tests/test_notify.py::TestAutoDetectIcon::test_custom_icon_overrides_default PASSED

13 passed
```

## 6. Acceptance Criteria

- [x] `pytest tests/test_notify.py -v` → **semua 13 test PASSED**.
- [x] Validation sweep: **0 panggilan** `st.error/warning/info/success` langsung di file-file yang dimigrasikan.
- [x] Tidak ada fungsi `def icon(` lokal di `format_tab.py`.
- [x] Tidak ada regresi pada test suite lain.
- [x] Server start tanpa error.
