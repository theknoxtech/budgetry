import sqlite3
import os
from app.models import Transaction, Category, Payee

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'budget.db')


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS transactions(id TEXT PRIMARY KEY, date TEXT, payee TEXT, amount REAL, memo TEXT, category_id TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY, name TEXT, budgeted REAL, activity REAL, available REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS payees(id TEXT PRIMARY KEY, name TEXT)")

    connection.commit()
    connection.close()


# --- Transactions ---

def add_transaction(transaction):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO transactions VALUES(?,?,?,?,?,?)",
        (transaction.id, transaction.date, transaction.payee, transaction.amount, transaction.memo, transaction.category_id)
    )
    connection.commit()
    connection.close()


def get_transaction():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    connection.close()
    return [Transaction(id=row[0], date=row[1], payee=row[2], amount=row[3], memo=row[4], category_id=row[5]) for row in rows]


def delete_transaction(transaction_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    connection.commit()
    connection.close()


# --- Categories ---

def add_category(category):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO categories VALUES(?,?,?,?,?)",
        (category.id, category.name, category.budgeted, category.activity, category.available)
    )
    connection.commit()
    connection.close()


def get_categories():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM categories")
    rows = cursor.fetchall()
    connection.close()
    return [Category(id=row[0], name=row[1], budgeted=row[2], activity=row[3], available=row[4]) for row in rows]


def delete_category(category_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    connection.commit()
    connection.close()


def update_category_budget(category_id, budgeted_amount):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE categories SET budgeted = ? WHERE id = ?", (budgeted_amount, category_id))
    connection.commit()
    connection.close()


# --- Payees ---

def add_payee(payee):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO payees VALUES(?,?)",
        (payee.id, payee.name)
    )
    connection.commit()
    connection.close()


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
