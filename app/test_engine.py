from budget_engine import run_budget_engine

# Test categories
rent = "rent"
internet = "internet"
electric = "electric"


# Test previously available amounts
previous_month_available = {
    rent: 300.00,
    internet: 0.50,
    electric: 20.00
}

# Test budgeted amounts
budgeted = {
    rent: 500,
    internet: 150.00,
    electric: 200.00
}

# Test transaction
transactions = [
    {"category_id": rent, "amount": -59.00},
    {"category_id": internet, "amount": -50.00},
    {"category_id": electric, "amount": -25.00},
    {"category_id": None, "amount": 5000.00}
]

result = run_budget_engine(previous_month_available, budgeted, transactions)
print(result)