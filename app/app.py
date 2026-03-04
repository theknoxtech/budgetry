import customtkinter
from models import Budget, Transaction, Category, Payee

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")
        self.title("Budgetry")
        
        self.budget = Budget(name="Main Budget")

class TransactionWindow(customtkinter.CTkToplevel):
    def __init__(self, master, on_save_callback):
        super().__init__(master)
        self.title("Add New Transaction")
        self.geometry("300x400")
        
        self.on_save_callback = on_save_callback
        self.payee = customtkinter.CTkEntry(self, placeholder_text="Payee")
        self.payee.pack(pady=10)
        
        self.amount = customtkinter.CTkEntry(self, placeholder_text="Amount")
        self.amount.pack(pady=10)
        
        # TODO Change to dropdown
        self.category = customtkinter.CTkEntry(self, placeholder_text="Category")
        self.category.pack(pady=10)



if __name__ == "__main__":
    app = App()
    app.mainloop()

