"""Account: stores transactions in a JSON file, with add, delete, edit and import."""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

from personal_finance_assistant.data_model import Transaction, validate_transaction

ACCOUNT_FILE = Path.home() / ".personal_finance_assistant" / "account.json"

class AccountFileError(Exception):
    """The account file exists but cannot be read (e.g. damaged JSON)."""

def load_transactions() -> list[Transaction]:
    # Read every transaction from the account file. If the file doesn't
    # exist yet, there simply are no transactions yet.
    path = ACCOUNT_FILE
    if not path.exists():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        return [Transaction.from_row(row) for row in rows]
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as error:
        raise AccountFileError(
            f"The account file {path} is damaged and cannot be read ({error})."
        ) from error


def backup_path():
    # account.json -> account.json.bak, next to the account file
    return ACCOUNT_FILE.with_name(ACCOUNT_FILE.name + ".bak")


def save_transactions(transactions) -> None:
    # Write the whole list back to the account file, as a JSON list of dicts.
    path = ACCOUNT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    # Keep the last good version before overwriting it.
    if path.exists():
        backup_path().write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    # Write to a temporary file first, then swap it in with one step,
    # so the account file is never left half-written.
    temp_path = path.with_name(path.name + ".tmp")
    rows = [tx.to_row() for tx in transactions]
    temp_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    os.replace(temp_path, path)


def restore_backup() -> bool:
    # Replace the damaged account file with the backup, if the backup is readable.
    # Returns True if it worked.
    backup = backup_path()
    if not backup.exists():
        return False

    try:
        text = backup.read_text(encoding="utf-8")
        rows = json.loads(text)
        [Transaction.from_row(row) for row in rows]  # only to check the backup is valid
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return False
    ACCOUNT_FILE.write_text(text, encoding="utf-8")
    return True


def move_damaged_file_aside():
    # Rename the damaged file (never delete it) so a new, empty account can start.
    # Returns the new path of the damaged file.
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    damaged_path = ACCOUNT_FILE.with_name(f"{ACCOUNT_FILE.stem}.damaged-{stamp}.json")
    os.replace(ACCOUNT_FILE, damaged_path)
    return damaged_path


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


def read_csv(path) -> tuple[list[Transaction], list[str]]:
    # Read transactions from a CSV file WITHOUT saving them anywhere.
    # Columns: date,type,amount,category,note (id is optional).
    # Returns (valid transactions, list of error messages for skipped rows).
    transactions = []
    errors = []

    # Read CSV files also saved by Excel.
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        row_number = 1
        for row in reader:
            row_number += 1  # row 1 is the header
            try:
                transactions.append(Transaction.from_row(row))

            except (ValueError, KeyError, TypeError, AttributeError) as error:
                errors.append(f"row {row_number}: {error}")

    return transactions, errors


def import_csv(path) -> tuple[int, list[str]]:
    # Add many transactions at once from an external CSV file
    # (same columns as the account file: id,date,type,amount,category,note).
    # Returns (number added, list of error messages for skipped rows).
    new_transactions, errors = read_csv(path)
    if new_transactions:
        save_transactions(load_transactions() + new_transactions)
    return len(new_transactions), errors

