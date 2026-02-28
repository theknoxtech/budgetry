import sqlite3
from models import Transaction, Category, Payee


# Init DB
def init_db():
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute("CREATE TABLE IF NOT EXISTS transactions(id TEXT PRIMARY KEY,date TEXT,payee TEXT,amount REAL,memo TEXT,category_id TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY,name TEXT,budgeted REAL,activity REAL,available REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS payees(id TEXT PRIMARY KEY,name TEXT)")
    
    connection.commit()
    connection.close()

def add_transaction(transaction):
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute(
        "INSERT INTO transactions VALUES(?,?,?,?,?,?)",
        (transaction.id, transaction.date, transaction.payee,transaction.amount,transaction.memo,transaction.category_id)
        )
    
    connection.commit()
    connection.close()

def get_transaction():
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    return [Transaction(id=row[0], date=row[1], payee=row[2], amount=row[3], memo=row[4], category_id=row[5]) for row in rows]

# TODO: Implement delete_transaction(transaction_id)
# TODO: Implement update_transaction(transaction_id, updated_transaction_obj)

def add_category(category):
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute(
        "INSERT INTO categories VALUES(?,?,?,?,?)",
        (category.id, category.name, category.budgeted,category.activity,category.available)
        )
    
    connection.commit()
    connection.close()

# TODO: Implement delete_category(category_id)
# TODO: Implement update_category(category_id, updated_category_obj)

def get_categories(names_only=False, select_category=False):
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    if names_only:
        cursor.execute("SELECT name FROM categories")
        rows = cursor.fetchall()
        return [row[0] for row in rows]

    cursor.execute("SELECT * FROM categories")
    rows = cursor.fetchall()
    return [Category(id=row[0], name=row[1], budgeted=row[2], activity=row[3], available=row[4]) for row in rows]


# TODO: Implement add_payee(payee)
def get_payees():
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM payees")
    rows = cursor.fetchall()
    return [Payee(id=row[0], name=row[1]) for row in rows]

def delete_payees(payee):
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute("DELETE FROM payees WHERE id = ?", (payee.id,))
    
    connection.commit()
    connection.close()

# TODO: Implement update_payee(payee_id, updated_payee_obj)
