from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import database
from app.models import Transaction, Category, Payee
from app.budget_engine import run_budget_engine
from datetime import date
import uuid

bp = Blueprint('main', __name__)


# --- Budget View ---

@bp.route('/')
def budget():
    categories = database.get_categories()
    transactions = database.get_transaction()

    budgeted = {c.id: c.budgeted for c in categories}
    previous = {c.id: 0.0 for c in categories}

    result = run_budget_engine(previous, budgeted, transactions)

    return render_template('budget.html',
                           categories=categories,
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
    category_map = {c.id: c.name for c in categories}
    return render_template('transactions.html', transactions=txns, category_map=category_map)


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
            category_id=category_id
        )
        database.add_transaction(transaction)
        flash('Transaction added!', 'success')
        return redirect(url_for('main.transactions'))

    categories = database.get_categories()
    return render_template('add_transaction.html', categories=categories, today=str(date.today()))


@bp.route('/transactions/<transaction_id>/delete', methods=['POST'])
def delete_transaction(transaction_id):
    database.delete_transaction(transaction_id)
    flash('Transaction deleted.', 'success')
    return redirect(url_for('main.transactions'))
