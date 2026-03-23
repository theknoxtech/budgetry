from collections import defaultdict
from datetime import date
from app.models import Transaction, Category


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
    '''
    print("Income:", income_total)
    print("Available: ", dict(available))    
    print("Activity:", dict(activity))
    print("To Be Budgeted: ", to_be_budgeted)
    print("Overspent: ", overspent_categories)
    '''
    
    return {
        "income_total": income_total,
        "available": available,
        "activity": activity,
        "to_be_budgeted": to_be_budgeted,
        "overspent_categories": overspent_categories
    }


def calculate_monthly_needed(target_amount, target_type, target_date, available=0.0):
    if not target_type or target_amount <= 0:
        return 0.0
    if target_type == "weekly":
        return target_amount * 4.33
    elif target_type == "biweekly":
        return target_amount * 2.17
    elif target_type == "monthly":
        return target_amount
    elif target_type == "yearly":
        return target_amount / 12.0
    elif target_type == "custom":
        remaining = target_amount - available
        if remaining <= 0:
            return 0.0
        try:
            target = date.fromisoformat(target_date)
            today = date.today()
            months_left = (target.year - today.year) * 12 + (target.month - today.month)
            months_left = max(1, months_left)
            return remaining / months_left
        except (ValueError, TypeError):
            return remaining
    return 0.0