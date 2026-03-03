from utils import validate_input, Prompt, clear_terminal
import database as db
import uuid
from rich.console import Console
from style import custom_theme

clear_terminal()
def payees_menu():
    console = Console(theme=custom_theme)
    Prompt.console = console
    
    while True:
        console.print(
            """
            ##################### 
            #   Manage Payees   #
            #####################
            """, style="sky_blue1")
        
        console.print("1. Add Payee", style="menu_option")
        console.print("2. Update Payee", style="menu_option")
        console.print("3. Delete Payee", style="menu_option")
        console.print("4. View Payeed", style="menu_option")
        console.print("5. Back to Main Menu", style="menu_option")
        
        # We pass the valid options for this specific menu
        choice = validate_input(["1", "2", "3","4","5"])

        if choice == "1":
            # TODO: FIX BUG - This is currently creating a Category, but it should create a Payee object
            new_category = db.Category(
                id = str(uuid.uuid4()),
                name = Prompt.ask("what do you want to name this category?").lower(),
                budgeted = 0.00,
                activity = 0.00,
                available = 0.00
            )
            db.add_category(new_category)
            # TODO: Call db.add_payee(new_payee) instead of add_category

        # TODO: Implement logic for Option 2: Update Payee
        # elif choice == "2":

        # TODO: Implement logic for Option 3: Delete Payee
        # elif choice == "3":

        # TODO: Implement logic for Option 4: View Payees
        # elif choice == "4":

        elif choice == "5":
            break