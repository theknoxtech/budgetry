import customtkinter
import utils


class Sidebar(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        #self.grid_columnconfigure(0, weight=0)
        #self.grid_rowconfigure(1, weight=0)
        #self.grid_rowconfigure(2, weight=0)
        #self.grid_rowconfigure(3, weight=0)
        #self.grid_rowconfigure(4, weight=0)
        #self.grid_rowconfigure(5, weight=0)
        #self.grid_rowconfigure(6, weight=0)
        
        view_transaction_btn  = customtkinter.CTkButton(self, text="View Transactions")
        view_transaction_btn.grid(row=1, column=0, padx=10, pady=10)
        
        category_btn = customtkinter.CTkButton(self, text="Categories")
        category_btn.grid(row=2, column=0, padx=10, pady=10)

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
        
class MainView(customtkinter.CTkFrame):
    def __init__(self,master):
        super().__init__(master)
        
        #self.grid_columnconfigure(1, weight=1)
        #self.grid_rowconfigure(1, weight=1)
        
        mainView_btn_1 = customtkinter.CTkButton(self, text="Main View Placeholder")
        mainView_btn_1.grid(padx=10, pady=10)
        
