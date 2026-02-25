import sqlite3
from models import Transaction, Category


# Init DB
def init_db():
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute("CREATE TABLE IF NOT EXISTS transactions(id TEXT PRIMARY KEY,date TEXT,payee TEXT,amount REAL,memo TEXT,category_id TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY,name TEXT,budgeted REAL,activity REAL,available REAL)")
    
    connection.commit()
    connection.close()

def save_transaction(transaction):
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute(
        "INSERT INTO transactions VALUES(?,?,?,?,?,?)",
        (transaction.id, transaction.date, transaction.payee,transaction.amount,transaction.memo,transaction.category_id)
        )
    
    connection.commit()
    connection.close()

def save_category(category):
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute(
        "INSERT INTO categories VALUES(?,?,?,?,?)",
        (category.id, category.name, category.budgeted,category.activity,category.available)
        )
    
    connection.commit()
    connection.close()

def get_transaction():
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    return [Transaction(id=row[0], date=row[1], payee=row[2], amount=row[3], memo=row[4], category_id=row[5]) for row in rows]

def get_categories():
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM categories")
    rows = cursor.fetchall()
    return [Category(id=row[0], name=row[1], budgeted=row[2], activity=row[3], available=row[4]) for row in rows]

# TODO Add Remove Functions for transactoins and categories
# TODO Create methods for adding and removing payees



init_db()

