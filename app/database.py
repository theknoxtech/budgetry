import sqlite3


# Init DB
def init_db():
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    
    cursor.execute("CREATE TABLE IF NOT EXISTS transactions(id TEXT PRIMARY KEY,date TEXT,payee TEXT,amount REAL,memo TEXT,category_id TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY,name TEXT,budgeted REAL,activity REAL,available REAL)")
    
    connection.commit()
    connection.close()

# TODO Add Save Functions for transaction and categories
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

# TODO Add Remove Functions for transactoins and categories

init_db()

