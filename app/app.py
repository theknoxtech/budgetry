import customtkinter
from models import Budget, Transaction, Category, Payee
from database import get_categories
from datetime import datetime
from utils import validate_input

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")
        self.title("Budgetry")
        
        self.budget = Budget(name="Main Budget")
        
        

class TransactionWindow(customtkinter.CTkToplevel):
    def __init__(self, master, on_save_callback, categories):
        super().__init__(master)
        self.title("Add New Transaction")
        self.geometry("300x400")
        
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
        
        self.on_save_callback = on_save_callback
        self.save_button = customtkinter.CTkButton(self, placeholder_text="Save Transaction", command=self.handle_save)
        self.save_button.pack(pady=20)
        
    def handle_save(self):
        
        date = self.date.get()
        payee = self.payee.get()
        
        selected_category = self.category_dropdown.get()
        category_id = self.category_map.get(selected_category)
        
        memo = self.memo.get()
        amount = float(self.amount.get())
        
        new_transaction = Transaction(date, payee, amount, memo, category_id)
        self.on_save_callback(new_transaction)
        self.destroy()
        
        
        
        



if __name__ == "__main__":
    app = App()
    app.mainloop()

