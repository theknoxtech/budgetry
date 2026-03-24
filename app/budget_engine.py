from collections import defaultdict
from calendar import monthrange
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

def calculate_spending_velocity(transactions, budgeted, year, month):
    """Calculate spending velocity per category.

    Returns a dict keyed by category_id with:
      - daily_rate: average spending per day so far
      - projected: projected total spending by month end
      - budget: budgeted amount
      - pace: 'under', 'on_track', 'over' (within 5% = on_track)
      - pace_pct: projected as percentage of budget (0 if no budget)
      - days_elapsed: days into the month
      - days_total: total days in the month
    """
    today = date.today()
    days_in_month = monthrange(year, month)[1]

    # For past months, use full month; for current month, use days elapsed
    if year == today.year and month == today.month:
        days_elapsed = today.day
    elif date(year, month, 1) < today:
        days_elapsed = days_in_month  # past month — all days elapsed
    else:
        days_elapsed = 0  # future month

    if days_elapsed == 0:
        return {}

    # Sum spending per category (exclude income)
    spent_by_cat = defaultdict(float)
    for t in transactions:
        if t.category_id and t.category_id != "income":
            spent_by_cat[t.category_id] += abs(t.amount)

    velocity = {}
    for cat_id, budget in budgeted.items():
        spent = spent_by_cat.get(cat_id, 0.0)
        daily_rate = spent / days_elapsed
        projected = daily_rate * days_in_month

        if budget > 0:
            pace_pct = (projected / budget) * 100
            if pace_pct <= 95:
                pace = 'under'
            elif pace_pct <= 105:
                pace = 'on_track'
            else:
                pace = 'over'
        else:
            pace_pct = 0
            pace = 'under' if spent == 0 else 'over'

        velocity[cat_id] = {
            'daily_rate': round(daily_rate, 2),
            'projected': round(projected, 2),
            'budget': budget,
            'pace': pace,
            'pace_pct': round(pace_pct, 1),
            'days_elapsed': days_elapsed,
            'days_total': days_in_month,
        }

    return velocity


if __name__ == "__main__":
    # Example usage or testing
    pass
