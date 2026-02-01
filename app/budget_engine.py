from collections import defaultdict

'''
### Basic Flow ###
1. Scan transactions → calculate:
   - activity per category
   - total income
2. Calculate available per category
3. Calculate To Be Budgeted (TBB)
4. Detect overspending
'''


def run_budget_engine(previous_month_available, budgeted, transactions):
    activity = defaultdict(float)
    income_total = 0.0
    
    for transaction in transactions:
        amount = transaction["amount"]
        category_id = transaction.get("category_id")
        if category_id is None:
            income_total += amount
        else:
            activity[category_id] += amount
    
    print("Activity:", dict(activity))
    print("Income:", income_total)
pass