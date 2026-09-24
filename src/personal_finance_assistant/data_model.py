"""Data model."""

import uuid
from dataclasses import dataclass, field
from datetime import date

INCOME = "income"
EXPENSE = "expense"
TRANSACTION_TYPES = (INCOME, EXPENSE)


def _new_id() -> str:
    # Unique 8 character id, e.g. 'a1b2c3d4'
    return uuid.uuid4().hex[:8]

def validate_transaction(amount: float, type_: str, category: str) -> list[str]:
    # Check raw transaction data before creating a Transaction.
    # Returns a list of error messages; an empty list means the data is valid.

    errors = []
    if type_ not in TRANSACTION_TYPES:
        errors.append(f"type must be one of {TRANSACTION_TYPES}, got '{type_}'")
    if amount <= 0:
        errors.append(f"amount must be positive, got {amount}")
    if not category.strip():
        errors.append("category must not be empty")
    return errors

@dataclass
class Transaction:
    # One money movement. Amount is always positive; `type` gives the direction.

    date: date
    amount: float
    type: str
    category: str
    note: str = ""
    id: str = field(default_factory=_new_id)

    @property
    def signed_amount(self) -> float:
        # Amount for computations: positive for income, negative for expense.
        return self.amount if self.type == INCOME else -self.amount

    @staticmethod
    def to_row(self) -> dict:
        # Convert to a dict of strings, ready for csv.DictWriter.
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "type": self.type,
            "amount": self.amount,
            "category": self.category,
            "note": self.note,
        }

    def from_row(row: dict) -> "Transaction":
        # Build a Transaction from a dict of strings, as read by csv.DictReader.
        # Raises ValueError (with all problems joined together) if the row is invalid.

        tx_date = date.fromisoformat(row["date"].strip())
        amount = float(row["amount"])
        tx_type = row["type"].strip().lower()
        category = row["category"].strip().lower()
        note = row.get("note", "").strip()
        tx_id = row.get("id", "").strip() or _new_id()

        errors = validate_transaction(amount, tx_type, category)
        if errors:
            raise ValueError("; ".join(errors))

        return Transaction(tx_date, amount, tx_type, category, note, tx_id)
