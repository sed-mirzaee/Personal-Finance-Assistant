"""Tests for settings.py."""
import pytest

import personal_finance_assistant.settings as st
from personal_finance_assistant.settings import (
    add_category,
    format_settings,
    load_settings,
    remove_category,
    set_value,
)


@pytest.fixture(autouse=True)
def isolate_settings_file(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "SETTINGS_FILE", tmp_path / "settings.json")


def test_load_creates_file_on_first_call():
    assert not st.SETTINGS_FILE.exists()
    assert load_settings() == st.DEFAULT_SETTINGS
    assert st.SETTINGS_FILE.exists()


def test_load_merges_partial_file_over_defaults():
    load_settings()
    st.SETTINGS_FILE.write_text('{"report_months": 6}', encoding="utf-8")
    loaded = load_settings()
    assert loaded["report_months"] == 6
    assert loaded["expense_categories"] == st.DEFAULT_SETTINGS["expense_categories"]


def test_add_category_rejects_duplicate():
    load_settings()
    with pytest.raises(ValueError):
        add_category("expense", "rent")


def test_add_category_rejects_empty_name():
    load_settings()
    with pytest.raises(ValueError):
        add_category("expense", "   ")


def test_remove_category(capsys):
    load_settings()
    remove_category("expense", "leisure")
    assert "leisure" not in load_settings()["expense_categories"]
    assert "successfully removed" in capsys.readouterr().out


def test_remove_other_is_protected():
    load_settings()
    with pytest.raises(ValueError):
        remove_category("income", "other")


def test_remove_unknown_category():
    load_settings()
    with pytest.raises(ValueError):
        remove_category("income", "yacht")


def test_set_value_rejects_unknown_key():
    load_settings()
    with pytest.raises(ValueError):
        set_value("nope", "1")


def test_format_settings_shows_values():
    load_settings()
    text = format_settings()
    assert "report_months: " in text
    assert "rent" in text