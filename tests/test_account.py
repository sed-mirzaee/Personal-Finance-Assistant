"""Tests for account.py."""

from datetime import date

import pytest

import personal_finance_assistant.account as ac
from personal_finance_assistant.account import (
    add_transaction,
    delete_transaction,
    edit_transaction,
    get_balance,
    import_csv,
    load_transactions,
)
from personal_finance_assistant.data_model import Transaction

DAY = date(2026, 9, 24)


@pytest.fixture(autouse=True)
def isolate_account_file(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "ACCOUNT_FILE", tmp_path / "account.json")


def test_empty_account_has_no_transactions_and_zero_balance():
    assert load_transactions() == []
    assert get_balance() == 0


def test_add_then_load_roundtrip():
    add_transaction(Transaction(DAY, 1200.0, "income", "salary"))
    add_transaction(Transaction(DAY, 45.5, "expense", "groceries"))
    transactions = load_transactions()
    assert len(transactions) == 2
    assert transactions[0].category == "salary"


def test_balance_sums_income_and_expenses():
    add_transaction(Transaction(DAY, 1200.0, "income", "salary"))
    add_transaction(Transaction(DAY, 45.5, "expense", "groceries"))
    assert get_balance() == pytest.approx(1154.5)


def test_delete_removes_the_right_transaction():
    tx1 = Transaction(DAY, 100.0, "income", "gift")
    tx2 = Transaction(DAY, 50.0, "expense", "leisure")
    add_transaction(tx1)
    add_transaction(tx2)

    deleted = delete_transaction(tx1.id)

    assert deleted is True
    remaining = load_transactions()
    assert len(remaining) == 1
    assert remaining[0].id == tx2.id


def test_delete_unknown_id_returns_false():
    add_transaction(Transaction(DAY, 100.0, "income", "gift"))
    assert delete_transaction("no-such-id") is False
    assert len(load_transactions()) == 1  # nothing was removed


def test_edit_changes_only_given_fields():
    tx = Transaction(DAY, 50.0, "expense", "groceries", "REWE")
    add_transaction(tx)

    edited = edit_transaction(tx.id, {"amount": 60})

    assert edited is True
    updated = load_transactions()[0]
    assert updated.amount == 60.0
    assert updated.category == "groceries"  # unchanged
    assert updated.note == "REWE"  # unchanged
    assert updated.id == tx.id  # id never changes


def test_edit_unknown_id_returns_false():
    add_transaction(Transaction(DAY, 50.0, "expense", "groceries"))
    assert edit_transaction("no-such-id", {"amount": 1}) is False


def test_edit_rejects_invalid_new_value():
    tx = Transaction(DAY, 50.0, "expense", "groceries")
    add_transaction(tx)
    with pytest.raises(ValueError):
        edit_transaction(tx.id, {"amount": -10})


def test_import_csv_adds_valid_rows(tmp_path):
    source = tmp_path / "import.csv"
    source.write_text(
        "date,type,amount,category,note\n"
        "2026-09-01,income,1000,salary,\n"
        "2026-09-05,expense,50,groceries,REWE\n",
        encoding="utf-8",
    )
    added, errors = import_csv(source)
    assert added == 2
    assert errors == []
    assert get_balance() == pytest.approx(950)


def test_import_csv_skips_bad_rows_and_reports_them(tmp_path):
    source = tmp_path / "import.csv"
    source.write_text(
        "date,type,amount,category,note\n"
        "2026-09-01,income,1000,salary,\n"
        "not-a-date,expense,50,groceries,\n"
        "2026-09-05,expense,-10,groceries,\n",
        encoding="utf-8",
    )
    added, errors = import_csv(source)
    assert added == 1
    assert len(errors) == 2