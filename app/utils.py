
import os
from rich.console import Console
from rich.prompt import Prompt as RichPrompt
from style import custom_theme

console = Console(theme=custom_theme)

class Prompt(RichPrompt):
    @classmethod
    def ask(cls, *args, **kwargs):
        if "console" not in kwargs:
            kwargs["console"] = console
        return super().ask(*args, **kwargs)


def validate_input(valid_options):
    while True:
        choice = Prompt.ask("[prompt]Enter a number for the option you want[/]")
        
        if choice in valid_options:
            return choice
        console.print(f"Invalid input. Please enter one of: {', '.join(valid_options)}", style="warning")

def clear_terminal():
    if os.name == "nt":
        os.system("cls")
    elif os.name == "posix":
        os.system("clear")
        return
