from collections import defaultdict
from calendar import monthrange, month_name
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


def analyze_budget_patterns(all_transactions, categories, months_back=3):
    """Analyze spending patterns and suggest budget reallocations.

    Looks at the last N months of transactions to identify:
    - Categories consistently underspent (wasted budget)
    - Categories consistently overspent (needs more budget)
    - Suggested reallocations to balance things out

    Returns a dict with:
      - underspent: [{category_name, avg_unused, budgeted, avg_spent}]
      - overspent: [{category_name, avg_overage, budgeted, avg_spent}]
      - suggestions: [{from_category, to_category, amount, reason}]
      - total_recoverable: sum of avg_unused from underspent
    """
    today = date.today()
    cat_map = {c.id: c for c in categories}

    # Build monthly spending per category for the last N months
    monthly_spending = defaultdict(lambda: defaultdict(float))
    for t in all_transactions:
        if not t.category_id or t.category_id == "income":
            continue
        try:
            t_date = date.fromisoformat(t.date[:10])
        except ValueError:
            continue
        months_ago = (today.year - t_date.year) * 12 + (today.month - t_date.month)
        if 1 <= months_ago <= months_back:  # exclude current month
            month_key = f"{t_date.year:04d}-{t_date.month:02d}"
            monthly_spending[t.category_id][month_key] += abs(t.amount)

    underspent = []
    overspent = []

    for cat in categories:
        if cat.budgeted <= 0:
            continue

        spending_by_month = monthly_spending.get(cat.id, {})
        if not spending_by_month:
            # No spending in past months but has budget — fully underspent
            underspent.append({
                'category_id': cat.id,
                'category_name': cat.name,
                'budgeted': cat.budgeted,
                'avg_spent': 0.0,
                'avg_unused': cat.budgeted,
                'months_analyzed': months_back,
            })
            continue

        months_with_data = len(spending_by_month)
        avg_spent = sum(spending_by_month.values()) / max(months_with_data, 1)
        diff = cat.budgeted - avg_spent

        if diff > cat.budgeted * 0.15:  # >15% underspent consistently
            underspent.append({
                'category_id': cat.id,
                'category_name': cat.name,
                'budgeted': cat.budgeted,
                'avg_spent': round(avg_spent, 2),
                'avg_unused': round(diff, 2),
                'months_analyzed': months_with_data,
            })
        elif diff < -(cat.budgeted * 0.1):  # >10% overspent consistently
            overspent.append({
                'category_id': cat.id,
                'category_name': cat.name,
                'budgeted': cat.budgeted,
                'avg_spent': round(avg_spent, 2),
                'avg_overage': round(abs(diff), 2),
                'months_analyzed': months_with_data,
            })

    # Sort by magnitude
    underspent.sort(key=lambda x: x['avg_unused'], reverse=True)
    overspent.sort(key=lambda x: x['avg_overage'], reverse=True)

    # Generate suggestions — match overspent needs with underspent surplus
    suggestions = []
    remaining_surplus = {u['category_id']: u['avg_unused'] for u in underspent}

    for over in overspent:
        needed = over['avg_overage']
        for under in underspent:
            if needed <= 0:
                break
            available = remaining_surplus.get(under['category_id'], 0)
            if available <= 0:
                continue
            transfer = min(needed, available)
            suggestions.append({
                'from_category': under['category_name'],
                'from_id': under['category_id'],
                'to_category': over['category_name'],
                'to_id': over['category_id'],
                'amount': round(transfer, 2),
                'reason': f"{over['category_name']} overspends by ${over['avg_overage']:.0f}/mo avg",
            })
            remaining_surplus[under['category_id']] -= transfer
            needed -= transfer

    total_recoverable = sum(u['avg_unused'] for u in underspent)

    return {
        'underspent': underspent,
        'overspent': overspent,
        'suggestions': suggestions,
        'total_recoverable': round(total_recoverable, 2),
        'months_analyzed': months_back,
    }


def run_forecast(accounts, categories, all_transactions, recurring, months_ahead=6, adjustments=None):
    """Project future balances based on current spending patterns and adjustments.

    Args:
        accounts: list of Account objects
        categories: list of Category objects
        all_transactions: all transactions for the budget
        recurring: list of RecurringTransaction objects
        months_ahead: number of months to project
        adjustments: dict of {category_id: new_budget_amount} for what-if scenarios

    Returns:
        list of monthly projections: [{month_label, income, expenses, net, balance}]
    """
    today = date.today()
    starting_balance = sum(a.balance for a in accounts)

    # Calculate average monthly income from past 3 months
    monthly_income = defaultdict(float)
    monthly_expenses = defaultdict(float)
    for t in all_transactions:
        try:
            t_date = date.fromisoformat(t.date[:10])
        except ValueError:
            continue
        months_ago = (today.year - t_date.year) * 12 + (today.month - t_date.month)
        if 1 <= months_ago <= 3:
            month_key = f"{t_date.year:04d}-{t_date.month:02d}"
            if t.category_id == "income" or t.amount > 0:
                monthly_income[month_key] += t.amount
            else:
                monthly_expenses[month_key] += abs(t.amount)

    avg_income = sum(monthly_income.values()) / max(len(monthly_income), 1)
    avg_expenses = sum(monthly_expenses.values()) / max(len(monthly_expenses), 1)

    # If adjustments are provided, recalculate expected expenses
    if adjustments:
        total_budgeted = sum(c.budgeted for c in categories)
        adjusted_total = 0
        for c in categories:
            if c.id in adjustments:
                adjusted_total += adjustments[c.id]
            else:
                adjusted_total += c.budgeted
        # Scale expenses proportionally to budget change
        if total_budgeted > 0:
            expense_ratio = adjusted_total / total_budgeted
            avg_expenses = avg_expenses * expense_ratio

    # Calculate recurring monthly totals for more accurate projections
    recurring_monthly_in = 0.0
    recurring_monthly_out = 0.0
    for rt in recurring:
        if not rt.is_active:
            continue
        monthly_equiv = rt.amount
        if rt.frequency == 'weekly':
            monthly_equiv = rt.amount * 4.33
        elif rt.frequency == 'biweekly':
            monthly_equiv = rt.amount * 2.17
        elif rt.frequency == 'yearly':
            monthly_equiv = rt.amount / 12

        if monthly_equiv >= 0:
            recurring_monthly_in += monthly_equiv
        else:
            recurring_monthly_out += abs(monthly_equiv)

    # Use the higher of avg or recurring as the baseline
    projected_income = max(avg_income, recurring_monthly_in)
    projected_expenses = max(avg_expenses, recurring_monthly_out)

    # Build monthly projections
    projections = []
    balance = starting_balance

    for i in range(months_ahead):
        future_month = today.month + i + 1
        future_year = today.year
        while future_month > 12:
            future_month -= 12
            future_year += 1

        net = projected_income - projected_expenses
        balance += net

        projections.append({
            'month_label': f"{month_name[future_month]} {future_year}",
            'month_num': future_month,
            'year': future_year,
            'income': round(projected_income, 2),
            'expenses': round(projected_expenses, 2),
            'net': round(net, 2),
            'balance': round(balance, 2),
        })

    return {
        'projections': projections,
        'avg_income': round(projected_income, 2),
        'avg_expenses': round(projected_expenses, 2),
        'starting_balance': round(starting_balance, 2),
        'months_ahead': months_ahead,
    }


def calculate_streaks(all_transactions, categories, accounts):
    """Calculate financial streaks and milestones.

    Returns:
      - no_spend_streak: consecutive days with no spending (ending today)
      - under_budget_streaks: {category_id: consecutive months under budget}
      - savings_rate: percentage of income saved this month
      - milestones: list of achieved milestones
      - active_streaks: list of current active streaks for display
    """
    today = date.today()

    # --- No-spend streak ---
    # Find consecutive days ending at yesterday with zero spending
    spending_dates = set()
    for t in all_transactions:
        if t.category_id != "income" and t.amount < 0:
            try:
                spending_dates.add(date.fromisoformat(t.date[:10]))
            except ValueError:
                pass

    no_spend_streak = 0
    if spending_dates:
        check_date = today - timedelta(days=1)
        while check_date not in spending_dates and check_date >= today - timedelta(days=365):
            no_spend_streak += 1
            check_date -= timedelta(days=1)

    # --- Under budget streaks per category ---
    # Count consecutive past months each category was under budget
    cat_map = {c.id: c for c in categories}
    monthly_spending_by_cat = defaultdict(lambda: defaultdict(float))
    for t in all_transactions:
        if not t.category_id or t.category_id == "income":
            continue
        try:
            t_date = date.fromisoformat(t.date[:10])
        except ValueError:
            continue
        month_key = (t_date.year, t_date.month)
        monthly_spending_by_cat[t.category_id][month_key] += abs(t.amount)

    under_budget_streaks = {}
    for cat in categories:
        if cat.budgeted <= 0:
            continue
        streak = 0
        for months_back in range(1, 13):  # check up to 12 months
            check_month = today.month - months_back
            check_year = today.year
            while check_month <= 0:
                check_month += 12
                check_year -= 1
            spent = monthly_spending_by_cat[cat.id].get((check_year, check_month), 0)
            if spent <= cat.budgeted:
                streak += 1
            else:
                break
        if streak > 0:
            under_budget_streaks[cat.id] = {
                'category_name': cat.name,
                'months': streak,
            }

    # --- Savings rate (current month) ---
    month_prefix = f"{today.year:04d}-{today.month:02d}"
    month_income = 0.0
    month_spending = 0.0
    for t in all_transactions:
        if not t.date.startswith(month_prefix):
            continue
        if t.category_id == "income" or t.amount > 0:
            month_income += abs(t.amount)
        else:
            month_spending += abs(t.amount)

    savings_rate = ((month_income - month_spending) / month_income * 100) if month_income > 0 else 0

    # --- Total balance milestone ---
    total_balance = sum(a.balance for a in accounts)

    # --- Build milestones ---
    milestones = []

    # No-spend milestones
    if no_spend_streak >= 1:
        milestones.append({'icon': 'shield', 'title': f'{no_spend_streak}-day no-spend streak', 'type': 'streak'})
    if no_spend_streak >= 7:
        milestones.append({'icon': 'fire', 'title': 'Week without spending!', 'type': 'achievement'})
    if no_spend_streak >= 30:
        milestones.append({'icon': 'trophy', 'title': 'Month without spending!', 'type': 'achievement'})

    # Under budget milestones
    for cat_id, info in under_budget_streaks.items():
        if info['months'] >= 3:
            milestones.append({
                'icon': 'target',
                'title': f"{info['category_name']}: {info['months']}mo under budget",
                'type': 'streak',
            })

    # Savings milestones
    if savings_rate >= 20:
        milestones.append({'icon': 'piggy', 'title': f'Saving {savings_rate:.0f}% of income this month', 'type': 'achievement'})
    if savings_rate >= 50:
        milestones.append({'icon': 'star', 'title': 'Super saver! 50%+ savings rate', 'type': 'achievement'})

    # Balance milestones
    balance_thresholds = [1000, 5000, 10000, 25000, 50000, 100000]
    for threshold in balance_thresholds:
        if total_balance >= threshold:
            milestones.append({
                'icon': 'bank',
                'title': f'Balance over ${threshold:,}',
                'type': 'milestone',
            })

    # Build active streaks for display
    active_streaks = []
    if no_spend_streak > 0:
        active_streaks.append({
            'name': 'No-Spend Days',
            'value': no_spend_streak,
            'unit': 'days',
            'color': 'positive',
        })

    # Top 3 under-budget streaks
    sorted_streaks = sorted(under_budget_streaks.values(), key=lambda x: x['months'], reverse=True)[:3]
    for s in sorted_streaks:
        active_streaks.append({
            'name': f"{s['category_name']} Under Budget",
            'value': s['months'],
            'unit': 'months',
            'color': 'accent',
        })

    if savings_rate > 0:
        active_streaks.append({
            'name': 'Savings Rate',
            'value': round(savings_rate, 1),
            'unit': '%',
            'color': 'positive' if savings_rate >= 20 else 'warning' if savings_rate >= 10 else 'negative',
        })

    return {
        'no_spend_streak': no_spend_streak,
        'under_budget_streaks': under_budget_streaks,
        'savings_rate': round(savings_rate, 1),
        'total_balance': round(total_balance, 2),
        'milestones': milestones,
        'active_streaks': active_streaks,
    }


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
