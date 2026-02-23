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
    available = defaultdict(float)
    
    for transaction in transactions:
        amount = transaction["amount"]
        category_id = transaction.get("category_id")
        if category_id is None:
            income_total += amount
        else:
            activity[category_id] += amount
    
    # Calculate Available Amounts 
    for category_id in budgeted:
        available[category_id] = previous_month_available[category_id ] + budgeted[category_id] - activity[category_id]
    
    # Calculate Amount to be Budgeted
    to_be_budgeted = income_total - sum(budgeted.values())
    
    # Calculate Overspent Categories
    overspent_categories = {}
    for category_id in dict(activity):
        if available[category_id] < 0:
            overspent_categories[category_id] = available[category_id]
    '''
    print("Income:", income_total)
    print("Available: ", dict(available))    
    print("Activity:", dict(activity))
    print("To Be Budgeted: ", to_be_budgeted)
    print("Overspent: ", overspent_categories)
    '''
    
    return {
        "income_total ":income_total,
        "available ": dict(available),
        "activity: ": dict(activity),
        "to_be_budgeted ": to_be_budgeted,
        "overspent_categories ": overspent_categories
        }