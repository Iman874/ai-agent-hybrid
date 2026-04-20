"""Tests untuk Beta 0.1.15 performa Streamlit (tanpa UI test)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
STREAMLIT_APP_DIR = ROOT_DIR / "streamlit_app"
if str(STREAMLIT_APP_DIR) not in sys.path:
    sys.path.insert(0, str(STREAMLIT_APP_DIR))


import state
from api import client
from components import format_tab
from components import settings_dialog
from components import tor_preview
from utils import i18n


class _StateProxy(dict):
    """Proxy session_state yang mendukung akses dict dan atribut."""

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key, value):
        self[key] = value


class _DummyCacheCallable:
    """Callable sederhana dengan clear counter untuk uji invalidasi cache."""

    def __init__(self):
        self.clear_calls = 0

    def __call__(self, *args, **kwargs):
        return None

    def clear(self):
        self.clear_calls += 1


class _DummySpinner:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeStreamlit:
    """Fake subset API Streamlit untuk unit test helper lazy-export."""

    def __init__(self, button_results: list[bool] | None = None):
        self.session_state = _StateProxy()
        self._button_results = list(button_results or [])
        self.download_calls: list[tuple] = []
        self.rerun_calls = 0

    def button(self, *args, **kwargs):
        if not self._button_results:
            return False
        return self._button_results.pop(0)

    def download_button(self, *args, **kwargs):
        self.download_calls.append((args, kwargs))
        return None

    def spinner(self, *args, **kwargs):
        return _DummySpinner()

    def rerun(self, *args, **kwargs):
        self.rerun_calls += 1


class _FakeRerunRecorder:
    def __init__(self, fail_on_fragment: bool = False):
        self.fail_on_fragment = fail_on_fragment
        self.calls: list[tuple[tuple, dict]] = []

    def rerun(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.fail_on_fragment and kwargs.get("scope") == "fragment":
            raise TypeError("fragment scope not supported")


def test_invalidate_session_cache_calls_clear(monkeypatch):
    session_list_cache = _DummyCacheCallable()
    session_detail_cache = _DummyCacheCallable()

    monkeypatch.setattr(client, "fetch_session_list", session_list_cache)
    monkeypatch.setattr(client, "fetch_session_detail", session_detail_cache)

    client.invalidate_session_cache()

    assert session_list_cache.clear_calls == 1
    assert session_detail_cache.clear_calls == 1


def test_invalidate_style_cache_calls_clear(monkeypatch):
    styles_cache = _DummyCacheCallable()
    active_style_cache = _DummyCacheCallable()

    monkeypatch.setattr(client, "get_styles", styles_cache)
    monkeypatch.setattr(client, "get_active_style", active_style_cache)

    client.invalidate_style_cache()

    assert styles_cache.clear_calls == 1
    assert active_style_cache.clear_calls == 1


def test_begin_ui_action_rejects_when_busy(monkeypatch):
    fake_st = SimpleNamespace(
        session_state=_StateProxy({
            "_ui_busy": True,
            "_ui_last_action": None,
        })
    )
    monkeypatch.setattr(state, "st", fake_st)

    assert state.begin_ui_action("chat:send:1") is False


def test_begin_ui_action_rejects_duplicate_action(monkeypatch):
    fake_st = SimpleNamespace(
        session_state=_StateProxy({
            "_ui_busy": False,
            "_ui_last_action": "chat:send:1",
        })
    )
    monkeypatch.setattr(state, "st", fake_st)

    assert state.begin_ui_action("chat:send:1") is False
    assert fake_st.session_state["_ui_busy"] is False


def test_begin_end_ui_action_updates_guard_state(monkeypatch):
    fake_st = SimpleNamespace(
        session_state=_StateProxy({
            "_ui_busy": False,
            "_ui_last_action": None,
        })
    )
    monkeypatch.setattr(state, "st", fake_st)

    assert state.begin_ui_action("session:open:1") is True
    assert fake_st.session_state["_ui_busy"] is True

    state.end_ui_action("session:open:1")

    assert fake_st.session_state["_ui_busy"] is False
    assert fake_st.session_state["_ui_last_action"] == "session:open:1"


def test_record_perf_sample_appends_when_enabled(monkeypatch):
    fake_st = SimpleNamespace(
        session_state=_StateProxy({
            "_perf_enabled": True,
            "_perf_samples": [],
        })
    )
    monkeypatch.setattr(state, "st", fake_st)

    state.record_perf_sample("chat_send", 12.345)

    assert len(fake_st.session_state["_perf_samples"]) == 1
    assert fake_st.session_state["_perf_samples"][0]["name"] == "chat_send"
    assert fake_st.session_state["_perf_samples"][0]["ms"] == 12.35


def test_record_perf_sample_skips_when_disabled(monkeypatch):
    fake_st = SimpleNamespace(
        session_state=_StateProxy({
            "_perf_enabled": False,
            "_perf_samples": [],
        })
    )
    monkeypatch.setattr(state, "st", fake_st)

    state.record_perf_sample("chat_send", 10.0)

    assert fake_st.session_state["_perf_samples"] == []


def test_lazy_export_no_call_on_passive_render(monkeypatch):
    fake_st = _FakeStreamlit(button_results=[False])
    monkeypatch.setattr(tor_preview, "st", fake_st)

    calls = {"count": 0}

    def _fake_export(session_id: str, fmt: str):
        calls["count"] += 1
        return b"binary"

    monkeypatch.setattr(tor_preview, "export_document", _fake_export)

    tor_preview._render_lazy_download(
        session_id="session-1",
        key_suffix="_hybrid",
        fmt="pdf",
        icon="PDF",
        mime="application/pdf",
    )

    assert calls["count"] == 0
    assert fake_st.rerun_calls == 0
    assert fake_st.download_calls == []


def test_lazy_export_prepare_then_use_local_cache(monkeypatch):
    fake_st = _FakeStreamlit(button_results=[True, False])
    monkeypatch.setattr(tor_preview, "st", fake_st)

    calls = {"count": 0}

    def _fake_export(session_id: str, fmt: str):
        calls["count"] += 1
        return b"cached-bytes"

    monkeypatch.setattr(tor_preview, "export_document", _fake_export)

    tor_preview._render_lazy_download(
        session_id="session-1",
        key_suffix="_hybrid",
        fmt="pdf",
        icon="PDF",
        mime="application/pdf",
    )

    cache_key = tor_preview._export_cache_key("session-1", "_hybrid", "pdf")
    assert calls["count"] == 1
    assert fake_st.rerun_calls == 1
    assert fake_st.session_state["_tor_export_cache"][cache_key] == b"cached-bytes"

    tor_preview._render_lazy_download(
        session_id="session-1",
        key_suffix="_hybrid",
        fmt="pdf",
        icon="PDF",
        mime="application/pdf",
    )

    assert calls["count"] == 1
    assert len(fake_st.download_calls) == 1


def test_is_default_style_true_for_bool_true():
    assert format_tab._is_default_style({"is_default": True}) is True


def test_is_default_style_false_for_false_string():
    assert format_tab._is_default_style({"is_default": "false"}) is False


def test_is_default_style_true_for_true_string():
    assert format_tab._is_default_style({"is_default": "true"}) is True


def test_format_tab_rerun_if_changed_prefers_fragment(monkeypatch):
    fake_st = _FakeRerunRecorder()
    monkeypatch.setattr(format_tab, "st", fake_st)

    format_tab._rerun_if_changed(True)

    assert len(fake_st.calls) == 1
    assert fake_st.calls[0][1] == {"scope": "fragment"}


def test_format_tab_rerun_if_changed_fallback_global(monkeypatch):
    fake_st = _FakeRerunRecorder(fail_on_fragment=True)
    monkeypatch.setattr(format_tab, "st", fake_st)

    format_tab._rerun_if_changed(True)

    assert len(fake_st.calls) == 2
    assert fake_st.calls[0][1] == {"scope": "fragment"}
    assert fake_st.calls[1][1] == {}


def test_i18n_get_language_defaults_to_id(monkeypatch):
    fake_st = SimpleNamespace(session_state=_StateProxy({}))
    monkeypatch.setattr(i18n, "st", fake_st)

    assert i18n.get_language() == "id"


def test_i18n_set_language_persists_and_normalizes(monkeypatch):
    fake_st = SimpleNamespace(session_state=_StateProxy({}))
    monkeypatch.setattr(i18n, "st", fake_st)

    assert i18n.set_language("en") == "en"
    assert fake_st.session_state["app_language"] == "en"

    assert i18n.set_language("fr") == "id"
    assert fake_st.session_state["app_language"] == "id"


def test_i18n_translation_fallback_to_id_when_en_missing(monkeypatch):
    fake_st = SimpleNamespace(session_state=_StateProxy({"app_language": "en"}))
    monkeypatch.setattr(i18n, "st", fake_st)
    monkeypatch.setattr(
        i18n,
        "TRANSLATIONS",
        {
            "id": {"k.only.id": "Hanya ID"},
            "en": {},
        },
    )

    assert i18n.tr("k.only.id", "Default") == "Hanya ID"


def test_i18n_translation_uses_default_for_unknown_key(monkeypatch):
    fake_st = SimpleNamespace(session_state=_StateProxy({"app_language": "en"}))
    monkeypatch.setattr(i18n, "st", fake_st)
    monkeypatch.setattr(i18n, "TRANSLATIONS", {"id": {}, "en": {}})

    assert i18n.tr("missing.key", "fallback") == "fallback"


def test_i18n_key_coverage_for_task11_core_components():
    required_keys = [
        "settings.nav.general",
        "settings.nav.format_tor",
        "settings.nav.advanced",
        "settings.section.language",
        "settings.language.label",
        "sidebar.model_label",
        "sidebar.new_chat",
        "sidebar.history",
        "sidebar.tools",
        "sidebar.settings",
        "chat.input_placeholder",
        "chat.empty_title",
        "chat.empty_desc",
        "chat.processing_spinner",
        "chat.back_to_active",
        "doc.title",
        "doc.subtitle",
        "doc.upload_label",
        "doc.generate_button",
        "format.title",
        "format.available",
        "format.set_active",
        "format.edit_style",
        "format.extract_button",
        "format.save_changes",
    ]

    for key in required_keys:
        assert key in i18n.TRANSLATIONS["id"], f"Missing id translation key: {key}"
        assert key in i18n.TRANSLATIONS["en"], f"Missing en translation key: {key}"


def test_settings_dialog_rerun_prefers_fragment(monkeypatch):
    fake_st = _FakeRerunRecorder()
    monkeypatch.setattr(settings_dialog, "st", fake_st)

    settings_dialog._run_dialog_rerun(True)

    assert len(fake_st.calls) == 1
    assert fake_st.calls[0][1] == {"scope": "fragment"}


def test_settings_dialog_app_rerun_is_global(monkeypatch):
    fake_st = _FakeRerunRecorder()
    monkeypatch.setattr(settings_dialog, "st", fake_st)

    settings_dialog._run_app_rerun(True)

    assert len(fake_st.calls) == 1
    assert fake_st.calls[0][1] == {}