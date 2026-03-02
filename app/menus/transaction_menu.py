from database import Transaction, get_transaction, add_transaction, get_categories
from datetime import date
import uuid
from utils import validate_input, clear_terminal

def transaction_menu():
    while True:
        print(
            """
            ###########################
            #   Manage Transactions   #
            ###########################
            """)
        
        print("1. Add Transaction")
        print("2. Update Transaction")
        print("3. Delete Transaction")
        print("4. View Transactions")
        print("5. Back to Main Menu")
        
        # We pass the valid options for this specific menu
        choice = validate_input(["1", "2", "3","4","5"])
        
        if choice == "1":
            clear_terminal()
            categories = get_categories(names_only=False)
            
            print("--- Available Categories ---")
            for index, category in enumerate(categories, start=1):
                print(f"{index}. {category.name}")
                
            valid_range = [str(num) for num in range(1, len(categories) + 1)]
            category_choice = validate_input(valid_range)
            
            get_category_index = int(category_choice) -1
            get_category_id = categories[get_category_index].name
            
            new_transaction = Transaction(
                id = str(uuid.uuid4()),
                date = str(date.today()),
                payee = input("What company or person did you pay? ").lower(),
                amount = float(input("What is the amount of money spent? ")),
                memo = input("What was this purchase for? ").lower(),
                # TODO add category view when choosing categories
                category_id = get_category_id
            )
            add_transaction(new_transaction)
            print("\nTransaction added successfully!")