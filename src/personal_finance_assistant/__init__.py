"""Personal Finance Assistant: track transactions, keep an account balance,
predict future balances and get simple saving and investment suggestions.

The most useful functions can be imported directly from the package:

    >>> from personal_finance_assistant import read_csv, predict_balance
    >>> transactions, errors = read_csv("examples/sample_transactions.csv")
    >>> predict_balance(3, transactions=transactions)
"""

from importlib.metadata import PackageNotFoundError, version

from personal_finance_assistant.account import (
    AccountFileError,
    add_transaction,
    get_balance,
    import_csv,
    load_transactions,
    read_csv,
)
from personal_finance_assistant.analysis import (
    average_monthly_expense_by_category,
    find_recurring_transactions,
    generate_recommendations,
    monthly_income_and_expense,
    predict_balance,
)
from personal_finance_assistant.charts import save_overview_chart
from personal_finance_assistant.data_model import EXPENSE, INCOME, Transaction
from personal_finance_assistant.settings import load_settings

try:
    __version__ = version("personal-finance-assistant")
except PackageNotFoundError:  # package is not installed, e.g. running from a plain copy
    __version__ = "unknown"

__all__ = [
    "EXPENSE",
    "INCOME",
    "AccountFileError",
    "Transaction",
    "__version__",
    "add_transaction",
    "average_monthly_expense_by_category",
    "find_recurring_transactions",
    "generate_recommendations",
    "get_balance",
    "import_csv",
    "load_settings",
    "load_transactions",
    "monthly_income_and_expense",
    "predict_balance",
    "read_csv",
    "save_overview_chart",
]