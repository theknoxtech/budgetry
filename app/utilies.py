
def validate_input(valid_options):
    choice = input("Enter a number for the option you want: ")
    
    if choice not in valid_options:
        print(f"Invalid input. Please enter one of: {', '.join(valid_options)}")
        return None
    else:
        return choice
