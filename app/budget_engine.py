from collections import defaultdict
from datetime import date
from app.models import Transaction, Category



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
        # TODO: Verify math logic. If spending is negative, subtracting it increases available amount.
        # Should likely be: previous_month + budget + spent_money (if spent_money is negative)
        available[category_id] = previous_month + budget - spent_money
    
    # Calculate Amount to be Budgeted
    to_be_budgeted = income_total - sum(budgeted.values())
    
    # Calculate Overspent Categories
    overspent_categories = {}
    for category_id, avail_amount in available.items():
        if avail_amount < 0:
            overspent_categories[category_id] = avail_amount
            
    # TODO: Fix dictionary keys (remove trailing spaces like "available ") to make them easier to access
    return {
<<<<<<< HEAD
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
=======
        "income_total ":income_total,
        "available ": available,
        "activity: ": activity,
        "to_be_budgeted ": to_be_budgeted,
        "overspent_categories ": overspent_categories
        }

if __name__ == "__main__":
    # Example usage or testing
    pass
>>>>>>> 582fc96af9373069e75211dc8180b2ae7100e0e8
