from app.utilies import validate_input
import database as db
import uuid

def categories_menu():
    while True:
        print(
            """
            ###########################
            #   Manage Categories   #
            ###########################
            """)
        
        print("1. Add Category")
        print("2. Update Category")
        print("3. Delete Category")
        print("4. View Categories")
        print("5. Back to Main Menu")
        
        # We pass the valid options for this specific menu
        choice = validate_input(["1", "2", "3","4","5"])

        if choice == "1":
            new_category = db.Category(
                id = str(uuid.uuid4()),
                name = input("what do you want to name this category? ").lower(),
                budgeted = 0.00,
                activity = 0.00,
                available = 0.00
            )
            db.add_category(new_category)