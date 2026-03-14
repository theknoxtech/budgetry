from dataclasses import dataclass, field
import uuid


@dataclass
class Account:
    id: str
    name: str
    account_type: str
    institution: str
    balance: float

@dataclass
class Transaction:
    date: str
    payee: str
    amount: float
    memo: str
    category_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Category:
    name: str
    budgeted: float
    activity: float 
    available: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Payee:
    id: str
    name: str

@dataclass
class Budget:
    name: str
    categories: list[str] = field(default_factory=list)
    transactions: list[str] = field(default_factory=list)
    payee: list[str] = field(default_factory=list)
    
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
    
    def add_payee(self, payee):
        if payee not in self.payee:
            self.payee.append(payee)
    
    def remove_payee(self, payee):
        if payee in self.payee:
            self.payee.remove(payee)

