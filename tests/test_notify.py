"""
Tests untuk Beta 0.1.13: notify() utility function.
"""
import pytest
from unittest.mock import patch


class TestNotifyToast:
    """Test notify() dengan method='toast'."""

    @patch("streamlit.toast")
    def test_toast_success(self, mock_toast):
        from streamlit_app.utils.notify import notify
        notify("Berhasil!", "success", method="toast")
        mock_toast.assert_called_once()
        call_arg = mock_toast.call_args[0][0]
        assert "Berhasil!" in call_arg
        assert "\u2705" in call_arg

    @patch("streamlit.toast")
    def test_toast_error(self, mock_toast):
        from streamlit_app.utils.notify import notify
        notify("Gagal!", "error", method="toast")
        mock_toast.assert_called_once()
        call_arg = mock_toast.call_args[0][0]
        assert "Gagal!" in call_arg
        assert "\u274c" in call_arg

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
