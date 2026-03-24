from collections import defaultdict
from datetime import date
from app.models import Transaction, Category

# TODO Add feature to get total spending by day, month, year


def total_spending():
    transactions = get_transaction()
    amounts = [transaction.amount for transaction in transactions]
    return sum(amounts)





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

    available = {}
    for category_id, budget in budgeted.items():
        previous_month = previous_month_available.get(category_id, 0.0)
        spent_money = activity.get(category_id, 0.0)
        available[category_id] = previous_month + budget - spent_money

    to_be_budgeted = income_total - sum(budgeted.values())

    overspent_categories = {}
    for category_id, avail_amount in available.items():
        if avail_amount < 0:
            overspent_categories[category_id] = avail_amount

    return {
        "income_total": income_total,
        "available": available,
        "activity": activity,
        "to_be_budgeted": to_be_budgeted,
        "overspent_categories": overspent_categories
    }


def calculate_monthly_needed(target_amount, target_type, target_date, current_available):
    today = date.today()
    remaining = target_amount - current_available
    if remaining <= 0:
        return 0.0

    if target_type == 'by_date' and target_date:
        if isinstance(target_date, str):
            target_date = date.fromisoformat(target_date)
        months_left = (target_date.year - today.year) * 12 + (target_date.month - today.month)
        if months_left <= 0:
            return remaining
        return remaining / months_left

    if target_type == 'monthly':
        return target_amount

    return remaining

if __name__ == "__main__":
    # Example usage or testing
    pass
