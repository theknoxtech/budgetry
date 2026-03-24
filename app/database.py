import sqlite3
import os
import uuid
from datetime import datetime
from app.models import Transaction, Category, Payee, Account, User, BudgetRecord, Rule, CategoryGroup, RecurringTransaction

_instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
os.makedirs(_instance_dir, exist_ok=True)
DB_PATH = os.path.join(_instance_dir, 'budgetry.db')


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    # Core tables
    cursor.execute("CREATE TABLE IF NOT EXISTS transactions(id TEXT PRIMARY KEY, date TEXT, payee TEXT, amount REAL, memo TEXT, category_id TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY, name TEXT, budgeted REAL, activity REAL, available REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS payees(id TEXT PRIMARY KEY, name TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY, name TEXT, account_type TEXT, institution TEXT, balance REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS plaid_items(id TEXT PRIMARY KEY, account_id TEXT, access_token TEXT, item_id TEXT, institution_name TEXT, cursor TEXT DEFAULT '', last_synced TEXT DEFAULT '')")

    # Auth + budget tables
    cursor.execute("CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, auth0_id TEXT DEFAULT '', email TEXT DEFAULT '', username TEXT NOT NULL, created_at TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS budgets(id TEXT PRIMARY KEY, name TEXT NOT NULL, is_shared INTEGER DEFAULT 0, created_at TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS budget_members(budget_id TEXT NOT NULL, user_id TEXT NOT NULL, role TEXT DEFAULT 'owner', PRIMARY KEY(budget_id, user_id))")

    # Settings tables
    cursor.execute("CREATE TABLE IF NOT EXISTS budget_defaults(budget_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT DEFAULT '', PRIMARY KEY(budget_id, key))")
    cursor.execute("CREATE TABLE IF NOT EXISTS payee_rules(id TEXT PRIMARY KEY, payee_name TEXT NOT NULL, category_id TEXT NOT NULL, budget_id TEXT NOT NULL)")

    # Category groups table
    cursor.execute("""CREATE TABLE IF NOT EXISTS category_groups(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        position INTEGER DEFAULT 0,
        budget_id TEXT NOT NULL
    )""")

    # Recurring transactions table
    cursor.execute("""CREATE TABLE IF NOT EXISTS recurring_transactions(
        id TEXT PRIMARY KEY,
        payee TEXT NOT NULL,
        amount REAL NOT NULL,
        memo TEXT DEFAULT '',
        category_id TEXT DEFAULT '',
        account_id TEXT DEFAULT '',
        frequency TEXT NOT NULL,
        next_date TEXT NOT NULL,
        budget_id TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    )""")

    # Rules table (expanded automation system)
    cursor.execute("""CREATE TABLE IF NOT EXISTS rules(
        id TEXT PRIMARY KEY,
        rule_type TEXT NOT NULL,
        match_field TEXT NOT NULL,
        match_type TEXT NOT NULL,
        match_value TEXT NOT NULL,
        action_type TEXT NOT NULL,
        action_value TEXT NOT NULL,
        budget_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")

    # --- Migrations: add columns if they don't exist ---

    # Transactions migrations
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in cursor.fetchall()]
    if "account_id" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN account_id TEXT DEFAULT ''")
    if "plaid_transaction_id" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN plaid_transaction_id TEXT DEFAULT ''")
    if "budget_id" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN budget_id TEXT DEFAULT ''")

    # Categories migrations
    cursor.execute("PRAGMA table_info(categories)")
    cat_columns = [col[1] for col in cursor.fetchall()]
    if "target_amount" not in cat_columns:
        cursor.execute("ALTER TABLE categories ADD COLUMN target_amount REAL DEFAULT 0")
    if "target_type" not in cat_columns:
        cursor.execute("ALTER TABLE categories ADD COLUMN target_type TEXT DEFAULT ''")
    if "target_date" not in cat_columns:
        cursor.execute("ALTER TABLE categories ADD COLUMN target_date TEXT DEFAULT ''")
    if "budget_id" not in cat_columns:
        cursor.execute("ALTER TABLE categories ADD COLUMN budget_id TEXT DEFAULT ''")
    if "group_id" not in cat_columns:
        cursor.execute("ALTER TABLE categories ADD COLUMN group_id TEXT DEFAULT ''")

    # Accounts migrations
    cursor.execute("PRAGMA table_info(accounts)")
    acct_columns = [col[1] for col in cursor.fetchall()]
    if "budget_id" not in acct_columns:
        cursor.execute("ALTER TABLE accounts ADD COLUMN budget_id TEXT DEFAULT ''")

    # Payees migrations
    cursor.execute("PRAGMA table_info(payees)")
    payee_columns = [col[1] for col in cursor.fetchall()]
    if "budget_id" not in payee_columns:
        cursor.execute("ALTER TABLE payees ADD COLUMN budget_id TEXT DEFAULT ''")

    # Users migrations
    cursor.execute("PRAGMA table_info(users)")
    user_columns = {col[1] for col in cursor.fetchall()}
    if "auth0_id" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN auth0_id TEXT DEFAULT ''")
    if "email" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT DEFAULT ''")
    if "password_hash" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT DEFAULT ''")
    if "totp_secret" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN totp_secret TEXT DEFAULT ''")

    # User management columns
    cursor.execute("PRAGMA table_info(users)")
    user_cols_updated = {col[1] for col in cursor.fetchall()}
    if "is_admin" not in user_cols_updated:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    if "is_active" not in user_cols_updated:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
    if "mfa_enabled" not in user_cols_updated:
        cursor.execute("ALTER TABLE users ADD COLUMN mfa_enabled INTEGER DEFAULT 0")

    # Migrate payee_rules into rules table
    cursor.execute("SELECT COUNT(*) FROM payee_rules")
    old_rule_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM rules")
    new_rule_count = cursor.fetchone()[0]
    if old_rule_count > 0 and new_rule_count == 0:
        cursor.execute("SELECT id, payee_name, category_id, budget_id FROM payee_rules")
        for row in cursor.fetchall():
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO rules(id, rule_type, match_field, match_type, match_value, action_type, action_value, budget_id, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (row[0], 'payee', 'payee_name', 'exact', row[1], 'set_category', row[2], row[3], now)
            )

    # --- Data migration: assign existing data to a default user/budget ---
    cursor.execute("SELECT COUNT(*) FROM budgets")
    budget_count = cursor.fetchone()[0]

    if budget_count == 0:
        # Check if there's existing data that needs migrating
        cursor.execute("SELECT COUNT(*) FROM categories")
        cat_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM accounts")
        acct_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM transactions")
        txn_count = cursor.fetchone()[0]

        if cat_count > 0 or acct_count > 0 or txn_count > 0:
            now = datetime.now().isoformat()

            # Create a placeholder user (will be linked to Auth0 on first login)
            default_user_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO users(id, auth0_id, email, username, created_at) VALUES(?,?,?,?,?)",
                           (default_user_id, "", "", "admin", now))

            # Create default personal budget
            default_budget_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO budgets(id, name, is_shared, created_at) VALUES(?,?,?,?)",
                           (default_budget_id, "My Budget", 0, now))

            # Link user to budget
            cursor.execute("INSERT INTO budget_members(budget_id, user_id, role) VALUES(?,?,?)",
                           (default_budget_id, default_user_id, "owner"))

            # Migrate existing data
            cursor.execute("UPDATE categories SET budget_id = ? WHERE budget_id = '' OR budget_id IS NULL", (default_budget_id,))
            cursor.execute("UPDATE accounts SET budget_id = ? WHERE budget_id = '' OR budget_id IS NULL", (default_budget_id,))
            cursor.execute("UPDATE transactions SET budget_id = ? WHERE budget_id = '' OR budget_id IS NULL", (default_budget_id,))
            cursor.execute("UPDATE payees SET budget_id = ? WHERE budget_id = '' OR budget_id IS NULL", (default_budget_id,))

            print(f"[Budgetry] Migrated existing data. Log in with Auth0 to claim your account.")

    # Seed first user as admin if no admins exist
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (row[0],))

    connection.commit()
    connection.close()


# --- Users ---

_USER_COLUMNS = "id, auth0_id, email, username, created_at, is_admin, is_active, mfa_enabled, password_hash, totp_secret"


def _row_to_user(row):
    if not row:
        return None
    return User(
        id=row[0], auth0_id=row[1], email=row[2], username=row[3],
        created_at=row[4], is_admin=row[5] or 0,
        is_active=row[6] if row[6] is not None else 1,
        mfa_enabled=row[7] or 0, password_hash=row[8] or "",
        totp_secret=row[9] or ""
    )


def add_user(user):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO users(id, auth0_id, email, username, created_at) VALUES(?,?,?,?,?)",
        (user.id, user.auth0_id, user.email, user.username, user.created_at)
    )
    connection.commit()
    connection.close()


def get_user_by_auth0_id(auth0_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE auth0_id = ?", (auth0_id,))
    row = cursor.fetchone()
    connection.close()
    return _row_to_user(row)


def get_user_by_email(email):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    connection.close()
    return _row_to_user(row)


def get_user_by_id(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    connection.close()
    return _row_to_user(row)


def get_user_by_username(username):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    connection.close()
    return _row_to_user(row)


def create_local_user(username, email, password_hash):
    now = datetime.now().isoformat()
    user = User(
        id=str(uuid.uuid4()),
        auth0_id="",
        email=email,
        username=username,
        created_at=now,
        password_hash=password_hash,
    )
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO users(id, auth0_id, email, username, created_at, password_hash) VALUES(?,?,?,?,?,?)",
        (user.id, "", email, username, now, password_hash)
    )
    connection.commit()
    connection.close()
    return user


def update_password_hash(user_id, password_hash):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    connection.commit()
    connection.close()


def update_totp_secret(user_id, totp_secret):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET totp_secret = ? WHERE id = ?", (totp_secret, user_id))
    connection.commit()
    connection.close()


def upsert_user_from_auth0(auth0_id, email, username):
    """Find or create a user from Auth0 login. Returns the User object."""
    # First try to find by auth0_id
    user = get_user_by_auth0_id(auth0_id)
    if user:
        # Update email/username in case they changed in Auth0
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET email = ?, username = ? WHERE auth0_id = ?",
                       (email, username, auth0_id))
        connection.commit()
        connection.close()
        user.email = email
        user.username = username
        return user

    # Try to find by email (link existing account)
    if email:
        user = get_user_by_email(email)
        if user:
            # Link this Auth0 ID to existing user
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET auth0_id = ?, username = ? WHERE id = ?",
                           (auth0_id, username, user.id))
            connection.commit()
            connection.close()
            user.auth0_id = auth0_id
            user.username = username
            return user

    # Create new user
    now = datetime.now().isoformat()
    new_user = User(
        id=str(uuid.uuid4()),
        auth0_id=auth0_id,
        email=email,
        username=username,
        created_at=now
    )
    add_user(new_user)
    return new_user


def update_username(user_id, username):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
    connection.commit()
    connection.close()


def get_all_users():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT {_USER_COLUMNS} FROM users ORDER BY created_at ASC")
    rows = cursor.fetchall()
    connection.close()
    return [_row_to_user(r) for r in rows]


def set_user_active(user_id, is_active):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id))
    connection.commit()
    connection.close()


def update_user_mfa_status(user_id, mfa_enabled):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET mfa_enabled = ? WHERE id = ?", (mfa_enabled, user_id))
    connection.commit()
    connection.close()


def get_user_role_in_budget(user_id, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT role FROM budget_members WHERE user_id = ? AND budget_id = ?", (user_id, budget_id))
    row = cursor.fetchone()
    connection.close()
    return row[0] if row else None


# --- Budgets ---

def add_budget(budget):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO budgets(id, name, is_shared, created_at) VALUES(?,?,?,?)",
        (budget.id, budget.name, budget.is_shared, budget.created_at)
    )
    connection.commit()
    connection.close()


def get_budget_by_id(budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, is_shared, created_at FROM budgets WHERE id = ?", (budget_id,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return BudgetRecord(id=row[0], name=row[1], is_shared=row[2], created_at=row[3])
    return None


def get_budgets_for_user(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT b.id, b.name, b.is_shared, b.created_at
        FROM budgets b
        JOIN budget_members bm ON b.id = bm.budget_id
        WHERE bm.user_id = ?
        ORDER BY b.is_shared ASC, b.name ASC
    """, (user_id,))
    rows = cursor.fetchall()
    connection.close()
    return [BudgetRecord(id=row[0], name=row[1], is_shared=row[2], created_at=row[3]) for row in rows]


def add_budget_member(budget_id, user_id, role="member"):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO budget_members(budget_id, user_id, role) VALUES(?,?,?)",
        (budget_id, user_id, role)
    )
    connection.commit()
    connection.close()


def is_budget_member(budget_id, user_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM budget_members WHERE budget_id = ? AND user_id = ?", (budget_id, user_id))
    count = cursor.fetchone()[0]
    connection.close()
    return count > 0


# --- Accounts ---

def add_account(account):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO accounts(id, name, account_type, institution, balance, budget_id) VALUES(?,?,?,?,?,?)",
        (account.id, account.name, account.account_type, account.institution, account.balance, account.budget_id)
    )
    connection.commit()
    connection.close()


def get_accounts(budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, account_type, institution, balance, budget_id FROM accounts WHERE budget_id = ?", (budget_id,))
    rows = cursor.fetchall()
    connection.close()
    return [Account(id=row[0], name=row[1], account_type=row[2], institution=row[3], balance=row[4], budget_id=row[5] or "") for row in rows]


def get_account(account_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, account_type, institution, balance, budget_id FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return Account(id=row[0], name=row[1], account_type=row[2], institution=row[3], balance=row[4], budget_id=row[5] or "")
    return None


def delete_account(account_id, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM accounts WHERE id = ? AND budget_id = ?", (account_id, budget_id))
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
        "INSERT INTO transactions(id, date, payee, amount, memo, category_id, account_id, plaid_transaction_id, budget_id) VALUES(?,?,?,?,?,?,?,?,?)",
        (transaction.id, transaction.date, transaction.payee, transaction.amount, transaction.memo, transaction.category_id, transaction.account_id, transaction.plaid_transaction_id, transaction.budget_id)
    )
    connection.commit()
    connection.close()


def get_transaction(budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, date, payee, amount, memo, category_id, account_id, plaid_transaction_id, budget_id FROM transactions WHERE budget_id = ?", (budget_id,))
    rows = cursor.fetchall()
    connection.close()
    return [Transaction(id=row[0], date=row[1], payee=row[2], amount=row[3], memo=row[4], category_id=row[5], account_id=row[6] or "", plaid_transaction_id=row[7] or "", budget_id=row[8] or "") for row in rows]


def get_transaction_by_id(transaction_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, date, payee, amount, memo, category_id, account_id, plaid_transaction_id, budget_id FROM transactions WHERE id = ?", (transaction_id,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return Transaction(id=row[0], date=row[1], payee=row[2], amount=row[3], memo=row[4], category_id=row[5], account_id=row[6] or "", plaid_transaction_id=row[7] or "", budget_id=row[8] or "")
    return None


def update_transaction(transaction):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE transactions SET date=?, payee=?, amount=?, memo=?, category_id=?, account_id=? WHERE id=? AND budget_id=?",
        (transaction.date, transaction.payee, transaction.amount, transaction.memo, transaction.category_id, transaction.account_id, transaction.id, transaction.budget_id)
    )
    connection.commit()
    connection.close()


def delete_transaction(transaction_id, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND budget_id = ?", (transaction_id, budget_id))
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
    connection = get_db()
    cursor = connection.cursor()
    query = """
        DELETE FROM transactions WHERE id = ?
    """
    cursor.execute(query, (transaction_id,))
    connection.commit()
    connection.close()

def update_transaction(transaction):
    connection = get_db()
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
        "INSERT INTO categories(id, name, budgeted, activity, available, target_amount, target_type, target_date, budget_id, group_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (category.id, category.name, category.budgeted, category.activity, category.available, category.target_amount, category.target_type, category.target_date, category.budget_id, category.group_id)
    )
    connection.commit()
    connection.close()

# TODO: Implement delete_category(category_id)
# TODO: Implement update_category(category_id, updated_category_obj)

def get_categories(budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, budgeted, activity, available, target_amount, target_type, target_date, budget_id, group_id FROM categories WHERE budget_id = ?", (budget_id,))
    rows = cursor.fetchall()
    connection.close()
    return [Category(id=row[0], name=row[1], budgeted=row[2], activity=row[3], available=row[4],
                     target_amount=row[5] or 0.0, target_type=row[6] or "", target_date=row[7] or "", budget_id=row[8] or "", group_id=row[9] or "") for row in rows]


def get_category_by_id(category_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, budgeted, activity, available, target_amount, target_type, target_date, budget_id, group_id FROM categories WHERE id = ?", (category_id,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return Category(id=row[0], name=row[1], budgeted=row[2], activity=row[3], available=row[4],
                        target_amount=row[5] or 0.0, target_type=row[6] or "", target_date=row[7] or "", budget_id=row[8] or "", group_id=row[9] or "")
    return None


def update_category(category_id, name, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE categories SET name = ? WHERE id = ? AND budget_id = ?", (name, category_id, budget_id))
    connection.commit()
    connection.close()


def delete_category(category_id, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ? AND budget_id = ?", (category_id, budget_id))
    connection.commit()
    connection.close()


def update_category_budget(category_id, budgeted_amount):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE categories SET budgeted = ? WHERE id = ?", (budgeted_amount, category_id))
    connection.commit()
    connection.close()


def update_category_target(category_id, target_amount, target_type, target_date):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE categories SET target_amount = ?, target_type = ?, target_date = ? WHERE id = ?",
                   (target_amount, target_type, target_date, category_id))
    connection.commit()
    connection.close()


# --- Payees ---

def add_payee(payee):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO payees(id, name, budget_id) VALUES(?,?,?)",
        (payee.id, payee.name, payee.budget_id)
    )
    connection.commit()
    connection.close()


def get_payees(budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, budget_id FROM payees WHERE budget_id = ?", (budget_id,))
    rows = cursor.fetchall()
    connection.close()
    return [Payee(id=row[0], name=row[1], budget_id=row[2] or "") for row in rows]


def delete_payee(payee_id, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM payees WHERE id = ? AND budget_id = ?", (payee_id, budget_id))
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


def get_plaid_item_by_account(account_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, account_id, access_token, item_id, institution_name, cursor, last_synced FROM plaid_items WHERE account_id = ?", (account_id,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return {"id": row[0], "account_id": row[1], "access_token": row[2], "item_id": row[3], "institution_name": row[4], "cursor": row[5], "last_synced": row[6]}
    return None


def update_plaid_cursor(plaid_item_id, new_cursor, last_synced):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE plaid_items SET cursor = ?, last_synced = ? WHERE id = ?", (new_cursor, last_synced, plaid_item_id))
    connection.commit()
    connection.close()


def delete_plaid_item(plaid_item_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM plaid_items WHERE id = ?", (plaid_item_id,))
    connection.commit()
    connection.close()


# --- Budget Defaults ---

def get_budget_default(budget_id, key):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM budget_defaults WHERE budget_id = ? AND key = ?", (budget_id, key))
    row = cursor.fetchone()
    connection.close()
    return row[0] if row else ''


def get_all_budget_defaults(budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT key, value FROM budget_defaults WHERE budget_id = ?", (budget_id,))
    rows = cursor.fetchall()
    connection.close()
    return {row[0]: row[1] for row in rows}


def set_budget_default(budget_id, key, value):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT OR REPLACE INTO budget_defaults(budget_id, key, value) VALUES(?,?,?)",
                   (budget_id, key, value))
    connection.commit()
    connection.close()


# --- Payee Rules ---

def get_payee_rules(budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, payee_name, category_id, budget_id FROM payee_rules WHERE budget_id = ?", (budget_id,))
    rows = cursor.fetchall()
    connection.close()
    return [{'id': r[0], 'payee_name': r[1], 'category_id': r[2], 'budget_id': r[3]} for r in rows]


def add_payee_rule(rule_id, payee_name, category_id, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO payee_rules(id, payee_name, category_id, budget_id) VALUES(?,?,?,?)",
                   (rule_id, payee_name, category_id, budget_id))
    connection.commit()
    connection.close()


def delete_payee_rule(rule_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM payee_rules WHERE id = ?", (rule_id,))
    connection.commit()
    connection.close()


def get_payee_rule_by_name(payee_name, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT category_id FROM payee_rules WHERE payee_name = ? AND budget_id = ?",
                   (payee_name, budget_id))
    row = cursor.fetchone()
    connection.close()
    return row[0] if row else ''


def update_payee(payee_id, name, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE payees SET name = ? WHERE id = ? AND budget_id = ?", (name, payee_id, budget_id))
    connection.commit()
    connection.close()


def get_payee_by_id(payee_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, budget_id FROM payees WHERE id = ?", (payee_id,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return Payee(id=row[0], name=row[1], budget_id=row[2] or "")
    return None


# --- Rules (expanded automation) ---

def get_rules(budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, rule_type, match_field, match_type, match_value, action_type, action_value, budget_id, created_at FROM rules WHERE budget_id = ? ORDER BY created_at ASC",
        (budget_id,)
    )
    rows = cursor.fetchall()
    connection.close()
    return [Rule(id=r[0], rule_type=r[1], match_field=r[2], match_type=r[3], match_value=r[4],
                 action_type=r[5], action_value=r[6], budget_id=r[7], created_at=r[8]) for r in rows]


def add_rule(rule_id, rule_type, match_field, match_type, match_value, action_type, action_value, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO rules(id, rule_type, match_field, match_type, match_value, action_type, action_value, budget_id, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (rule_id, rule_type, match_field, match_type, match_value, action_type, action_value, budget_id, now)
    )
    connection.commit()
    connection.close()


def delete_rule(rule_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
    connection.commit()
    connection.close()


# --- Category Groups ---

def get_category_groups(budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, position, budget_id FROM category_groups WHERE budget_id = ? ORDER BY position ASC", (budget_id,))
    rows = cursor.fetchall()
    connection.close()
    return [CategoryGroup(id=r[0], name=r[1], position=r[2], budget_id=r[3]) for r in rows]


def add_category_group(group):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO category_groups(id, name, position, budget_id) VALUES(?,?,?,?)",
                   (group.id, group.name, group.position, group.budget_id))
    connection.commit()
    connection.close()


def update_category_group(group_id, name, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE category_groups SET name = ? WHERE id = ? AND budget_id = ?", (name, group_id, budget_id))
    connection.commit()
    connection.close()


def delete_category_group(group_id, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    # Ungroup categories first
    cursor.execute("UPDATE categories SET group_id = '' WHERE group_id = ? AND budget_id = ?", (group_id, budget_id))
    cursor.execute("DELETE FROM category_groups WHERE id = ? AND budget_id = ?", (group_id, budget_id))
    connection.commit()
    connection.close()


def set_category_group(category_id, group_id, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE categories SET group_id = ? WHERE id = ? AND budget_id = ?", (group_id, category_id, budget_id))
    connection.commit()
    connection.close()


# --- Recurring Transactions ---

def get_recurring_transactions(budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, payee, amount, memo, category_id, account_id, frequency, next_date, budget_id, is_active FROM recurring_transactions WHERE budget_id = ? ORDER BY next_date ASC",
        (budget_id,)
    )
    rows = cursor.fetchall()
    connection.close()
    return [RecurringTransaction(id=r[0], payee=r[1], amount=r[2], memo=r[3], category_id=r[4], account_id=r[5],
                                  frequency=r[6], next_date=r[7], budget_id=r[8], is_active=r[9]) for r in rows]


def add_recurring_transaction(rt):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO recurring_transactions(id, payee, amount, memo, category_id, account_id, frequency, next_date, budget_id, is_active) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (rt.id, rt.payee, rt.amount, rt.memo, rt.category_id, rt.account_id, rt.frequency, rt.next_date, rt.budget_id, rt.is_active)
    )
    connection.commit()
    connection.close()


def update_recurring_next_date(rt_id, next_date):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE recurring_transactions SET next_date = ? WHERE id = ?", (next_date, rt_id))
    connection.commit()
    connection.close()


def delete_recurring_transaction(rt_id, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM recurring_transactions WHERE id = ? AND budget_id = ?", (rt_id, budget_id))
    connection.commit()
    connection.close()


def toggle_recurring_transaction(rt_id, is_active, budget_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE recurring_transactions SET is_active = ? WHERE id = ? AND budget_id = ?", (is_active, rt_id, budget_id))
    connection.commit()
    connection.close()


def apply_rules(payee_name, amount, budget_id):
    """Apply all matching rules and return a dict of actions.
    First-match-wins per action type."""
    rules = get_rules(budget_id)
    result = {}

    for rule in rules:
        matched = False

        if rule.match_field == 'payee_name' and payee_name:
            pn = payee_name.lower()
            mv = rule.match_value.lower()
            if rule.match_type == 'exact' and pn == mv:
                matched = True
            elif rule.match_type == 'contains' and mv in pn:
                matched = True
            elif rule.match_type == 'starts_with' and pn.startswith(mv):
                matched = True

        elif rule.match_field == 'amount' and amount is not None:
            try:
                if rule.match_type == 'greater_than' and abs(amount) > float(rule.match_value):
                    matched = True
                elif rule.match_type == 'less_than' and abs(amount) < float(rule.match_value):
                    matched = True
                elif rule.match_type == 'between':
                    low, high = rule.match_value.split('|')
                    if float(low) <= abs(amount) <= float(high):
                        matched = True
            except (ValueError, IndexError):
                pass

        if matched:
            if rule.action_type == 'set_category' and 'category_id' not in result:
                result['category_id'] = rule.action_value
            elif rule.action_type == 'set_memo' and 'memo' not in result:
                result['memo'] = rule.action_value
            elif rule.action_type == 'set_account' and 'account_id' not in result:
                result['account_id'] = rule.action_value
            elif rule.action_type == 'flag' and 'flagged' not in result:
                result['flagged'] = True

    return result
