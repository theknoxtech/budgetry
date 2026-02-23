import sqlite3

'''
def init_db():
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
'''
# Query to cbeck if table exists
def table_exists(connection, table_name):
    cursor = connection.cursor()
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
    cursor.execute(query, (table_name,))
    result = cursor.fetchone()
    
    return result is not None

# Init DB
connection = sqlite3.connect("budget.db")
cursor = connection.cursor()

if table_exists(connection, 'transactions'):
    print("Table 'transactions' exists.")
else:
    print("Table 'transactions' does not exist")