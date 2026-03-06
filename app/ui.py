import customtkinter
from utils import validate_input
from database import get_transaction, get_categories, get_payees
from models import Transaction, Category, Payee
from datetime import datetime


class Sidebar(customtkinter.CTkFrame):
    def __init__(self, master, open_transaction_window):
        super().__init__(master)
        
        #self.grid_columnconfigure(0, weight=0)
        #self.grid_rowconfigure(1, weight=0)
        #self.grid_rowconfigure(2, weight=0)
        #self.grid_rowconfigure(3, weight=0)
        #self.grid_rowconfigure(4, weight=0)
        #self.grid_rowconfigure(5, weight=0)
        #self.grid_rowconfigure(6, weight=0)
        
        
        self.add_transaction_btn = customtkinter.CTkButton(self, text="Add Transaction", command=open_transaction_window)
        self.add_transaction_btn.grid(row=1, column=0, padx=10, pady=10)
        
        self.view_transaction_btn  = customtkinter.CTkButton(self, text="View Transactions")
        self.view_transaction_btn.grid(row=2, column=0, padx=10, pady=10)
        
        self.category_btn = customtkinter.CTkButton(self, text="Categories")
        self.category_btn.grid(row=3, column=0, padx=10, pady=10)

class Toolbar(customtkinter.CTkFrame):
    def __init__(self,master):
        super().__init__(master)
        
        #self.grid_rowconfigure(0, weight=1)
        #self.grid_columnconfigure(0, weight=1)
        #self.grid_columnconfigure(1, weight=1)
        #self.grid_columnconfigure(2, weight=1)
        #self.grid_columnconfigure(3, weight=1)
        
        placeholder_btn_1 = customtkinter.CTkButton(self, text="Placeholder")
        placeholder_btn_1.grid(row=0, column=0, padx=10, pady=10)
        
        placeholder_btn_2 = customtkinter.CTkButton(self, text="Placeholder")
        placeholder_btn_2.grid(row=0, column=1, padx=10, pady=10)
        
        placeholder_btn_3 = customtkinter.CTkButton(self, text="Placeholder")
        placeholder_btn_3.grid(row=0, column=2, padx=10, pady=10)
        
        placeholder_btn_4 = customtkinter.CTkButton(self, text="Placeholder")
        placeholder_btn_4.grid(row=0, column=3, padx=10, pady=10)
        
class Overview(customtkinter.CTkFrame):
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
            
        
