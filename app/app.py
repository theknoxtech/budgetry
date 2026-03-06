import customtkinter
from models import Budget, Transaction, Category, Payee
from database import get_categories, add_transaction
from datetime import datetime
from utils import validate_input
from ui import Sidebar, Toolbar, MainView

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")
        self.title("Budgetry")
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=0)
        
        # Toolbar
        self.toolbar = Toolbar(master=self)
        self.toolbar.grid(row=0, column=0, sticky="ew", columnspan=2)
        
        # Sidebar
        self.sidebar = Sidebar(master=self)
        self.sidebar.grid(row=1,column=0,sticky="nsw")
        
        self.mainview = MainView(master=self)
        self.mainview.grid(row=1, column=0, sticky="ew", columnspan=2)
        
        self.budget = Budget(name="Main Budget")

        # TODO Create button class in UI.py
        self.add_transaction_btn = customtkinter.CTkButton(self, text="Add Transaction", command=self.open_transaction_window)
        #self.add_transaction_btn.pack(pady=20)
        
    def open_transaction_window(self):
        categories = get_categories()
        category_map = {category.name: category.id for category in categories}
        self.transaction_window = TransactionWindow(self, self.handle_save_success, category_map)
    
    def handle_save_success(self, transaction):
        add_transaction(transaction)
        # TODO this needs to be a notifcation
        print("Transaction has been saved!")
        

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
        
        self.save_button = customtkinter.CTkButton(self, text="Save Transaction", command=self.handle_save)
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
            
        
        
        



if __name__ == "__main__":
    app = App()
    app.mainloop()

