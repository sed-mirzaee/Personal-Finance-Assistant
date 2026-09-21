"""Command-line interface."""

WELCOME = "Welcome to Personal Finance Assistant!"
GOODBYE = "\nGoodbye!"

# Menu 1: always shown at startup.
SHORT_MENU = "Enter a command, 'help' for the full list, or 'exit' to quit."

# Menu 2: shown only when the user types 'help'.
FULL_MENU = """\

Available commands in PFA(Personal Finance Assistant):
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

def cmd_show_help():
    print(FULL_MENU)

def cmd_settings():
    pass

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

        else:
            print(f"Unknown command: '{command}'. Type 'help' to see the options.")

# Entry point of project.scripts
def main():
    run_main_menu()

if __name__ == "__main__":
    main()