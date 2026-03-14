from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app import database
from app.models import Transaction, Category, Payee, Account
from app.budget_engine import run_budget_engine
from datetime import date, datetime
import uuid

bp = Blueprint('main', __name__)


# --- Budget View ---

@bp.route('/')
def budget():
    categories = database.get_categories()
    transactions = database.get_transaction()
    accounts = database.get_accounts()

    budgeted = {c.id: c.budgeted for c in categories}
    previous = {c.id: 0.0 for c in categories}

    result = run_budget_engine(previous, budgeted, transactions)

    return render_template('budget.html',
                           categories=categories,
                           accounts=accounts,
                           result=result)


@bp.route('/categories/<category_id>/budget', methods=['POST'])
def update_budget(category_id):
    try:
        amount = float(request.form['budgeted'])
        database.update_category_budget(category_id, amount)
        flash('Budget updated!', 'success')
    except (ValueError, KeyError):
        flash('Please enter a valid number.', 'error')
    return redirect(url_for('main.budget'))


# --- Accounts ---

@bp.route('/accounts')
def accounts():
    accts = database.get_accounts()
    plaid_status = {a.id: database.get_plaid_item_by_account(a.id) for a in accts}
    return render_template('accounts.html', accounts=accts, plaid_status=plaid_status)


@bp.route('/accounts/add', methods=['POST'])
def add_account():
    name = request.form.get('name', '').strip()
    account_type = request.form.get('account_type', '').strip()
    institution = request.form.get('institution', '').strip()

    if not name:
        flash('Account name is required.', 'error')
        return redirect(url_for('main.accounts'))

    account = Account(
        id=str(uuid.uuid4()),
        name=name,
        account_type=account_type,
        institution=institution,
        balance=0.00
    )
    database.add_account(account)
    flash(f'Account "{name}" added!', 'success')
    return redirect(url_for('main.accounts'))


@bp.route('/accounts/<account_id>/delete', methods=['POST'])
def delete_account(account_id):
    database.delete_account(account_id)
    flash('Account deleted.', 'success')
    return redirect(url_for('main.accounts'))


# --- Categories ---

@bp.route('/categories')
def categories():
    cats = database.get_categories()
    return render_template('categories.html', categories=cats)


@bp.route('/categories/add', methods=['POST'])
def add_category():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('main.categories'))

    category = Category(
        id=str(uuid.uuid4()),
        name=name,
        budgeted=0.00,
        activity=0.00,
        available=0.00
    )
    database.add_category(category)
    flash(f'Category "{name}" added!', 'success')
    return redirect(url_for('main.categories'))


@bp.route('/categories/<category_id>/delete', methods=['POST'])
def delete_category(category_id):
    database.delete_category(category_id)
    flash('Category deleted.', 'success')
    return redirect(url_for('main.categories'))


# --- Transactions ---

@bp.route('/transactions')
def transactions():
    txns = database.get_transaction()
    categories = database.get_categories()
    accts = database.get_accounts()
    category_map = {c.id: c.name for c in categories}
    account_map = {a.id: a.name for a in accts}
    return render_template('transactions.html', transactions=txns, category_map=category_map, account_map=account_map)


@bp.route('/transactions/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
        except (ValueError, KeyError):
            flash('Please enter a valid amount.', 'error')
            return redirect(url_for('main.add_transaction'))

        payee = request.form.get('payee', '').strip()
        memo = request.form.get('memo', '').strip()
        category_id = request.form.get('category_id', '')
        account_id = request.form.get('account_id', '')
        txn_date = request.form.get('date', str(date.today()))

        if not payee:
            flash('Payee is required.', 'error')
            return redirect(url_for('main.add_transaction'))

        transaction = Transaction(
            id=str(uuid.uuid4()),
            date=txn_date,
            payee=payee,
            amount=amount,
            memo=memo,
            category_id=category_id,
            account_id=account_id
        )
        database.add_transaction(transaction)
        flash('Transaction added!', 'success')
        return redirect(url_for('main.transactions'))

    categories = database.get_categories()
    accts = database.get_accounts()
    return render_template('add_transaction.html', categories=categories, accounts=accts, today=str(date.today()))


@bp.route('/transactions/<transaction_id>/delete', methods=['POST'])
def delete_transaction(transaction_id):
    database.delete_transaction(transaction_id)
    flash('Transaction deleted.', 'success')
    return redirect(url_for('main.transactions'))


# --- Plaid Integration ---

@bp.route('/accounts/<account_id>/connect')
def plaid_connect(account_id):
    account = database.get_account(account_id)
    if not account:
        flash('Account not found.', 'error')
        return redirect(url_for('main.accounts'))
    return render_template('plaid_connect.html', account=account)


@bp.route('/plaid/create_link_token', methods=['POST'])
def create_link_token():
    from app.plaid_client import get_plaid_client
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products
    from plaid.model.country_code import CountryCode

    client = get_plaid_client()
    plaid_request = LinkTokenCreateRequest(
        products=[Products("transactions")],
        client_name="Budgetry",
        country_codes=[CountryCode("US")],
        language="en",
        user=LinkTokenCreateRequestUser(client_user_id="budgetry-user")
    )
    response = client.link_token_create(plaid_request)
    return jsonify({"link_token": response.link_token})


@bp.route('/plaid/exchange_token', methods=['POST'])
def exchange_token():
    from app.plaid_client import get_plaid_client
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

    data = request.get_json()
    public_token = data.get('public_token')
    account_id = data.get('account_id')

    client = get_plaid_client()
    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    response = client.item_public_token_exchange(exchange_request)

    database.add_plaid_item(
        plaid_item_id=str(uuid.uuid4()),
        account_id=account_id,
        access_token=response.access_token,
        item_id=response.item_id,
        institution_name=""
    )

    return jsonify({"success": True})


@bp.route('/plaid/sync/<account_id>', methods=['POST'])
def plaid_sync(account_id):
    from app.plaid_client import get_plaid_client
    from plaid.model.transactions_sync_request import TransactionsSyncRequest
    from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest

    plaid_item = database.get_plaid_item_by_account(account_id)
    if not plaid_item:
        flash('No bank connection found for this account.', 'error')
        return redirect(url_for('main.accounts'))

    client = get_plaid_client()
    access_token = plaid_item['access_token']
    sync_cursor = plaid_item['cursor'] or ""

    added_count = 0
    removed_count = 0
    has_more = True

    while has_more:
        sync_request = TransactionsSyncRequest(
            access_token=access_token,
            cursor=sync_cursor
        )
        response = client.transactions_sync(sync_request)

        # Process added transactions
        for txn in response.added:
            plaid_txn_id = txn.transaction_id
            if database.get_transaction_by_plaid_id(plaid_txn_id):
                continue

            transaction = Transaction(
                id=str(uuid.uuid4()),
                date=str(txn.date),
                payee=txn.merchant_name or txn.name or "Unknown",
                amount=-txn.amount,  # Plaid: positive = debit, we negate
                memo=txn.name or "",
                category_id="",
                account_id=account_id,
                plaid_transaction_id=plaid_txn_id
            )
            database.add_transaction(transaction)
            added_count += 1

        # Process removed transactions
        for txn in response.removed:
            database.delete_transaction_by_plaid_id(txn.transaction_id)
            removed_count += 1

        sync_cursor = response.next_cursor
        has_more = response.has_more

    # Update the sync cursor and timestamp
    database.update_plaid_cursor(plaid_item['id'], sync_cursor, datetime.now().isoformat())

    # Update account balance from Plaid
    try:
        balance_request = AccountsBalanceGetRequest(access_token=access_token)
        balance_response = client.accounts_balance_get(balance_request)
        if balance_response.accounts:
            total_balance = sum(a.balances.current or 0 for a in balance_response.accounts)
            database.update_account_balance(account_id, total_balance)
    except Exception:
        pass  # Balance update is best-effort

    msg = f"Synced {added_count} new transaction{'s' if added_count != 1 else ''}"
    if removed_count:
        msg += f", removed {removed_count}"
    flash(msg, 'success')
    return redirect(url_for('main.accounts'))
