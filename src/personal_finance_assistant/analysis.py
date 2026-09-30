"""Analysis: detect recurring payments, predict balance, give recommendations."""

import numpy as np
import pandas as pd

from personal_finance_assistant.account import load_transactions
from personal_finance_assistant.data_model import EXPENSE, INCOME
from personal_finance_assistant.settings import load_settings

DAYS_PER_MONTH = 30  # the forecast counts one month as 30 days (same as the chart)

def group_by_type_and_category(transactions) -> dict:
    # Returns a dict like {("expense", "rent"): [tx1, tx2, ...], ...}
    groups = {}
    for tx in transactions:
        key = (tx.type, tx.category)
        if key not in groups:
            groups[key] = []
        groups[key].append(tx)
    return groups


def find_recurring_transactions(transactions=None, settings=None) -> list:
    # Look through the transactions and find groups (same type + category)
    # that repeat roughly every month with a similar amount.
    if transactions is None:
        transactions = load_transactions()
    if settings is None:
        settings = load_settings()

    min_interval = settings.get("recurring_min_interval_days", 25)
    max_interval = settings.get("recurring_max_interval_days", 35)
    tolerance = settings.get("recurring_amount_tolerance", 0.15)

    recurring = []
    groups = group_by_type_and_category(transactions)

    for (tx_type, category), group in groups.items():
        if len(group) < 2:
            continue

        group.sort(key=lambda tx: tx.date)

        gaps = []
        for i in range(len(group) - 1):
            gap = (group[i + 1].date - group[i].date).days
            gaps.append(gap)
        average_gap = sum(gaps) / len(gaps)

        amounts = [tx.amount for tx in group]
        average_amount = sum(amounts) / len(amounts)

        amounts_are_similar = True
        for amount in amounts:
            if abs(amount - average_amount) > average_amount * tolerance:
                amounts_are_similar = False

        if min_interval <= average_gap <= max_interval and amounts_are_similar:
            recurring.append({
                "type": tx_type,
                "category": category,
                "average_amount": round(average_amount, 2),
                "average_interval_days": round(average_gap, 1),
                "occurrences": len(group),
            })

    return recurring


def predict_balance_recurring(months_ahead=1, transactions=None, settings=None) -> float:
    # Forecast method "recurring": start from the current balance and assume
    # every recurring payment (salary, rent, ...) keeps happening every month.
    if transactions is None:
        transactions = load_transactions()
    if settings is None:
        settings = load_settings()

    current_balance = sum(tx.signed_amount for tx in transactions)

    monthly_net_change = 0.0
    for item in find_recurring_transactions(transactions, settings):
        if item["type"] == INCOME:
            monthly_net_change += item["average_amount"]
        else:
            monthly_net_change -= item["average_amount"]

    predicted = current_balance + monthly_net_change * months_ahead
    return round(predicted, 2)


def daily_balance(transactions) -> pd.Series:
    # Balance at the end of each day that has transactions, oldest first.
    # Returns a Series with the date as index, e.g.  2026-01-01  1000.0
    df = transactions_to_dataframe(transactions)
    signed = df["amount"].where(df["type"] == INCOME, -df["amount"])
    return signed.groupby(df["date"]).sum().cumsum()


def predict_balance_trend(months_ahead=1, transactions=None) -> float:
    # Forecast method "trend": fit a straight line (linear regression) through
    # the daily balance and continue it from the current balance.
    if transactions is None:
        transactions = load_transactions()
    if not transactions:
        return 0.0

    balance = daily_balance(transactions)
    current = float(balance.iloc[-1])
    if len(balance) < 2:
        return round(current, 2)  # one day of data: no trend to measure

    days = (balance.index - balance.index[0]).days
    slope_per_day, _ = np.polyfit(days, balance.to_numpy(), 1)

    predicted = current + slope_per_day * DAYS_PER_MONTH * months_ahead
    return round(float(predicted), 2)


def predict_balance(months_ahead=1, transactions=None, settings=None) -> float:
    # Estimate the balance N months from now, using the forecast method
    # chosen in the settings ("trend" by default, or "recurring").
    if settings is None:
        settings = load_settings()

    if settings.get("forecast_method", "trend") == "recurring":
        return predict_balance_recurring(months_ahead, transactions, settings)
    return predict_balance_trend(months_ahead, transactions)


def generate_recommendations(transactions=None, settings=None) -> list:
    # Simple rule-based suggestions about saving and spending.
    if transactions is None:
        transactions = load_transactions()
    if settings is None:
        settings = load_settings()

    low_savings_rate = settings.get("low_savings_rate", 0.10)
    high_spending_share = settings.get("high_spending_share", 0.30)

    recommendations = []

    total_income = sum(tx.amount for tx in transactions if tx.type == INCOME)
    total_expense = sum(tx.amount for tx in transactions if tx.type == EXPENSE)

    if total_income == 0:
        recommendations.append("No income recorded yet, so no savings advice can be given.")
        return recommendations

    if total_expense > total_income:
        recommendations.append(
            f"You spent {total_expense - total_income:.2f} more than you earned. "
            "Try to reduce your expenses."
        )

    savings_amount = sum(
        tx.amount for tx in transactions
        if tx.type == EXPENSE and tx.category == "savings"
    )
    savings_rate = savings_amount / total_income
    if savings_rate < low_savings_rate:
        recommendations.append(
            f"You are saving only {savings_rate:.0%} of your income. "
            "Consider setting aside more each month."
        )

    # Compare the AVERAGE monthly expense with the monthly limit.
    monthly_expense = float(average_monthly_expense_by_category(transactions).sum())
    limit = settings.get("monthly_expense_limit", 0)
    if limit and monthly_expense > limit:
        recommendations.append(
            f"Your average monthly expenses ({monthly_expense:.2f}) "
            f"exceed your monthly limit ({limit:.2f})."
        )

    category_totals = {}
    for tx in transactions:
        if tx.type == EXPENSE:
            category_totals[tx.category] = category_totals.get(tx.category, 0) + tx.amount

    for category, amount in category_totals.items():
        if amount > total_income * high_spending_share:
            recommendations.append(
                f"Spending on '{category}' ({amount:.2f}) is more than "
                f"{high_spending_share:.0%} of your income."
            )

    # Investment: keep an emergency fund of a few months of expenses,
    # and suggest investing whatever is above it.
    emergency_months = settings.get("emergency_fund_months", 3)
    if monthly_expense > 0:
        emergency_fund = monthly_expense * emergency_months
        balance = sum(tx.signed_amount for tx in transactions)
        if balance > emergency_fund:
            recommendations.append(
                f"Your balance ({balance:.2f}) is more than {emergency_months} months "
                f"of expenses ({emergency_fund:.2f}). "
                f"Consider investing the extra {balance - emergency_fund:.2f}."
            )
            
    if not recommendations:
        recommendations.append("Your finances look balanced. Keep it up!")

    return recommendations


def transactions_to_dataframe(transactions) -> pd.DataFrame:
    # One row per transaction, used by the pandas-based analyses below.
    return pd.DataFrame({
        "date": pd.to_datetime([tx.date for tx in transactions]),
        "type": [tx.type for tx in transactions],
        "category": [tx.category for tx in transactions],
        "amount": [tx.amount for tx in transactions],
    })


def average_monthly_expense_by_category(transactions=None) -> pd.Series:
    # Average monthly spending per expense category, largest first.
    # Total per category is divided by the number of months the data covers
    # (first to last transaction month, inclusive), so a category that
    # appears only once is not treated as if it happened every month.
    # Returns a Series like:  rent 650.0, groceries 210.5, ...
    if transactions is None:
        transactions = load_transactions()
    if not transactions:
        return pd.Series(dtype=float)

    df = transactions_to_dataframe(transactions)

    months = df["date"].dt.to_period("M")
    month_count = (months.max() - months.min()).n + 1

    expenses = df[df["type"] == EXPENSE]
    averages = expenses.groupby("category")["amount"].sum() / month_count
    return averages.round(2).sort_values(ascending=False)


def monthly_income_and_expense(transactions=None) -> pd.DataFrame:
    # Total income and expense per month, as a table:
    #            income  expense
    # month
    # 2026-06    1000.0    730.0
    # 2026-07    1000.0      0.0
    if transactions is None:
        transactions = load_transactions()
    if not transactions:
        return pd.DataFrame(columns=[INCOME, EXPENSE])

    df = transactions_to_dataframe(transactions)
    df["month"] = df["date"].dt.strftime("%Y-%m")

    table = df.groupby(["month", "type"])["amount"].sum().unstack(fill_value=0.0)

    # Always have both columns in the same order, even if a month has no income.
    return table.reindex(columns=[INCOME, EXPENSE], fill_value=0.0).round(2)