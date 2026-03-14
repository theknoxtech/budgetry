from utils import validate_input, Prompt, clear_terminal
from database import Category, add_category
import uuid
from rich.console import Console
from style import custom_theme

clear_terminal()
def categories_menu():
    console = Console(theme=custom_theme)
    Prompt.console = console
    
    while True:
        console.print(
            """
            ###########################
            #   Manage Categories   #
            ###########################
            """, style="sky_blue1")
        
        console.print("1. Add Category", style="menu_option")
        console.print("2. Update Category", style="menu_option")
        console.print("3. Delete Category", style="menu_option")
        console.print("4. View Categories", style="menu_option")
        console.print("5. Back to Main Menu", style="menu_option")
        
        # We pass the valid options for this specific menu
        choice = validate_input(["1", "2", "3","4","5"])

        if choice == "1":
            new_category = Category(
                id = str(uuid.uuid4()),
                name = Prompt.ask("what do you want to name this category?"),
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