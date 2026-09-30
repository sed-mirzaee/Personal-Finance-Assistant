"""Tests for analysis.py."""

from datetime import date

import pytest

import personal_finance_assistant.settings as st
from personal_finance_assistant.analysis import (
    average_monthly_expense_by_category,
    find_recurring_transactions,
    generate_recommendations,
    predict_balance,
    predict_balance_recurring,
    predict_balance_trend,
)
from personal_finance_assistant.data_model import Transaction


@pytest.fixture(autouse=True)
def isolate_settings_file(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "SETTINGS_FILE", tmp_path / "settings.json")


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
    predicted = predict_balance_recurring(months_ahead=1, transactions=transactions)
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

def test_average_monthly_expense_by_category():
    transactions = [
        Transaction(date(2026, 6, 1), 600.0, "expense", "rent"),
        Transaction(date(2026, 7, 1), 600.0, "expense", "rent"),
        Transaction(date(2026, 8, 1), 600.0, "expense", "rent"),
        Transaction(date(2026, 7, 15), 300.0, "expense", "health"),  # only once
        Transaction(date(2026, 6, 1), 1000.0, "income", "salary"),   # ignored
    ]
    averages = average_monthly_expense_by_category(transactions)

    assert averages["rent"] == 600.0
    assert averages["health"] == 100.0  # 300 spread over 3 months
    assert "salary" not in averages


def test_average_monthly_expense_with_no_transactions():
    assert average_monthly_expense_by_category([]).empty


def steady_decline():
    # 1000 income, then 100 spent every 30 days: the balance falls
    # exactly 100 per month (1000, 900, 800, 700).
    return [
        Transaction(date(2026, 1, 1), 1000.0, "income", "salary"),
        Transaction(date(2026, 1, 31), 100.0, "expense", "groceries"),
        Transaction(date(2026, 3, 2), 100.0, "expense", "groceries"),
        Transaction(date(2026, 4, 1), 100.0, "expense", "groceries"),
    ]


def test_trend_continues_a_steady_decline():
    assert predict_balance_trend(1, transactions=steady_decline()) == pytest.approx(600.0)
    assert predict_balance_trend(3, transactions=steady_decline()) == pytest.approx(400.0)


def test_trend_with_one_day_returns_current_balance():
    transactions = [Transaction(date(2026, 1, 1), 1000.0, "income", "salary")]
    assert predict_balance_trend(3, transactions=transactions) == 1000.0


def test_trend_with_no_transactions():
    assert predict_balance_trend(3, transactions=[]) == 0.0


def test_predict_balance_uses_trend_by_default():
    result = predict_balance(1, transactions=steady_decline(), settings={})
    assert result == predict_balance_trend(1, transactions=steady_decline())


def test_predict_balance_can_use_recurring_method():
    settings = {"forecast_method": "recurring"}
    result = predict_balance(1, transactions=steady_decline(), settings=settings)
    assert result == predict_balance_recurring(1, transactions=steady_decline(), settings=settings)


def savings_account():
    # 5000 income, then 300 spent in each of three months:
    # monthly expense = 300, balance = 4100.
    return [
        Transaction(date(2026, 1, 1), 5000.0, "income", "salary"),
        Transaction(date(2026, 1, 15), 300.0, "expense", "rent"),
        Transaction(date(2026, 2, 15), 300.0, "expense", "rent"),
        Transaction(date(2026, 3, 15), 300.0, "expense", "rent"),
    ]


def test_recommends_investing_above_emergency_fund():
    recommendations = generate_recommendations(savings_account(), settings={})

    # emergency fund = 3 x 300 = 900, extra = 4100 - 900 = 3200
    assert any("Consider investing the extra 3200.00" in r for r in recommendations)


def test_no_investment_advice_below_emergency_fund():
    transactions = [
        Transaction(date(2026, 1, 1), 1000.0, "income", "salary"),
        Transaction(date(2026, 1, 15), 300.0, "expense", "rent"),
        Transaction(date(2026, 2, 15), 300.0, "expense", "rent"),
        Transaction(date(2026, 3, 15), 300.0, "expense", "rent"),
    ]
    recommendations = generate_recommendations(transactions, settings={})

    # balance 100 < emergency fund 900
    assert not any("Consider investing" in r for r in recommendations)


def test_investment_advice_uses_emergency_fund_setting():
    recommendations = generate_recommendations(
        savings_account(), settings={"emergency_fund_months": 20}
    )

    # emergency fund = 20 x 300 = 6000 > balance 4100
    assert not any("Consider investing" in r for r in recommendations)