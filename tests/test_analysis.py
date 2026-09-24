"""Tests for analysis.py."""

from datetime import date
import pytest
import personal_finance_assistant.settings as st

@pytest.fixture(autouse=True)
def isolate_settings_file(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "SETTINGS_FILE", tmp_path / "settings.json")

from personal_finance_assistant.analysis import (
    find_recurring_transactions, generate_recommendations, predict_balance,
)
from personal_finance_assistant.data_model import Transaction


def monthly(day1, day2, day3, tx_type, category, amount):
    # Helper: build three transactions roughly a month apart.
    return [
        Transaction(day1, amount, tx_type, category),
        Transaction(day2, amount, tx_type, category),
        Transaction(day3, amount, tx_type, category),
    ]


def test_finds_a_monthly_recurring_expense():
    transactions = monthly(
        date(2026, 6, 1), date(2026, 7, 1), date(2026, 8, 1),
        "expense", "rent", 650.0,
    )
    recurring = find_recurring_transactions(transactions)
    assert len(recurring) == 1
    assert recurring[0]["category"] == "rent"
    assert recurring[0]["average_amount"] == 650.0
    assert recurring[0]["occurrences"] == 3


def test_ignores_irregular_transactions():
    transactions = [
        Transaction(date(2026, 6, 1), 40.0, "expense", "groceries"),
        Transaction(date(2026, 6, 3), 25.0, "expense", "groceries"),
        Transaction(date(2026, 6, 20), 60.0, "expense", "groceries"),
    ]
    assert find_recurring_transactions(transactions) == []


def test_ignores_single_occurrence():
    transactions = [Transaction(date(2026, 6, 1), 650.0, "expense", "rent")]
    assert find_recurring_transactions(transactions) == []


def test_ignores_similar_interval_but_different_amounts():
    transactions = [
        Transaction(date(2026, 6, 1), 100.0, "expense", "leisure"),
        Transaction(date(2026, 7, 1), 300.0, "expense", "leisure"),
    ]
    assert find_recurring_transactions(transactions) == []


def test_predict_balance_adds_recurring_income_and_subtracts_expenses():
    transactions = (
        monthly(date(2026, 6, 1), date(2026, 7, 1), date(2026, 8, 1),
                "income", "salary", 1200.0)
        + monthly(date(2026, 6, 2), date(2026, 7, 2), date(2026, 8, 2),
                  "expense", "rent", 650.0)
    )
    current_balance = sum(tx.signed_amount for tx in transactions)
    predicted = predict_balance(months_ahead=1, transactions=transactions)
    assert predicted == round(current_balance + (1200.0 - 650.0), 2)


def test_recommendations_flag_low_savings():
    transactions = [
        Transaction(date(2026, 6, 1), 2000.0, "income", "salary"),
        Transaction(date(2026, 6, 2), 50.0, "expense", "savings"),
    ]
    settings = {"monthly_expense_limit": 0}
    messages = generate_recommendations(transactions, settings)
    assert any("saving only" in m for m in messages)


def test_recommendations_flag_exceeded_limit():
    transactions = [
        Transaction(date(2026, 6, 1), 1000.0, "income", "salary"),
        Transaction(date(2026, 6, 2), 900.0, "expense", "leisure"),
    ]
    settings = {"monthly_expense_limit": 500}
    messages = generate_recommendations(transactions, settings)
    assert any("exceed your monthly limit" in m for m in messages)


def test_recommendations_flag_high_spending_category():
    transactions = [
        Transaction(date(2026, 6, 1), 1000.0, "income", "salary"),
        Transaction(date(2026, 6, 2), 500.0, "expense", "leisure"),
    ]
    settings = {"monthly_expense_limit": 0}
    messages = generate_recommendations(transactions, settings)
    assert any("leisure" in m for m in messages)


def test_no_income_gives_a_single_message():
    transactions = [Transaction(date(2026, 6, 1), 50.0, "expense", "groceries")]
    messages = generate_recommendations(transactions, {})
    assert len(messages) == 1
    assert "No income" in messages[0]


def test_balanced_finances_give_positive_message():
    transactions = [
        Transaction(date(2026, 6, 1), 2000.0, "income", "salary"),
        Transaction(date(2026, 6, 2), 300.0, "expense", "groceries"),
        Transaction(date(2026, 6, 3), 300.0, "expense", "savings"),
    ]
    settings = {"monthly_expense_limit": 0}
    messages = generate_recommendations(transactions, settings)
    assert messages == ["Your finances look balanced. Keep it up!"]