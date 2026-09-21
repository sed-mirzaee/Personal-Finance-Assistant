"""User settings: the lists of income and expense categories, ... """

import copy
import json
from pathlib import Path

SETTINGS_FILE = Path.home() / ".personal_finance_assistant" / "settings.json"

DEFAULT_SETTINGS = {
    "income_categories": ["salary", "scholarship", "gift", "other"],
    "expense_categories": [
        "rent", "groceries", "transport", "insurance", "subscriptions",
        "leisure", "health", "education", "savings", "other",
    ],
    "monthly_expense_limit": 0.0,  # 0 = no limit
    "report_months": 3,            # default number of months in reports
}
REQUIRED_CATEGORY = "other"        # can never be removed


def load_settings() -> dict:
    # If exist file, do nothing. If there is no file write in path
    path = SETTINGS_FILE
    settings = copy.deepcopy(DEFAULT_SETTINGS)

    if path.exists():
        # Read
        settings.update(json.loads(path.read_text(encoding="utf-8")))
    else:
        #FirstTime, Write
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(settings, indent=2), encoding="utf-8")

    return settings


def save_settings(settings: dict) -> None:
    path = SETTINGS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def add_category(kind: str, name: str) -> None:
    settings = load_settings()

    # kind is 'income' or 'expense'.
    name, key = name.strip().lower(), f"{kind}_categories"
    if key not in settings:
        raise ValueError("type must be 'income' or 'expense'")
    if not name:
        raise ValueError("name must not be empty")
    if name in settings[key]:
        raise ValueError(f"'{name}' already exists")

    settings[key].append(name)
    save_settings(settings)
    print(f"'{name}' is successfully added to {kind}_categories")


def remove_category(kind: str, name: str) -> None:
    settings = load_settings()

    # kind is 'income' or 'expense'.
    name, key = name.strip().lower(), f"{kind}_categories"
    if key not in settings:
        raise ValueError("type must be 'income' or 'expense'")
    if name == REQUIRED_CATEGORY:
        raise ValueError(f"'{REQUIRED_CATEGORY}' is required and cannot be removed")
    if name not in settings[key]:
        raise ValueError(f"'{name}' does not exist")

    settings[key].remove(name)
    save_settings(settings)
    print(f"'{name}' is successfully removed from {kind}_categories")


def set_value(key: str, text: str) -> None:

    settings = load_settings()

    if (key not in settings):
        raise ValueError("setting key is not valid")

    # Change a single-value setting
    default = DEFAULT_SETTINGS.get(key)

    if default is None or isinstance(default, list):
        raise ValueError(f"'{key}' is not a value setting")
    value = type(default)(text)  # raises ValueError for e.g. "abc"
    if value < 0:
        raise ValueError("value must not be negative")

    settings[key] = value
    save_settings(settings)
    print(f"'{key}' is successfully updated to {text}")


def format_settings() -> str:
    # Readable format for showing the current settings.
    settings = load_settings()

    lines = ["Current settings:"]
    for key, value in settings.items():
        shown = ", ".join(value) if isinstance(value, list) else value
        lines.append(f"  {key}: {shown}")
    return "\n".join(lines)