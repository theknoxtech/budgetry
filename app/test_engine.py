from budget_engine import run_budget_engine
from models import Transaction, Category, Budget
from database import init_db, save_transaction, save_category, get_categories, get_transaction


# Test categories
rent = "rent"
internet = "internet"
electric = "electric"
income = "income"


# Test previously available amounts
previous_month_available = {
    rent: 5.00,
    internet: 10.00,
    electric: 100.00
}

# Test budgeted amounts
budgeted = {
    rent: -100.00,
    internet: 100.00,
    electric: 200.00
}

# Test transaction
transactions = [
    Transaction(id="t1", date="2026-01-01", payee="A", amount=100.00, memo="", category_id=rent),
    Transaction(id="t2", date="2026-01-02", payee="B", amount=-10.00, memo="", category_id=internet),
    Transaction(id="t3", date="2026-01-03", payee="C", amount=5000.00, memo="", category_id=electric),
    Transaction(id="t4", date="2026-01-04", payee="D", amount=5000.00, memo="", category_id=income)
]

init_db()

for t in transactions:
    save_transaction(t)

fetched = get_transaction()
result = run_budget_engine(previous_month_available, budgeted, fetched)
print(fetched)