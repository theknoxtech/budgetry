import customtkinter
from models import Budget, Transaction, Category, Payee
from database import get_categories, add_transaction
from datetime import datetime
from utils import validate_input
from ui import SideBar, ToolBar, OverviewFrame, TransactionWindow

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1100x700")
        self.title("Budgetry")
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        
        # Toolbar
        self.toolbar = ToolBar(master=self)
        self.toolbar.grid(row=0, column=1, sticky="ne")
        
        # Sidebar
        self.sidebar = SideBar(master=self, open_transaction_window=self.open_transaction_window)
        self.sidebar.grid(row=0,column=0,rowspan=2, sticky="nsew")
        
        # Overview
        self.overview = OverviewFrame(master=self)
        self.overview.grid(row=1, column=1, sticky="nsew")
        
        
        
        #self.budget = Budget(name="Main Budget")
        
    def open_transaction_window(self):
        categories = get_categories()
        category_map = {category.name: category.id for category in categories}
        self.transaction_window = TransactionWindow(self, self.handle_save_success, category_map)
        
    
    def handle_save_success(self, transaction):
        add_transaction(transaction)
        # TODO this needs to be a notifcation
        print("Transaction has been saved!")



if __name__ == "__main__":
    app = App()
    app.mainloop()

