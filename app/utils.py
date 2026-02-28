
import os

def validate_input(valid_options):
    while True:
        choice = input("Enter a number for the option you want: ")
        
        if choice in valid_options:
            return choice
        print(f"Invalid input. Please enter one of: {', '.join(valid_options)}")

def clear_terminal():
    if os.name == "nt":
        os.system("cls")
    elif os.name == "posix":
        os.system("clear")
        return
