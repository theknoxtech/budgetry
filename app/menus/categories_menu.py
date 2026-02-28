from utils import validate_input
from database import Category, add_category
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
            new_category = Category(
                id = str(uuid.uuid4()),
                name = input("what do you want to name this category? ").lower(),
                budgeted = 0.00,
                activity = 0.00,
                available = 0.00
            )
            add_category(new_category)

        # TODO: Implement logic for Option 2: Update Category
        # elif choice == "2":

        # TODO: Implement logic for Option 3: Delete Category
        # elif choice == "3":

        # TODO: Implement logic for Option 4: View Categories
        # elif choice == "4":
            # Call get_categories() and print them nicely

        elif choice == "5":
            break