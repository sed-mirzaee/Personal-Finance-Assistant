# Personal Finance Assistant

A simple command-line tool that tracks your income and expenses, detects
recurring payments (like rent or subscriptions), predicts your future
account balance, and gives basic text recommendations for saving money.

This project was built as the final project for the "Introduction to
Python" course at TU Dortmund.

## Features

- Add, edit, delete, and list transactions (income or expense)
- Import transactions from a CSV file
- Check your current balance
- Configure your own income/expense categories and thresholds
- Detect recurring payments (e.g. monthly rent)
- Predict your balance a few months into the future
- Get simple, rule-based recommendations for savings

## Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/) (used to install and run the project)

## Installation

Clone the repository and install it in editable mode:

```bash
git clone https://github.com/sed-mirzaee/Personal-Finance-Assistant.git
cd Personal-Finance-Assistant
uv pip install -e .
```

## Running the program

```bash
uv run -m personal_finance_assistant
```

or, using the installed command shortcut:

```bash
uv run pfa
```

Either way, you will see a welcome message and a short menu. Type `help`
at any time to see the full list of commands.

## Available commands

| Command     | What it does                                              |
|-------------|-----------------------------------------------------------|
| `add`       | Add a new transaction (income or expense)                 |
| `list`      | Show all transactions                                     |
| `edit`      | Edit an existing transaction                              |
| `delete`    | Delete a transaction by its id                            |
| `import`    | Import transactions from a CSV file                       |
| `balance`   | Show your current balance                                 |
| `recurring` | Detect recurring (repeated, roughly monthly) payments     |
| `predict`   | Predict your balance a number of months ahead             |
| `recommend` | Get a text recommendation based on your finances          |
| `settings`  | View or change categories and thresholds                  |
| `help`      | Show the full list of commands                            |
| `exit`      | Quit the program                                          |

## Where your data is stored

Your transactions and settings are saved as JSON files in your home
folder, under `.personal_finance_assistant/`. They are created
automatically the first time you run the program, so there is nothing to
set up manually.

## Running the tests

The project comes with a full pytest test suite. To run it:

```bash
uv run pytest -v
```

## Project structure

Personal-Finance-Assistant/
├── src/
│ ├── personal_finance_assistant/
│ ├── __init__.py
│ ├── __main__.py
│ ├── cli.py # the interactive command-line menu
│ ├── data_model.py # the Transaction data structure
│ ├── account.py # loading/saving transactions
│ ├── settings.py # user settings (categories, thresholds)
│ └── analysis.py # recurring payments, prediction, recommendations
├── tests/ # pytest tests for every module above
├── pyproject.toml
└── README.md


## Author

Sedigheh Mirzaei — TU Dortmund, Introduction to Python course project.