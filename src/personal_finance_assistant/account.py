"""Account: stores transactions in a JSON file, with add, delete, edit and import."""

import csv
import json
from pathlib import Path

from personal_finance_assistant.data_model import Transaction, validate_transaction

ACCOUNT_FILE = Path.home() / ".personal_finance_assistant" / "account.json"


def load_transactions() -> list[Transaction]:
    # Read every transaction from the account file. If the file doesn't
    # exist yet, there simply are no transactions yet.
    if not ACCOUNT_FILE.exists():
        return []

    with open(ACCOUNT_FILE, encoding="utf-8") as f:
        rows = json.load(f)

    transactions = []
    for row in rows:
        transactions.append(Transaction.from_row(row))
    return transactions


def save_transactions(transactions: list[Transaction]) -> None:
    # Write the whole list back to the account file, as a JSON list of dicts.
    ACCOUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
    rows = [tx.to_row() for tx in transactions]
    with open(ACCOUNT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def add_transaction(tx: Transaction) -> None:
    # Load everything, add the new transaction, save everything again.
    transactions = load_transactions()
    transactions.append(tx)
    save_transactions(transactions)


def delete_transaction(tx_id: str) -> bool:
    # Keep every transaction whose id is NOT the one we want to delete.
    # Returns True if a transaction was actually found and removed.
    transactions = load_transactions()
    remaining = []
    found = False
    for tx in transactions:
        if tx.id == tx_id:
            found = True
        else:
            remaining.append(tx)

    if found:
        save_transactions(remaining)
    return found


def edit_transaction(tx_id: str, changes: dict) -> bool:
    # Find the transaction with this id and replace some of its fields.
    # Example: edit_transaction("a1b2c3d4", amount=50, note="corrected")
    # Returns True if the transaction was found and updated.
    transactions = load_transactions()
    found = False
    updated_transactions = []

    for tx in transactions:
        if tx.id != tx_id:
            updated_transactions.append(tx)
            continue

        found = True
        # Start from the current values, then apply whatever changed.
        new_date = changes.get("date", tx.date)
        new_amount = changes.get("amount", tx.amount)
        new_type = changes.get("type", tx.type)
        new_category = changes.get("category", tx.category)
        new_note = changes.get("note", tx.note)

        errors = validate_transaction(new_amount, new_type, new_category)
        if errors:
            raise ValueError("; ".join(errors))

        updated_tx = Transaction(new_date, new_amount, new_type, new_category, new_note, tx_id)
        updated_transactions.append(updated_tx)

    if found:
        save_transactions(updated_transactions)
    return found


def get_balance() -> float:
    # Sum of all income minus all expenses.
    total = 0.0
    for tx in load_transactions():
        total += tx.signed_amount
    return total


def import_csv(path) -> tuple[int, list[str]]:
    # Add many transactions at once from an external CSV file
    # (same columns as the account file: id,date,type,amount,category,note).
    # Returns (number added, list of error messages for skipped rows).
    transactions = load_transactions()
    added = 0
    errors = []

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row_number = 1
        for row in reader:
            row_number += 1  # row 1 is the header
            try:
                tx = Transaction.from_row(row)
                transactions.append(tx)
                added += 1
            except (ValueError, KeyError) as error:
                errors.append(f"row {row_number}: {error}")

    save_transactions(transactions)
    return added, errors