import database as db
from utils import validate_input, clear_terminal
from menus.transaction_menu import transaction_menu
from menus.categories_menu import categories_menu
from menus.payees_menu import payees_menu
#from menus.reports_menu import reports_menu

def main():
    db.init_db()
    
    while True:
        print(
            """
            ##################
            |    Budgetry    |
            ------------------
            |    Main Menu   |
            ##################
            
            """
            )
        print("1. Manage Transactions")
        
        # TODO Add logic for categorirs_menu
        print("2. Manage Categories") 
        
        # TODO Add logic for payees_menu
        print("3. Manage Payees") 
        
        # TODO Add logic for getting reports
        print("4. Reports")
        
        # TODO Add logic for exit
        print("5. Exit")
        
        result = validate_input(["1","2","3","4","5"])
        # Logic for Option 1 Adding Trasaction 
        if result == "1":
            clear_terminal()
            transaction_menu()
        elif result == "2":
            clear_terminal()
            categories_menu()
        elif result == "3":
            clear_terminal()
            payees_menu()
        elif result == "4":
            clear_terminal()
            #reports_menu()
        elif result == "5":
            exit()
    

main()