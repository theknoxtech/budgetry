import database as db
from utils import validate_input, Prompt
from transaction_menu import transaction_menu
from categories_menu import categories_menu
from payees_menu import payees_menu
from rich.console import Console
from style import custom_theme

# TODO from menus.reports_menu import reports_menu

def main():
    db.init_db()
    console = Console(theme=custom_theme)
    Prompt.console = console
    
    while True:
        console.print(
            """
            ##################
            |    Budgetry    |
            ------------------
            |    Main Menu   |
            ##################
            
            """, style="sky_blue1"
            )
        console.print("1. Manage Transactions", style="menu_option")
        
        # TODO Add logic for categorirs_menu
        console.print("2. Manage Categories", style="menu_option") 
        
        # TODO Add logic for payees_menu
        console.print("3. Manage Payees", style="menu_option") 
        
        # TODO Add logic for getting reports1
        console.print("4. Reports", style="menu_option")
        
        # TODO Add logic for exit1
        console.print("5. Exit", style="menu_option")
        
        result = validate_input(["1","2","3","4","5"])
        if result == "1":
            transaction_menu()
            
        elif result == "2":
            
            categories_menu()
        elif result == "3":
            
            payees_menu()
        elif result == "4":
            #reports_menu()
        #elif result == "5":
            exit()
    

main()