from collections import defaultdict

'''
### Basic Flow ###
1. Calc activity per category (Scan transactions)
2. Calc total income
3. Calc total available (Per categorty)
4. Calc to be budgeted (Money available to budget)
5. Calc overspending per category

'''

def run_budget_engine():
    pass



transaction_id = defaultdict(int)
ids = [0,0,0,2,24,5]
for id in ids:
    if id == 0:
        transaction_id[id] += 1
print(transaction_id)