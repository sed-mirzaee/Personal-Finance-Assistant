"""Tests for the interactive main menu."""

from datetime import date

import pytest

import personal_finance_assistant.account as ac
import personal_finance_assistant.settings as st
from personal_finance_assistant.cli import (
    FULL_MENU,
    GOODBYE,
    SHORT_MENU,
    WELCOME,
    run_main_menu,
)


@pytest.fixture(autouse=True)
def isolate_settings_file(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "SETTINGS_FILE", tmp_path / "settings.json")


@pytest.fixture(autouse=True)
def isolate_account_file(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "ACCOUNT_FILE", tmp_path / "account.json")


def run_with_inputs(monkeypatch, capsys, inputs):
    """Run the menu with scripted user input and return everything printed."""
    answers = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    run_main_menu()
    return capsys.readouterr().out


# --- menu basics -----------------------------------------------------------

def test_startup_shows_welcome_and_short_menu_only(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["exit"])
    assert WELCOME in out
    assert SHORT_MENU in out
    assert FULL_MENU not in out


def test_help_shows_full_menu(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["help", "exit"])
    assert FULL_MENU in out


def test_exit_says_goodbye(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["exit"])
    assert GOODBYE in out


def test_empty_input_reprints_short_menu(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["", "exit"])
    assert out.count(SHORT_MENU) == 2
    assert "Unknown command" not in out


def test_unknown_command_points_to_help(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["abc", "exit"])
    assert "Unknown command: 'abc'" in out


def test_ctrl_c_exits_cleanly(monkeypatch, capsys):
    def raise_interrupt(_prompt=""):
        raise KeyboardInterrupt
    monkeypatch.setattr("builtins.input", raise_interrupt)
    run_main_menu()
    assert GOODBYE in run_with_inputs(monkeypatch, capsys, ["exit"])  # sanity: fixture still works


# --- settings command (unchanged behaviour) --------------------------------

def test_settings_add_category_flow(monkeypatch, capsys):
    out = run_with_inputs(
        monkeypatch, capsys,
        ["settings", "add-cat", "expense", "pets", "back", "exit"],
    )
    assert "successfully added" in out
    assert "pets" in st.load_settings()["expense_categories"]


# --- add / list / balance ---------------------------------------------------

def test_add_transaction_flow(monkeypatch, capsys):
    out = run_with_inputs(
        monkeypatch, capsys,
        ["add", "income", "salary", "1200", "", "", "balance", "exit"],
    )
    assert "Added income" in out
    assert "Current balance: +1200.00" in out


def test_add_transaction_rejects_unknown_category(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["add", "income", "yacht-sales", "exit"])
    assert "Not added" in out


def test_add_transaction_rejects_bad_amount(monkeypatch, capsys):
    out = run_with_inputs(
        monkeypatch, capsys,
        ["add", "income", "salary", "not-a-number", "exit"],
    )
    assert "Not added: amount must be a number" in out


def test_list_with_no_transactions(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["list", "exit"])
    assert "No transactions yet." in out


def test_list_shows_added_transaction(monkeypatch, capsys):
    out = run_with_inputs(
        monkeypatch, capsys,
        ["add", "expense", "groceries", "", "", "42", "list", "exit"],
    )
    assert "groceries" in out


# --- delete ------------------------------------------------------------

def test_delete_existing_transaction(monkeypatch, capsys):
    from personal_finance_assistant.data_model import Transaction
    tx = Transaction(date(2026, 9, 24), 10.0, "expense", "groceries")
    ac.add_transaction(tx)

    out = run_with_inputs(monkeypatch, capsys, ["delete", tx.id, "exit"])
    assert f"Deleted transaction {tx.id}" in out
    assert ac.load_transactions() == []


def test_delete_unknown_id(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["delete", "no-such-id", "exit"])
    assert "Not deleted" in out


# --- edit ------------------------------------------------------------

def test_edit_existing_transaction(monkeypatch, capsys):
    from personal_finance_assistant.data_model import Transaction
    tx = Transaction(date(2026, 9, 24), 10.0, "expense", "groceries")
    ac.add_transaction(tx)

    out = run_with_inputs(monkeypatch, capsys, ["edit", tx.id, "60", "", "", "", "exit"])
    assert f"Updated transaction {tx.id}" in out
    assert ac.load_transactions()[0].amount == 60.0


def test_edit_unknown_id(monkeypatch, capsys):
    out = run_with_inputs(
        monkeypatch, capsys,
        ["edit", "no-such-id", "60", "", "", "", "exit"],
    )
    assert "Not edited" in out


# --- import ------------------------------------------------------------

def test_import_reports_missing_file(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["import", "no_such_file.csv", "exit"])
    assert "Not imported" in out


def test_import_reads_valid_csv(monkeypatch, capsys, tmp_path):
    source = tmp_path / "import.csv"
    source.write_text(
        "date,type,amount,category,note\n2026-09-01,income,1000,salary,\n",
        encoding="utf-8",
    )
    out = run_with_inputs(monkeypatch, capsys, ["import", str(source), "balance", "exit"])
    assert "Imported 1 transaction(s)." in out
    assert "Current balance: +1000.00" in out


 #--- analysis ------------------------------------------------------------

def test_recurring_shows_messge_when_none_found(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["recurring", "exit"])
    assert "No recurring payments detected yet." in out


def test_recurring_detects_pattern(monkeypatch, capsys):
    from personal_finance_assistant.data_model import Transaction
    for d in [date(2026, 6, 1), date(2026, 7, 1), date(2026, 8, 1)]:
        ac.add_transaction(Transaction(d, 650.0, "expense", "rent"))
    out = run_with_inputs(monkeypatch, capsys, ["recurring", "exit"])
    assert "rent" in out


def test_predict_default_one_month(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["predict", "", "exit"])
    assert "Predicted balance in 1 month(s):" in out


def test_predict_rejects_bad_number(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["predict", "abc", "exit"])
    assert "Invalid number of months" in out


def test_recommend_no_income_message(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["recommend", "exit"])
    assert "No income recorded yet" in out