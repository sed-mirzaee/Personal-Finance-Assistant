"""Command-line interface."""

from personal_finance_assistant.settings import (
    add_category, format_settings, load_settings,
    remove_category, save_settings, set_value,
)

WELCOME = "Welcome to Personal Finance Assistant!"
GOODBYE = "\nGoodbye!"

# Menu 1: always shown at startup.
SHORT_MENU = "Enter a command, 'help' for the full list, or 'exit' to quit."

# Menu 2: shown only when the user types 'help'.
FULL_MENU = """\

Available commands in PFA(Personal Finance Assistant):
  settings  show settings
  help   show this full list
  exit   quit the program
  """

def cmd_show_recommendations():
    pass

def cmd_get_file():
    pass

def cmd_get_transactions():
    pass

def cmd_predict_balance():
    pass

def cmd_show_summary():
    pass

def cmd_set_balance():
    pass

def cmd_get_balance():
    pass

def cmd_add_transaction():
    pass




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

        else:
            print(f"Unknown command: '{command}'. Type 'help' to see the options.")

# Entry point of project.scripts
def main():
    run_main_menu()

if __name__ == "__main__":
    main()