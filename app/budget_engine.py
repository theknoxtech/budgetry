from collections import defaultdict
from calendar import monthrange
from datetime import date, timedelta
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


def build_cashflow_calendar(accounts, transactions, recurring, year, month):
    """Build a daily cash flow calendar for a given month.

    Returns a list of dicts (one per day) with:
      - day: day number (1-31)
      - date: YYYY-MM-DD string
      - inflows: total money in
      - outflows: total money out
      - net: inflows - outflows
      - balance: running projected balance
      - events: list of {payee, amount, is_recurring}
    """
    days_in_month = monthrange(year, month)[1]
    today = date.today()
    month_prefix = f"{year:04d}-{month:02d}"

    # Starting balance = sum of all account balances
    starting_balance = sum(a.balance for a in accounts)

    # Index actual transactions by day
    txn_by_day = defaultdict(list)
    for t in transactions:
        if t.date.startswith(month_prefix):
            try:
                day = int(t.date[8:10])
                txn_by_day[day].append(t)
            except (ValueError, IndexError):
                pass

    # Project future recurring transactions for this month
    recurring_by_day = defaultdict(list)
    for rt in recurring:
        if not rt.is_active:
            continue
        # Generate all occurrences of this recurring txn in the target month
        next_d = rt.next_date
        if isinstance(next_d, str):
            try:
                next_d = date.fromisoformat(next_d)
            except ValueError:
                continue
        # Walk forward through the month
        for attempt in range(60):  # safety limit
            if next_d.year == year and next_d.month == month:
                if next_d > today:  # only future dates (past ones are already transactions)
                    recurring_by_day[next_d.day].append(rt)
                next_d = _advance_date(next_d, rt.frequency)
            elif next_d > date(year, month, days_in_month):
                break
            else:
                next_d = _advance_date(next_d, rt.frequency)

    # Build calendar
    # For days up to today: use actual transaction data
    # For future days: use recurring projections
    # Balance adjusts from starting balance minus all past activity
    # then projects forward with recurring

    # Calculate net activity before this month (starting_balance already reflects it)
    # For current month, we build running balance day by day
    running_balance = starting_balance

    # Subtract all current month transactions that already happened
    # (they're already in the account balance)
    # We need to ADD them back then replay day by day
    month_actual_net = sum(t.amount for t in transactions if t.date.startswith(month_prefix))
    running_balance -= month_actual_net  # rewind to start of month

    calendar_days = []
    for day in range(1, days_in_month + 1):
        day_date = f"{year:04d}-{month:02d}-{day:02d}"
        events = []
        inflows = 0.0
        outflows = 0.0

        # Actual transactions for this day
        for t in txn_by_day.get(day, []):
            events.append({'payee': t.payee, 'amount': t.amount, 'is_recurring': False})
            if t.amount >= 0:
                inflows += t.amount
            else:
                outflows += abs(t.amount)

        # Future recurring projections
        current_date = date(year, month, day)
        if current_date > today:
            for rt in recurring_by_day.get(day, []):
                events.append({'payee': rt.payee, 'amount': rt.amount, 'is_recurring': True})
                if rt.amount >= 0:
                    inflows += rt.amount
                else:
                    outflows += abs(rt.amount)

        net = inflows - outflows
        running_balance += net

        calendar_days.append({
            'day': day,
            'date': day_date,
            'inflows': round(inflows, 2),
            'outflows': round(outflows, 2),
            'net': round(net, 2),
            'balance': round(running_balance, 2),
            'events': events,
            'is_today': current_date == today,
            'is_past': current_date < today,
            'is_future': current_date > today,
            'weekday': current_date.weekday(),  # 0=Mon, 6=Sun
        })

    return calendar_days


def _advance_date(d, frequency):
    """Advance a date by the given frequency. Returns a new date."""
    if frequency == 'weekly':
        return d + timedelta(days=7)
    elif frequency == 'biweekly':
        return d + timedelta(days=14)
    elif frequency == 'monthly':
        month = d.month + 1
        year = d.year
        if month > 12:
            month = 1
            year += 1
        day = min(d.day, monthrange(year, month)[1])
        return date(year, month, day)
    elif frequency == 'yearly':
        try:
            return d.replace(year=d.year + 1)
        except ValueError:
            return d.replace(year=d.year + 1, day=28)
    return d + timedelta(days=30)


if __name__ == "__main__":
    # Example usage or testing
    pass
