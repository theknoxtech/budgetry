from database import Transaction, get_transaction, add_transaction, get_categories, update_transaction
from datetime import date
import uuid
from utils import validate_input, clear_terminal
from rich.table import Table
from rich.console import Console

def transaction_menu():
    while True:
        console = Console()
        print(
            """
            ###########################
            #   Manage Transactions   #
            ###########################
            """)
        
        console.print("1. Add Transaction")
        console.print("2. Update Transaction")
        console.print("3. Delete Transaction")
        console.print("4. View Transactions")
        console.print("5. Back to Main Menu")
        
        choice = validate_input(["1", "2", "3","4","5"])
        
        # Add transaction
        if choice == "1":
            clear_terminal()
            categories = get_categories(names_only=False)
            
            
            console.print("--- Available Categories ---")
            for index, category in enumerate(categories, start=1):
                console.print(f"{index}. {category.name}")
                
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
                category_id = get_category_id
            )
            add_transaction(new_transaction)
            clear_terminal()
            console.print("\nTransaction added successfully!")
            
            # Update transaction
        elif choice == "2":
            clear_terminal()
            transactions = get_transaction()
            
            # Outputs a table of transactions to update
            console = Console()
            transaction_table = Table(title="Transactions")
            transaction_table.add_column("Transaction Number", style="cyan", justify="center")
            transaction_table.add_column("Date", style="magenta", justify="center")
            transaction_table.add_column("Payee", style="yellow", justify="right")
            transaction_table.add_column("Category", style="green", justify="right")
            transaction_table.add_column("Memo", style="white", justify="right")
            transaction_table.add_column("Amount", style="blue", justify="center")
            
            for index, transaction in enumerate(transactions, start=1):
                transaction_table.add_row(
                    str(index),
                    transaction.date,
                    transaction.payee,
                    transaction.category_id,
                    transaction.memo,
                    f"${transaction.amount:.2f}"
                )
            
            clear_terminal()
            console.print(transaction_table)
            
            select_transaction = input("\nEnter the transaction number you want to update ")
            
            # Outputs table with selected transaction
            transaction_index = int(select_transaction) -1
            if 0 <= transaction_index < len(transactions):
                transaction_to_update = transactions[transaction_index]
                
                transaction_update_table = Table(title="Selected Transaction to Update")
                transaction_update_table.add_column("Transaction Number", style="cyan", justify="center")
                transaction_update_table.add_column("Date", style="magenta", justify="center")
                transaction_update_table.add_column("Payee", style="yellow", justify="right")
                transaction_update_table.add_column("Category", style="green", justify="right")
                transaction_update_table.add_column("Memo", style="white", justify="right")
                transaction_update_table.add_column("Amount", style="blue", justify="center")
                transaction_update_table.add_row(
                    str(transaction_to_update.id),
                    transaction_to_update.date,
                    transaction_to_update.payee,
                    transaction_to_update.category_id,
                    transaction_to_update.memo,
                    f"${transaction_to_update.amount:.2f}"
                )
                console.print(transaction_update_table)
                
                # Get current transaction details
                # Asks user to update and if not keeps current data
                # Outputs a new transaction object
                current_transaction = transaction_to_update
                
                if current_transaction:
                    print("\nEditing transaction (Press Enter to Keep Current Data)")
                    new_date = input(f"Current Date ({current_transaction.date}): Enter a new date") or current_transaction.date
                    new_payee = input(f"Current Payee ({current_transaction.payee}): Enter a new payee") or current_transaction.payee
                    new_category = input(f"Current Category ({current_transaction.category_id}): Enter a new category") or current_transaction.category_id
                    new_memo = input(f"Current Memo ({current_transaction.memo}): Enter a new memo") or current_transaction.memo
                    new_amount = input(f"Current Amount ({current_transaction.amount}): Enter a new amount") 
                    input_amount = float(new_amount) if new_amount else current_transaction.amount
                    
                    updated_transaction = Transaction(
                        id = current_transaction.id,
                        date = new_date,
                        payee = new_payee,
                        amount = input_amount,
                        memo = new_memo,
                        category_id = new_category
                    )
                    update_transaction(updated_transaction)
                    print("\nTransaction updated successfully")