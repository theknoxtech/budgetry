
import os
import re
import customtkinter

    

def validate_input(input):
    match_regex = r"\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b"
    
    if re.findall(match_regex, input):
        return True
    else:
        return False

def clear_terminal():
    if os.name == "nt":
        os.system("cls")
    elif os.name == "posix":
        os.system("clear")
        
