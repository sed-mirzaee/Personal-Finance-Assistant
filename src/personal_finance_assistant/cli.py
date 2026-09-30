"""Command-line interface."""

from datetime import date, datetime
from pathlib import Path

from personal_finance_assistant.account import (
    AccountFileError,
    add_transaction,
    delete_transaction,
    edit_transaction,
    get_balance,
    import_csv,
    load_transactions,
    move_damaged_file_aside,
    restore_backup,
)
from personal_finance_assistant.analysis import (
    find_recurring_transactions,
    generate_recommendations,
    predict_balance,
)
from personal_finance_assistant.charts import save_overview_chart
from personal_finance_assistant.data_model import Transaction, validate_transaction
from personal_finance_assistant.settings import (
    add_category,
    format_settings,
    load_settings,
    remove_category,
    set_value,
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
  import     import transactions from a CSV file (see examples/sample_transactions.csv)
  balance    show current balance
  list       show all transactions
  recurring  detect recurring monthly payments
  predict    predict balance N months ahead
  recommend  get saving, spending and investment suggestions
  chart      save an overview image with four charts as a PNG file
  settings   show and change categories and limits
  help       show this full list
  exit       quit the program

If your account file is damaged, the program will offer to 'restore'
the last backup or 'reset' to a new account. You don't need a command for that.
  """


def load_transactions_or_warn():
    # Returns the transactions, or None (after printing a message) if there are none.
    transactions = load_transactions()
    if not transactions:
        print("No transactions yet. Add or import some first, then try again.")
        return None
    return transactions


def handle_damaged_account(error):
    print(error)
    print("  restore  go back to the last saved backup")
    print("  reset    start a new, empty account (the damaged file is kept aside)")
    print("  (anything else: leave it and fix the file yourself)")
    choice = input("  what do you want to do? ").strip().lower()

    if choice == "restore":
        if restore_backup():
            print("Backup restored. You can continue.")
        else:
            print("No usable backup found. Try 'reset' or fix the file yourself.")
    elif choice == "reset":
        damaged_path = move_damaged_file_aside()
        print(f"Started a new account. The damaged file was saved as {damaged_path}")
    else:
        print("Nothing was changed.")


def cmd_show_chart():
    transactions = load_transactions_or_warn()
    if transactions is None:
        return

    try:
        path = save_overview_chart(transactions=transactions)
    except OSError as error:
        print(f"Could not save the chart: {error}")
        print("If the image is open in another program, close it and try again.")
        return

    print(f"Chart saved to {path}")

def cmd_show_recurring() -> None:
    transactions = load_transactions_or_warn()
    if transactions is None:
        return

    recurring = find_recurring_transactions(transactions=transactions)
    if not recurring:
        print("No recurring payments detected yet.")
        return
    for item in recurring:
        print(f"{item['type']:7s} {item['category']:15s} avg {item['average_amount']:.2f} "
              f"every ~{item['average_interval_days']:.0f} days ({item['occurrences']} times)")


def cmd_predict_balance() -> None:
    transactions = load_transactions_or_warn()
    if transactions is None:
        return

    months_text = input("  months ahead (default 1): ").strip()
    try:
        months = int(months_text) if months_text else 1
    except ValueError:
        print(f"Invalid number of months: '{months_text}'")
        return

    if months < 1:
        print("Invalid number of months: must be 1 or more")
        return

    predicted = predict_balance(months, transactions=transactions)
    print(f"Predicted balance in {months} month(s): {predicted:+.2f}")


def cmd_show_recommendations() -> None:
    transactions = load_transactions_or_warn()
    if transactions is None:
        return

    for line in generate_recommendations(transactions=transactions):
        print(f"- {line}")

def cmd_add_transaction() -> None:
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
        tx_date = date.fromisoformat(date_text) if date_text else datetime.now().astimezone().date()
    except ValueError:
        print(f"Not added: date must be YYYY-MM-DD, got '{date_text}'")
        return

    note = input("  note (optional): ").strip()

    tx = Transaction(tx_date, amount, tx_type, category, note)
    add_transaction(tx)
    print(f"Added {tx_type} of {amount:.2f} ({category}) on {tx_date}  [id: {tx.id}]")


def cmd_get_transactions() -> None:
    transactions = load_transactions()
    if not transactions:
        print("No transactions yet.")
        return
    for tx in transactions:
        print(f"{tx.id}  {tx.date}  {tx.type:7s}  {tx.amount:10.2f}  {tx.category:15s}  {tx.note}")


def cmd_delete_transaction() -> None:
    tx_id = input("  id of transaction to delete: ").strip()
    if delete_transaction(tx_id):
        print(f"Deleted transaction {tx_id}")
    else:
        print(f"Not deleted: no transaction with id '{tx_id}'")


def cmd_edit_transaction() -> None:
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


def cmd_import() -> None:
    path_text = input("  path to CSV file: ").strip()
    path = Path(path_text)

    if not path_text or not path.is_file():
        print(f"Not imported: no file found at '{path.resolve()}'")
        return

    added, errors = import_csv(path)

    print(f"Imported {added} transaction(s).")

    for error in errors:
        print(f"  skipped {error}")


def cmd_get_balance() -> None:
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
        choice = input("pfa-settings> ").strip().lower()
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


def cmd_show_help() -> None:
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

        try:
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

            elif command == "chart":
                cmd_show_chart()

            else:
                print(f"Unknown command: '{command}'. Type 'help' to see the options.")


        except AccountFileError as error:
            handle_damaged_account(error)
            
        except (EOFError, KeyboardInterrupt):
            print(GOODBYE)
            break

# Entry point of project.scripts
def main() -> None:
    run_main_menu()

if __name__ == "__main__":
    main()