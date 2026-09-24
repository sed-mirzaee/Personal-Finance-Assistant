"""Tests for the Transaction model."""

from datetime import date

import pytest

from personal_finance_assistant.data_model import Transaction, validate_transaction

DAY = date(2026, 9, 21)


def test_income_signed_amount_is_positive():
    tx = Transaction(DAY, 1200.0, "income", "salary")
    assert tx.signed_amount == 1200.0


def test_expense_signed_amount_is_negative():
    tx = Transaction(DAY, 45.5, "expense", "groceries")
    assert tx.signed_amount == -45.5


def test_note_is_optional():
    assert Transaction(DAY, 10, "expense", "coffee").note == ""


def test_validate_accepts_good_input():
    assert validate_transaction(10, "expense", "groceries") == []


@pytest.mark.parametrize("amount", [0, -5])
def test_validate_rejects_non_positive_amount(amount):
    errors = validate_transaction(amount, "expense", "coffee")
    assert errors and "amount" in errors[0]


def test_validate_rejects_unknown_type():
    errors = validate_transaction(10, "gift", "coffee")
    assert errors and "type" in errors[0]


def test_validate_rejects_empty_category():
    errors = validate_transaction(10, "expense", "   ")
    assert errors and "category" in errors[0]


def test_validate_can_return_multiple_errors_at_once():
    errors = validate_transaction(-5, "gift", "")
    assert len(errors) == 3


def test_to_row_gives_string_friendly_dict():
    tx = Transaction(DAY, 45.5, "expense", "groceries", "Aldi", id="abc12345")
    assert tx.to_row() == {
        "id": "abc12345", "date": "2026-09-21", "type": "expense",
        "amount": 45.5, "category": "groceries", "note": "Aldi",
    }


def test_from_row_builds_equivalent_transaction():
    row = {"id": "xyz789", "date": "2026-09-21", "type": "expense",
           "amount": "45.5", "category": "Groceries ", "note": " Aldi "}
    tx = Transaction.from_row(row)
    assert tx == Transaction(DAY, 45.5, "expense", "groceries", "Aldi", id="xyz789")


def test_from_row_generates_id_when_missing():
    row = {"date": "2026-09-21", "type": "expense", "amount": "45.5", "category": "groceries"}
    assert Transaction.from_row(row).id


def test_from_row_rejects_invalid_data():
    row = {"date": "2026-09-21", "type": "gift", "amount": "45.5", "category": "groceries"}
    with pytest.raises(ValueError):
        Transaction.from_row(row)


def test_two_transactions_get_different_ids():
    tx1 = Transaction(DAY, 10, "expense", "groceries")
    tx2 = Transaction(DAY, 10, "expense", "groceries")
    assert tx1.id != tx2.id


def test_to_row_then_from_row_roundtrip():
    original = Transaction(DAY, 1200.0, "income", "salary")
    assert Transaction.from_row(original.to_row()) == original