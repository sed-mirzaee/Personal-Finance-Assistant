"""Command-line interface."""

from datetime import date
from pathlib import Path

from personal_finance_assistant.account import (
    add_transaction, delete_transaction, edit_transaction,
    get_balance, import_csv, load_transactions,
)

from personal_finance_assistant.data_model import Transaction, validate_transaction

from personal_finance_assistant.settings import (
    add_category, format_settings, load_settings,
    remove_category, save_settings, set_value,
)

from personal_finance_assistant.analysis import (
    find_recurring_transactions, generate_recommendations, predict_balance,
)

WELCOME = "Welcome to Personal Finance Assistant!"
GOODBYE = "\nGoodbye!"

# Menu 1: always shown at startup.
SHORT_MENU = "Enter a command, 'help' for the full list, or 'exit' to quit."

# Menu 2: shown only when the user types 'help'.
FULL_MENU = """\

Available commands in PFA (Personal Finance Assistant):
  add        add a transaction
  delete     delete a transaction by id
  edit       edit a transaction by id
  import     import transactions from a CSV file
  balance    show current balance
  list       show all transactions
  recurring  detect recurring monthly payments
  predict    predict balance N months ahead
  recommend  get savings/spending suggestions
  settings   show and change categories and limits
  help       show this full list
  exit       quit the program
  """


def cmd_get_file():
    pass

def cmd_show_summary():
    pass

def cmd_set_balance():
    pass

def cmd_show_recurring():
    recurring = find_recurring_transactions()
    if not recurring:
        print("No recurring payments detected yet.")
        return
    for item in recurring:
        print(f"{item['type']:7s} {item['category']:15s} avg {item['average_amount']:.2f} "
              f"every ~{item['average_interval_days']:.0f} days ({item['occurrences']} times)")


def cmd_predict_balance():
    months_text = input("  months ahead (default 1): ").strip()
    try:
        months = int(months_text) if months_text else 1
    except ValueError:
        print(f"Invalid number of months: '{months_text}'")
        return
    predicted = predict_balance(months)
    print(f"Predicted balance in {months} month(s): {predicted:+.2f}")


def cmd_show_recommendations():
    for line in generate_recommendations():
        print(f"- {line}")

def cmd_add_transaction():
    settings = load_settings()
    tx_type = input("  income or expense? ").strip().lower()
    key = f"{tx_type}_categories"
    if key not in settings:
        print("Not added: type must be 'income' or 'expense'")
        return

    print(f"  categories: {', '.join(settings[key])}")
    category = input("  category: ").strip().lower()
    if category not in settings[key]:
        print(f"Not added: '{category}' is not a known {tx_type} category (add it in settings first)")
        return

    amount_text = input("  amount: ").strip()
    try:
        amount = float(amount_text)
    except ValueError:
        print(f"Not added: amount must be a number, got '{amount_text}'")
        return

    errors = validate_transaction(amount, tx_type, category)
    if errors:
        print("Not added: " + "; ".join(errors))
        return

    date_text = input("  date (YYYY-MM-DD, blank = today): ").strip()
    try:
        tx_date = date.fromisoformat(date_text) if date_text else date.today()
    except ValueError:
        print(f"Not added: date must be YYYY-MM-DD, got '{date_text}'")
        return

    note = input("  note (optional): ").strip()

    tx = Transaction(tx_date, amount, tx_type, category, note)
    add_transaction(tx)
    print(f"Added {tx_type} of {amount:.2f} ({category}) on {tx_date}  [id: {tx.id}]")


def cmd_get_transactions():
    transactions = load_transactions()
    if not transactions:
        print("No transactions yet.")
        return
    for tx in transactions:
        print(f"{tx.id}  {tx.date}  {tx.type:7s}  {tx.amount:10.2f}  {tx.category:15s}  {tx.note}")


def cmd_delete_transaction():
    tx_id = input("  id of transaction to delete: ").strip()
    if delete_transaction(tx_id):
        print(f"Deleted transaction {tx_id}")
    else:
        print(f"Not deleted: no transaction with id '{tx_id}'")


def cmd_edit_transaction():
    tx_id = input("  id of transaction to edit: ").strip()
    print("  Leave a field blank to keep it unchanged.")
    changes = {}

    amount_text = input("  new amount: ").strip()
    if amount_text:
        try:
            changes["amount"] = float(amount_text)
        except ValueError:
            print(f"Not edited: amount must be a number, got '{amount_text}'")
            return

    type_text = input("  new type (income/expense): ").strip().lower()
    if type_text:
        changes["type"] = type_text

    category_text = input("  new category: ").strip().lower()
    if category_text:
        changes["category"] = category_text

    note_text = input("  new note: ").strip()
    if note_text:
        changes["note"] = note_text

    if not changes:
        print("Nothing to change.")
        return

    try:
        edited = edit_transaction(tx_id, changes)
    except ValueError as error:
        print(f"Not edited: {error}")
        return

    if edited:
        print(f"Updated transaction {tx_id}")
    else:
        print(f"Not edited: no transaction with id '{tx_id}'")


def cmd_import():
    path = Path(input("  path to CSV file: ").strip())

    if not path.exists():
        print(f"Not imported: file '{path}' does not exist")
        return

    added, errors = import_csv(path)

    print(f"Imported {added} transaction(s).")

    for error in errors:
        print(f"  skipped {error}")


def cmd_get_balance():
    print(f"Current balance: {get_balance():+.2f}")


SETTINGS_HELP = """Change settings: 
    add-cat
    remove-cat 
    set 
    back """

def cmd_settings() -> None:

    # Show the settings, then let the user change them or 'back'.
    print(format_settings())
    print(SETTINGS_HELP)

    while True:
        choice = input(f"pfa-settings> ").strip().lower()
        try:
            if choice == "back":
                break

            elif choice == "add-cat":
                add_category(input("  income or expense? ").strip().lower(),
                             input("  new category name: "))

            elif choice == "remove-cat":
                remove_category(input("  income or expense? ").strip().lower(),
                                input("  category to remove: "))

            elif choice == "set":
                set_value(input("  setting name: ").strip(),
                          input("  new value: ").strip())

            else:
                print(f"Unknown choice: '{choice}'.")
                continue

        except ValueError as error:
            print(f"Not changed: {error}")
            continue


def cmd_show_help():
    print(FULL_MENU)

def run_main_menu() -> None:

    """Show welcome + short menu, then read commands until 'exit'."""
    print(WELCOME)
    print(SHORT_MENU)

    while True:

        try:
            full_command = input("pfa> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(GOODBYE)
            break

        command_args = full_command.split()
        if not command_args: #Empty line
            print(SHORT_MENU)
            continue

        command = command_args[0].lower()

        if command == "exit":
            print(GOODBYE)
            break

        elif command == "help":
            cmd_show_help()

        elif command == "settings":
            cmd_settings()

        elif command == "add":
            cmd_add_transaction()

        elif command == "delete":
            cmd_delete_transaction()

        elif command == "edit":
            cmd_edit_transaction()

        elif command == "import":
            cmd_import()

        elif command == "balance":
            cmd_get_balance()

        elif command == "list":
            cmd_get_transactions()

        elif command == "recurring":
            cmd_show_recurring()

        elif command == "predict":
            cmd_predict_balance()

        elif command == "recommend":
            cmd_show_recommendations()

        else:
            print(f"Unknown command: '{command}'. Type 'help' to see the options.")

# Entry point of project.scripts
def main():
    run_main_menu()

if __name__ == "__main__":
    main()