from database import Transaction, Category, save_transaction, save_category, get_transaction, get_categories
from datetime import date
import uuid

def validate_input():
    choice = input("Enter a number for the option you want: ")
    valid_input = ["1","2","3","4","5"]
    
    if choice not in valid_input:
        raise TypeError("Please enter a number between 1 - 5")
    else:
        return choice

def main():
    while True:
        print(
            """
            ##################
            #### Budgetry ####
            ##################
            """)
        print("1. Add Transaction")
        
        # TODO Add logic for adding category
        print("2. Add Category") 
        
        # TODO Add logic for getting transactions
        # TODO Add logic to get transactions by month
        print("3. Get Transactions") 
        
        # TODO Add logic for getting categories
        print("4. Get Categories")
        
        # TODO Add logic for exit
        print("5. Exit")
        
        result = validate_input()
        # Logic for Option 1 Adding Trasaction 
        if result == "1":
            new_tranaction = Transaction(
                id = str(uuid.uuid4()),
                date = str(date.today()),
                payee = input("What company or person did you pay? "),
                amount = float(input("what is the amount of money spent? ")),
                memo = input("What was this purchase for? This is for the memo field "),
                
                # TODO Check if category exists or if needs to be created
                category_id = input("What category should this transaction be placed in? ")
            )
            save_transaction(new_tranaction)
            
        # Logic for Option 2 Adding Category
        elif result == "2":
            new_category = Category(
                id = str(uuid.uuid4()),
                name = input("what do you want to name this category? "),
                budgeted = 0.00,
                activity = 0.00,
                available = 0.00
            )
            save_category(new_category)

main()