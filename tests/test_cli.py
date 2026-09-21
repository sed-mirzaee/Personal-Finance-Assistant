"""Tests for the interactive main menu."""

import pytest

from personal_finance_assistant.cli import (
    FULL_MENU, GOODBYE, SHORT_MENU, WELCOME, run_main_menu,
)

def test_exit_says_goodbye(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["exit"])
    assert GOODBYE in out


def test_empty_input_reprints_short_menu(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["", "exit"])
    assert out.count(SHORT_MENU) == 2   # once at startup, once after empty line
    assert "Unknown command" not in out


def run_with_inputs(monkeypatch, capsys, inputs):
    """Run the menu with scripted user input and return everything printed."""
    answers = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    run_main_menu()
    return capsys.readouterr().out


def test_startup_shows_welcome_and_short_menu_only(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["exit"])
    assert WELCOME in out
    assert SHORT_MENU in out
    assert FULL_MENU not in out


def test_help_shows_full_menu(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["help", "exit"])
    assert FULL_MENU in out


def test_unknown_command_points_to_help(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["abc", "exit"])
    assert "Unknown command: 'abc'" in out


def test_empty_input_is_ignored(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["", "exit"])
    assert "Unknown command" not in out


@pytest.mark.parametrize("text", ["HELP", "  help  ", "Help"])
def test_commands_ignore_case_and_spaces(monkeypatch, capsys, text):
    out = run_with_inputs(monkeypatch, capsys, [text, "exit"])
    assert FULL_MENU in out


def test_ctrl_c_exits_cleanly(monkeypatch, capsys):
    def raise_interrupt(_prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_interrupt)
    run_main_menu()
    assert "Goodbye!" in capsys.readouterr().out