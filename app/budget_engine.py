from collections import defaultdict
from models import Transaction, Category, Budget



def run_budget_engine(previous_month_available, budgeted, transactions):
    activity = {}
    income_total = 0.0

    for transaction in transactions:
        amount = transaction.amount
        category_id = transaction.category_id
        if category_id == "income":
            income_total += amount
        else:
            activity.setdefault(category_id, 0.0)
            activity[category_id] += amount
    
    # Calculate Available Amounts
    available = {}
    for category_id, budget in budgeted.items():
        previous_month = previous_month_available.get(category_id, 0.0)
        spent_money = activity.get(category_id, 0.0)
        available[category_id] = previous_month + budget - spent_money
    
    # Calculate Amount to be Budgeted
    to_be_budgeted = income_total - sum(budgeted.values())
    
    # Calculate Overspent Categories
    overspent_categories = {}
    for category_id, avail_amount in available.items():
        if avail_amount < 0:
            overspent_categories[category_id] = avail_amount
            
    return {
        "income_total ":income_total,
        "available ": available,
        "activity: ": activity,
        "to_be_budgeted ": to_be_budgeted,
        "overspent_categories ": overspent_categories
        }
run_budget_engine()