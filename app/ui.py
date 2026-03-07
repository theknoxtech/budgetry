import customtkinter
from utils import validate_input
from database import get_transaction, get_categories, get_payees
from models import Transaction, Category, Payee
from datetime import datetime
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent 
FONT_PATH = BASE_DIR / "assets" / "fonts" / "otf" / "Font Awesome 7 Solid-900.otf"
PNG_PATH = BASE_DIR / "assets" / "fonts" / "icons" / "pngs"

# Background: Ghost White / Space Cadet (Deep Navy)
SIDEBAR_BG = ("#F8F9FA", "#2745A0")
# Sidebar Border: Platinum / Yankee Blue
SIDEBAR_BORDER = ("#DEE2E6", "#2E32B1")
# Button Hover: Light Gray / Navy Blue highlight
BTN_HOVER = ("#E9ECEF", "#4247CE")
# Text Color: Charcoal / Cloud Gray
TEXT_COLOR = ("#212529", "#F8F9FA")
# Accent Color: Vibrant Blue for active buttons/actions
ACCENT_BLUE = ("#3A86FF", "#3A86FF")


class SideBar(customtkinter.CTkFrame):
    def __init__(self, master, open_transaction_window):
        # 1. Initialize with fixed width and no rounded corners for the edge
        super().__init__(master, width=60, corner_radius=0, bg_color=SIDEBAR_BG, border_width=2, border_color=SIDEBAR_BORDER)
        self.grid_propagate(False) # Prevents frame from shrinking
        self.expand_sidebar = False
        
        # 2. Define Sidebar Items (Data-driven approach)
        self.menu_items = [
            {"icon": "plus", "label": "Add Transaction", "cmd": open_transaction_window},
            {"icon": "list", "label": "View Transactions", "cmd": lambda: print("View clicked")},
            {"icon": "tags", "label": "Categories", "cmd": lambda: print("Categories clicked")},
        ]
        self.nav_buttons = [] # Store button objects to update them during toggle
        
        # 3. Load Menu Toggle Icons (Smart Light/Dark objects)
        self.menu_open_icon = customtkinter.CTkImage(
            light_image=Image.open(PNG_PATH / "menu_open_light.png"),
            dark_image=Image.open(PNG_PATH / "menu_open_dark.png"),
            size=(24, 24)
        )
        self.menu_close_icon = customtkinter.CTkImage(
            light_image=Image.open(PNG_PATH / "menu_close_light.png"),
            dark_image=Image.open(PNG_PATH / "menu_close_dark.png"),
            size=(24, 24)
        )
        
        # 4. The Hamburger/Toggle Button
        self.menu_btn = customtkinter.CTkButton(
            self,
            text="",
            image=self.menu_open_icon,
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=BTN_HOVER,
            command=self.toggle_sidebar
        )
        self.menu_btn.grid(row=0, column=0, padx=10, pady=(20, 10))
        
        # 5. Build Navigation Buttons via Loop
        for i, item in enumerate(self.menu_items):
            # Attempt to load light/dark versions of icons
            # Note: Ensure you have 'plus_light.png' and 'plus_dark.png' etc.
            try:
                icon_img = customtkinter.CTkImage(
                    light_image=Image.open(PNG_PATH / f"{item['icon']}_light.png"),
                    dark_image=Image.open(PNG_PATH / f"{item['icon']}_dark.png"),
                    size=(20, 20)
                )
            except Exception:
                # Fallback if specific light/dark files don't exist yet
                icon_img = None 

            btn = customtkinter.CTkButton(
                self, 
                text="",
                image=icon_img, 
                compound="left", 
                anchor="w",
                width=40,
                fg_color="transparent",
                border_color=ACCENT_BLUE,
                border_width=1,
                text_color=TEXT_COLOR,
                hover_color=BTN_HOVER,
                command=item["cmd"]
            )
            btn.grid(row=i + 1, column=0, padx=10, pady=5, sticky="ew")
            self.nav_buttons.append(btn)
        
    def toggle_sidebar(self):
        self.expand_sidebar = not self.expand_sidebar
        
        # Update Sidebar Width
        set_width = 200 if self.expand_sidebar else 60
        self.configure(width=set_width)

        # Update Toggle Icon (Hamburger vs X)
        set_icon = self.menu_close_icon if self.expand_sidebar else self.menu_open_icon
        self.menu_btn.configure(image=set_icon)
        
        # Update all Nav Buttons
        for i, btn in enumerate(self.nav_buttons):
            # Add a space before the label for padding next to the icon
            new_text = f"  {self.menu_items[i]['label']}" if self.expand_sidebar else ""
            btn.configure(text=new_text)

        
        

class ToolBar(customtkinter.CTkFrame):
    def __init__(self,master):
        super().__init__(master)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=0)
        self.grid_columnconfigure(4, weight=0)
        
        summary_btn = customtkinter.CTkButton(self, text="Summary")
        summary_btn.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        placeholder_btn_2 = customtkinter.CTkButton(self, text="Placeholder2")
        placeholder_btn_2.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
        placeholder_btn_3 = customtkinter.CTkButton(self, text="Placeholder3")
        placeholder_btn_3.grid(row=0, column=3, padx=10, pady=10, sticky="e")
        
        placeholder_btn_4 = customtkinter.CTkButton(self, text="Placeholder4")
        placeholder_btn_4.grid(row=0, column=4, padx=10, pady=10, sticky="e")


class OverviewFrame(customtkinter.CTkFrame):
    def __init__(self,master):
        super().__init__(master)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        
        self.total_amount_available_label = customtkinter.CTkLabel(self, text="Total Available Funds")
        self.total_amount_available_label.grid(row=2, column=0)
        self.total_amount_available_frame = customtkinter.CTkFrame(self, height=200, width=300)
        self.total_amount_available_frame.grid(row=3, column=0)
        
        self.amount_spent_label = customtkinter.CTkLabel(self, text="Amount Spent")
        self.amount_spent_label.grid(row=0, column=0)
        self.amount_spent_frame = customtkinter.CTkFrame(self,height=200, width=300)
        self.amount_spent_frame.grid(row=1, column=0)
        
        self.total_income_label = customtkinter.CTkLabel(self, text="Total Monthly Income")
        self.total_income_label.grid(row=0, column=1, padx=2, pady=2)
        self.total_income_frame = customtkinter.CTkFrame(self, height=200, width=300)
        self.total_income_frame.grid(row=1, column=1)
        
        self.total_overspent_label = customtkinter.CTkLabel(self, text="Total Overspent")
        self.total_overspent_label.grid(row=0, column=2, padx=2, pady=2)
        self._overspent_frame = customtkinter.CTkFrame(self, height=200, width=300)
        self._overspent_frame.grid(row=1, column=2)
        
        
        

class TransactionWindow(customtkinter.CTkToplevel):
    def __init__(self, master, on_save_callback, category_map):
        super().__init__(master)
        self.title("Add New Transaction")
        self.geometry("300x400")
        
        self.on_save_callback = on_save_callback
        self.category_map = category_map
        
        # TODO Change to date selector
        
        self.date = customtkinter.CTkEntry(self,placeholder_text="YYYY-MM-DD")
        self.date.pack(pady=10)
        today = datetime.now().strftime("%Y-%m-%d")
        self.date.insert(0,today)
        
        
        # TODO Change to dropdown
        self.payee = customtkinter.CTkEntry(self, placeholder_text="Payee")
        self.payee.pack(pady=10)
        
        # TODO Change to dropdown
        categories = get_categories()
        self.category_map = {category.name: category.id for category in categories}
        self.category_dropdown = customtkinter.CTkOptionMenu(self, values=list(self.category_map.keys()))
        self.category_dropdown.pack(pady=10)
        
        self.memo = customtkinter.CTkEntry(self, placeholder_text="Memo")
        self.memo.pack(pady=10)
        
        self.amount = customtkinter.CTkEntry(self, placeholder_text="Amount")
        self.amount.pack(pady=10)
        
        self.save_button_icon = customtkinter.CTkImage(light_image=Image.open((f"{PNG_PATH}/save.png")), size=(20,20))
        self.save_button = customtkinter.CTkButton(self, text="Save Transaction", image=self.save_button_icon, compound="left", command=self.handle_save)
        self.save_button.pack(pady=20)
        
    def handle_save(self):
        
        date = self.date.get()
        payee = self.payee.get()
        
        selected_category = self.category_dropdown.get()
        category_id = self.category_map.get(selected_category)
        
        memo = self.memo.get()
        amount_input = self.amount.get()
        if not validate_input(amount_input):

            # TODO this needs to be a notification
            print("Invalid entry format: Please use 0.00!")
            return
        
        try:
            clean_amount = amount_input.replace(',', '')
            new_transaction = Transaction(date=date, payee=payee, amount=clean_amount, memo=memo, category_id=category_id)
            self.on_save_callback(new_transaction)
            self.destroy()
        except ValueError:
            print("There was a problem with the amount conversion")
            
        
