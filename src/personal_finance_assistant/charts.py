"""Turn transactions into one overview image (four charts) saved to disk."""

# Remember: We never call plt.show() here. The image is written straight to a file.

import matplotlib

matplotlib.use("Agg")  # tell matplotlib not to look for a screen/display
from datetime import timedelta
from pathlib import Path

import matplotlib.pyplot as plt

from personal_finance_assistant.account import load_transactions
from personal_finance_assistant.analysis import (
    average_monthly_expense_by_category,
    monthly_income_and_expense,
    predict_balance,
)
from personal_finance_assistant.settings import load_settings

DEFAULT_OVERVIEW_FILE = Path.home() / ".personal_finance_assistant" / "finance_overview.png"


def running_balance(transactions):
    # Returns (dates, balances): the balance after each transaction, oldest first.
    transactions = sorted(transactions, key=lambda tx: tx.date)
    dates = []
    balances = []
    running_total = 0.0
    for tx in transactions:
        running_total += tx.signed_amount
        dates.append(tx.date)
        balances.append(running_total)
    return dates, balances


# The charts are created in specific ax

def draw_balance_history(ax, transactions):
    dates, balances = running_balance(transactions)
    ax.plot(dates, balances, marker="o")
    ax.set_title("Account balance over time")
    ax.set_ylabel("Balance")
    ax.grid(axis="y", visible=True)
    ax.tick_params(axis="x", labelrotation=45)


def draw_balance_forecast(ax, transactions, settings):
    months_ahead = settings["forecast_months"]
    dates, balances = running_balance(transactions)
    if dates:
        ax.plot(dates, balances, marker="o", label="History")

        # The forecast starts from the last real point so the two lines connect.
        last_date = dates[-1]
        forecast_dates = [last_date]
        forecast_balances = [balances[-1]]
        for month in range(1, months_ahead + 1):
            forecast_dates.append(last_date + timedelta(days=30 * month))
            forecast_balances.append(
                predict_balance(months_ahead=month, transactions=transactions,
                                settings=settings)
            )
        ax.plot(forecast_dates, forecast_balances,
                linestyle="--", marker="x", label="Forecast")
        ax.legend()

    ax.set_title(f"Balance with {months_ahead}-month forecast")
    ax.set_ylabel("Balance")
    ax.grid(axis="y", visible=True)
    ax.tick_params(axis="x", labelrotation=45)


def draw_monthly_income_and_expense(ax, transactions):
    table = monthly_income_and_expense(transactions)
    if not table.empty:
        table.plot.bar(ax=ax)  # one group of bars per month, legend included
    ax.set_title("Income and expense per month")
    ax.set_xlabel("")
    ax.set_ylabel("Amount")
    ax.grid(axis="y", visible=True)
    ax.tick_params(axis="x", labelrotation=45)


def draw_category_averages(ax, transactions):
    averages = average_monthly_expense_by_category(transactions)
    if not averages.empty:
        averages.plot.barh(ax=ax)
        ax.invert_yaxis()  # largest category on top
    ax.set_title("Average monthly expense per category")
    ax.set_xlabel("Average per month")
    ax.set_ylabel("")
    # ax.grid(axis="x", visible=True)


# Put all four charts together in one image
def save_overview_chart(transactions=None, settings=None, output_path=None):
    # Draw all four charts into one image (2 x 2 grid) and save it.
    # Returns the path the image was saved to.
    if transactions is None:
        transactions = load_transactions()
    if settings is None:
        settings = load_settings()
    if output_path is None:
        output_path = DEFAULT_OVERVIEW_FILE
    output_path = Path(output_path)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    draw_balance_history(axes[0][0], transactions)
    draw_balance_forecast(axes[0][1], transactions, settings)
    draw_monthly_income_and_expense(axes[1][0], transactions)
    draw_category_averages(axes[1][1], transactions)

    fig.suptitle("Personal finance overview", fontsize=16)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)  # release the figure from memory now that we're done
    return output_path