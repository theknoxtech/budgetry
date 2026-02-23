# Budgetry — Python Learning Plan

A step-by-step guide to building your own YNAB-style budget app while learning Python.

---

## Project Overview

You are building a personal budgeting app inspired by YNAB (You Need A Budget). The core idea is simple:

- You assign money to **categories** (rent, groceries, etc.)
- You record **transactions** against those categories
- The app tracks how much is **available** in each category
- Any unbudgeted income becomes **To Be Budgeted (TBB)**

The data flow looks like this:

```
Income + Previous Available → TBB → Budgeted → Available → Overspending
```

---

## What You Already Have

| File | Description |
|---|---|
| `app/budget_engine.py` | Core engine with the 4-step flow outlined in comments. Step 1 (scanning transactions) is partially done. |
| `app/test_engine.py` | Test data with categories, budgeted amounts, and sample transactions to drive the engine. |

---

## Phase 1 — Finish the Engine

**Core Python concepts:** `dict`, `defaultdict`, `sum()`, list comprehensions, return values

**Goal:** Make `run_budget_engine()` return meaningful data instead of `None`.

### Steps

1. **Complete Step 2** — Calculate `available` per category:
   ```
   available[cat] = previous_available[cat] + budgeted[cat] - activity[cat]
   ```

2. **Complete Step 3** — Calculate To Be Budgeted (TBB):
   ```
   tbb = total_income - sum(budgeted.values())
   ```

3. **Complete Step 4** — Find overspent categories (where `available < 0`)

4. **Return a result** — Return a dictionary from the function instead of `pass`. Example shape:
   ```python
   return {
       "available": available,
       "tbb": tbb,
       "overspent": overspent_categories,
   }
   ```

5. **Print a summary** — In `test_engine.py`, print the result in a readable format.

### You'll Know It's Working When
Running `test_engine.py` prints a table showing each category's budgeted amount, activity, and available balance — and correctly identifies any overspent categories.

---

## Phase 2 — Data Models

**Core Python concepts:** `@dataclass`, classes, `__init__`, `__repr__`, type hints

**Goal:** Replace plain dictionaries with proper Python objects so your data has structure and meaning.

### Steps

1. **Create a `Transaction` dataclass** with fields:
   - `id` (str)
   - `date` (str or datetime)
   - `amount` (float)
   - `payee` (str)
   - `memo` (str)
   - `category_id` (str or None — None means it's income)

2. **Create a `Category` dataclass** with fields:
   - `id` (str)
   - `name` (str)
   - `budgeted` (float)
   - `activity` (float)
   - `available` (float)

3. **Create a `Budget` class** that holds:
   - A list of categories
   - A list of transactions
   - Methods to add categories and transactions

4. **Refactor `run_budget_engine()`** to accept and return these objects instead of raw dicts.

### You'll Know It's Working When
You can do `transaction.amount` instead of `transaction["amount"]` and your IDE shows you autocomplete on object fields.

---

## Phase 3 — Data Persistence

**Core Python concepts:** `json` module, `csv` module, file open/read/write, exception handling (`try`/`except`)

**Goal:** Save and load your budget data so it persists between program runs.

### Steps

1. **Save to JSON** — Write a function that saves your budget categories and transactions to a `.json` file.

2. **Load from JSON** — Write a function that reads that file back and reconstructs your Python objects.

3. **Import from CSV** — Banks let you export transactions as CSV files. Write an importer that reads a CSV and creates `Transaction` objects from each row.

4. **Handle errors gracefully** — What happens if the file doesn't exist yet? Use `try`/`except` to handle it.

5. **Organize by month** — Store data in a way that separates different months (e.g., one JSON file per month, or a `month` field on each record).

### You'll Know It's Working When
You can quit the program, run it again, and all your data is still there.

---

## Phase 4 — CLI Interface

**Core Python concepts:** `input()`, `while` loops, string formatting (`f-strings`), conditional logic

**Goal:** Interact with the app from the terminal instead of editing the test file.

### Steps

1. **Build a main menu loop:**
   ```
   === Budgetry ===
   [1] View Budget
   [2] Add Transaction
   [3] Add Category
   [4] Quit
   ```

2. **View Budget** — Display a formatted table of categories showing budgeted, activity, and available amounts.

3. **Add Transaction** — Prompt the user for payee, amount, and category, then save it.

4. **Add Category** — Prompt for a name and budgeted amount, then save it.

5. **Input validation** — What if the user types a letter when you expect a number? Handle it.

### You'll Know It's Working When
You can run the app, add a transaction from the terminal, quit, reopen, and see the transaction still listed.

---

## Phase 5 — Monthly Budgets and Rollover

**Core Python concepts:** `datetime`, organizing data by time periods, more complex data structures

**Goal:** Handle real YNAB-style monthly budget flows.

### Steps

1. **Add a month concept** — Each budget period is tied to a specific month (e.g., `2026-02`).

2. **Month-to-month rollover** — When a new month starts, carry positive available balances forward as `previous_available` for the next month.

3. **Handle YNAB overspending rule** — If a category was overspent last month, that negative amount reduces this month's TBB.

4. **Monthly summary report** — Print a report showing all months and their totals.

### You'll Know It's Working When
You can create budgets for multiple months and the app correctly carries balances forward.

---

## Phase 6 — Simple Web UI (Stretch Goal)

**Core Python concepts:** web frameworks, HTTP, JSON APIs, HTML templates

**Goal:** Wrap the engine in a basic web interface you can open in a browser.

### Steps

1. **Add FastAPI or Flask** as a dependency and install it.

2. **Create API endpoints:**
   - `GET /budget` — return the current budget as JSON
   - `POST /transactions` — add a new transaction

3. **Build a simple HTML page** that calls those endpoints and displays the budget.

4. **Run a local server** and open it in your browser.

### You'll Know It's Working When
You can open `http://localhost:8000` in your browser and see your budget.

---

## Recommended Learning Resources

| Topic | Resource |
|---|---|
| Python basics | [docs.python.org/3/tutorial](https://docs.python.org/3/tutorial/) |
| Dataclasses | [docs.python.org/3/library/dataclasses.html](https://docs.python.org/3/library/dataclasses.html) |
| JSON module | [docs.python.org/3/library/json.html](https://docs.python.org/3/library/json.html) |
| CSV module | [docs.python.org/3/library/csv.html](https://docs.python.org/3/library/csv.html) |
| FastAPI (stretch) | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) |

---

## Immediate Next Step

Open [app/budget_engine.py](app/budget_engine.py) and complete **Step 2** in the existing comments. It's just a few lines of arithmetic using the data you're already collecting in Step 1. Once that works and prints correctly using your test data, you're building!
