import sqlite3
import os
from app.models import Transaction, Category, Payee, Account

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'budget.db')


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS transactions(id TEXT PRIMARY KEY, date TEXT, payee TEXT, amount REAL, memo TEXT, category_id TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY, name TEXT, budgeted REAL, activity REAL, available REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS payees(id TEXT PRIMARY KEY, name TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY, name TEXT, account_type TEXT, institution TEXT, balance REAL)")

    cursor.execute("CREATE TABLE IF NOT EXISTS plaid_items(id TEXT PRIMARY KEY, account_id TEXT, access_token TEXT, item_id TEXT, institution_name TEXT, cursor TEXT DEFAULT '', last_synced TEXT DEFAULT '')")

    # Migrations: add new columns to transactions if they don't exist
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in cursor.fetchall()]
    if "account_id" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN account_id TEXT DEFAULT ''")
    if "plaid_transaction_id" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN plaid_transaction_id TEXT DEFAULT ''")

    connection.commit()
    connection.close()


# --- Accounts ---

def add_account(account):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO accounts VALUES(?,?,?,?,?)",
        (account.id, account.name, account.account_type, account.institution, account.balance)
    )
    connection.commit()
    connection.close()


def get_accounts():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM accounts")
    rows = cursor.fetchall()
    connection.close()
    return [Account(id=row[0], name=row[1], account_type=row[2], institution=row[3], balance=row[4]) for row in rows]


def get_account(account_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return Account(id=row[0], name=row[1], account_type=row[2], institution=row[3], balance=row[4])
    return None


def delete_account(account_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    connection.commit()
    connection.close()


def update_account_balance(account_id, balance):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (balance, account_id))
    connection.commit()
    connection.close()


# --- Transactions ---

def add_transaction(transaction):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO transactions(id, date, payee, amount, memo, category_id, account_id, plaid_transaction_id) VALUES(?,?,?,?,?,?,?,?)",
        (transaction.id, transaction.date, transaction.payee, transaction.amount, transaction.memo, transaction.category_id, transaction.account_id, transaction.plaid_transaction_id)
    )
    connection.commit()
    connection.close()


def get_transaction():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, date, payee, amount, memo, category_id, account_id, plaid_transaction_id FROM transactions")
    rows = cursor.fetchall()
    connection.close()
    return [Transaction(id=row[0], date=row[1], payee=row[2], amount=row[3], memo=row[4], category_id=row[5], account_id=row[6] or "", plaid_transaction_id=row[7] or "") for row in rows]


def delete_transaction(transaction_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    connection.commit()
    connection.close()


def get_transaction_by_plaid_id(plaid_transaction_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM transactions WHERE plaid_transaction_id = ?", (plaid_transaction_id,))
    row = cursor.fetchone()
    connection.close()
    return row is not None

# TODO: Implement delete_transaction(transaction_id)
def delete_transaction(transaction_id):
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    query = """
        DELETE FROM transactions WHERE id = ?
    """
    cursor.execute(query, (transaction_id) )
    connection.commit()
    connection.close()

def update_transaction(transaction):
    connection = sqlite3.connect("budget.db")
    cursor = connection.cursor()
    query = """
        UPDATE transactions 
        SET date = ?, payee = ?, amount = ?, memo = ?, category_id = ? 
        WHERE id = ?
    """
    values = (
        transaction.date, 
        transaction.payee, 
        transaction.amount, 
        transaction.memo, 
        transaction.category_id, 
        transaction.id
    )
    
    cursor.execute(query, values)
    connection.commit()
    connection.close()

def add_category(category):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO categories VALUES(?,?,?,?,?)",
        (category.id, category.name, category.budgeted, category.activity, category.available)
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
    connection.close()
    return [Category(id=row[0], name=row[1], budgeted=row[2], activity=row[3], available=row[4]) for row in rows]


# TODO: Implement add_payee(payee)
def get_payees():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM payees")
    rows = cursor.fetchall()
    connection.close()
    return [Payee(id=row[0], name=row[1]) for row in rows]


def delete_payee(payee_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM payees WHERE id = ?", (payee_id,))
    connection.commit()
    connection.close()


# --- Plaid Items ---

def add_plaid_item(plaid_item_id, account_id, access_token, item_id, institution_name):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO plaid_items(id, account_id, access_token, item_id, institution_name) VALUES(?,?,?,?,?)",
        (plaid_item_id, account_id, access_token, item_id, institution_name)
    )
    connection.commit()
    connection.close()

# TODO: Implement update_payee(payee_id, updated_payee_obj)
