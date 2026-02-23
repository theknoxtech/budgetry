from budget_engine import run_budget_engine

# Test categories
rent = "rent"
internet = "internet"
electric = "electric"


# Test previously available amounts
previous_month_available = {
    rent: 0.0,
    internet: 0.0,
    electric: 0.0
}

# Test budgeted amounts
budgeted = {
    rent: 0.0,
    internet: 0.0,
    electric: 0.0
}

# Test transaction
transactions = [
    {"category_id": rent, "amount": 100.00},
    {"category_id": internet, "amount": -10.00},
    {"category_id": electric, "amount": 5000.00},
    {"category_id": None, "amount": 5000.00}
]

result = run_budget_engine(previous_month_available, budgeted, transactions)
print(result)