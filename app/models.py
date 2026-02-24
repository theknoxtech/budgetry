from dataclasses import dataclass, field

@dataclass
class transaction:
    id: str
    date: str
    payee: str
    amount: float
    memo: str
    category_id: str

@dataclass
class category:
    id: str
    name: str
    budgeted: float
    activity: float
    available: float

@dataclass
class budget:
    name: str
    categories: list[str] = field(default_factory=list)
    transactions: list[str] = field(default_factory=list)
    
    def add_category(self, category):
        if category not in self.categories:
            self.categories.append(category)
    
    def remove_category(self, category):
        if category in self.categories:
            self.categories.remove(category)
    
    def add_transaction(self, transaction):
        if transaction not in self.transactions:
            self.transactions.append(transaction)
    
    def remove_transaction(self, transaction):
        if transaction in self.transactions:
            self.transactions.remove(transaction)
