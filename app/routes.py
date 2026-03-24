from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, g, current_app
from app import database
from app.models import Transaction, Category, Payee, Account, User, BudgetRecord, CategoryGroup, RecurringTransaction
from app.budget_engine import run_budget_engine, calculate_monthly_needed
from app.auth import login_required, admin_required, oauth, is_auth0_enabled
from datetime import date, datetime, timedelta
from calendar import month_name
from collections import defaultdict
from urllib.parse import urlencode, quote_plus
import uuid

bp = Blueprint('main', __name__)


# --- Before Request: load budget context ---

@bp.before_request
def load_budget_context():
    if 'user_id' in session:
        # Validate the user still exists in the database
        user = database.get_user_by_id(session['user_id'])
        if not user:
            session.clear()
            g.user_id = None
            g.budget_id = None
            return
        g.user_id = session['user_id']
        g.budget_id = session.get('active_budget_id', '')
    else:
        g.user_id = None
        g.budget_id = None


# --- Auth Routes ---

@bp.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('main.budget'))
    return render_template('login.html', auth0_enabled=is_auth0_enabled())


@bp.route('/auth/local-login', methods=['POST'])
def local_login():
    from werkzeug.security import check_password_hash
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect(url_for('main.login'))

    user = database.get_user_by_username(username)
    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        flash('Invalid username or password.', 'error')
        return redirect(url_for('main.login'))

    if not user.is_active:
        flash('Your account has been deactivated. Contact an administrator.', 'error')
        return redirect(url_for('main.login'))

    # Check if MFA is enabled (TOTP)
    if user.totp_secret:
        session['mfa_user_id'] = user.id
        return redirect(url_for('main.mfa_challenge'))

    return _complete_login(user)


@bp.route('/auth/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('main.budget'))

    if request.method == 'POST':
        from werkzeug.security import generate_password_hash
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('main.register'))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('main.register'))

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return redirect(url_for('main.register'))

        if database.get_user_by_username(username):
            flash('Username already taken.', 'error')
            return redirect(url_for('main.register'))

        if email and database.get_user_by_email(email):
            flash('Email already registered.', 'error')
            return redirect(url_for('main.register'))

        pw_hash = generate_password_hash(password)
        user = database.create_local_user(username, email, pw_hash)

        # First user auto-promoted to admin
        all_users = database.get_all_users()
        if len(all_users) == 1:
            connection = database.get_connection()
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user.id,))
            connection.commit()
            connection.close()

        return _complete_login(user)

    return render_template('register.html', auth0_enabled=is_auth0_enabled())


@bp.route('/auth/mfa-challenge', methods=['GET', 'POST'])
def mfa_challenge():
    if 'mfa_user_id' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        import pyotp
        code = request.form.get('code', '').strip()
        user = database.get_user_by_id(session['mfa_user_id'])
        if not user or not user.totp_secret:
            session.pop('mfa_user_id', None)
            return redirect(url_for('main.login'))

        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code):
            session.pop('mfa_user_id', None)
            return _complete_login(user)
        else:
            flash('Invalid verification code.', 'error')

    return render_template('mfa_challenge.html')


def _complete_login(user):
    """Set session and redirect after successful authentication."""
    session['user_id'] = user.id
    budgets = database.get_budgets_for_user(user.id)
    if budgets:
        session['active_budget_id'] = budgets[0].id
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('main.budget'))
    else:
        return redirect(url_for('main.onboarding'))


@bp.route('/auth/login')
def auth_login():
    if not is_auth0_enabled():
        flash('OAuth is not configured.', 'error')
        return redirect(url_for('main.login'))
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for('main.callback', _external=True)
    )


@bp.route('/auth/signup')
def signup():
    if not is_auth0_enabled():
        return redirect(url_for('main.register'))
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for('main.callback', _external=True),
        screen_hint="signup"
    )


@bp.route('/auth/callback')
def callback():
    if not is_auth0_enabled():
        return redirect(url_for('main.login'))
    token = oauth.auth0.authorize_access_token()
    userinfo = token.get("userinfo", {})

    user = database.upsert_user_from_auth0(
        auth0_id=userinfo["sub"],
        email=userinfo.get("email", ""),
        username=userinfo.get("nickname", userinfo.get("name", "User"))
    )

    if not user.is_active:
        session.clear()
        flash('Your account has been deactivated. Contact an administrator.', 'error')
        return redirect(url_for('main.login'))

    return _complete_login(user)


@bp.route('/auth/logout')
def logout():
    session.clear()
    if is_auth0_enabled() and current_app.config.get("AUTH0_DOMAIN"):
        return redirect(
            f'https://{current_app.config["AUTH0_DOMAIN"]}/v2/logout?'
            + urlencode(
                {"returnTo": url_for("main.login", _external=True),
                 "client_id": current_app.config["AUTH0_CLIENT_ID"]},
                quote_via=quote_plus
            )
        )
    return redirect(url_for('main.login'))


# --- Onboarding (first-time user) ---

@bp.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    # If user already has budgets, skip onboarding
    budgets = database.get_budgets_for_user(g.user_id)
    if budgets:
        session['active_budget_id'] = budgets[0].id
        return redirect(url_for('main.budget'))

    if request.method == 'POST':
        name = request.form.get('budget_name', '').strip()
        if not name:
            flash('Please give your budget a name.', 'error')
            return redirect(url_for('main.onboarding'))

        now = datetime.now().isoformat()
        budget = BudgetRecord(
            id=str(uuid.uuid4()),
            name=name,
            is_shared=0,
            created_at=now
        )
        database.add_budget(budget)
        database.add_budget_member(budget.id, g.user_id, "owner")
        session['active_budget_id'] = budget.id

        user = database.get_user_by_id(g.user_id)
        flash(f'Welcome, {user.username}! Your budget "{name}" is ready.', 'success')
        return redirect(url_for('main.budget'))

    user = database.get_user_by_id(g.user_id)
    return render_template('onboarding.html', username=user.username)


# --- Budget Switching ---

@bp.route('/switch-budget', methods=['POST'])
@login_required
def switch_budget():
    budget_id = request.form.get('budget_id', '')
    if budget_id and database.is_budget_member(budget_id, g.user_id):
        session['active_budget_id'] = budget_id
        budget = database.get_budget_by_id(budget_id)
        if budget:
            flash(f'Switched to {budget.name}.', 'success')
    return redirect(url_for('main.budget'))


@bp.route('/budgets/create-shared', methods=['POST'])
@login_required
def create_shared_budget():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Budget name is required.', 'error')
        return redirect(url_for('main.settings', tab='budget'))

    now = datetime.now().isoformat()
    shared_budget = BudgetRecord(
        id=str(uuid.uuid4()),
        name=name,
        is_shared=1,
        created_at=now
    )
    database.add_budget(shared_budget)
    database.add_budget_member(shared_budget.id, g.user_id, "owner")

    session['active_budget_id'] = shared_budget.id
    flash(f'Shared budget "{name}" created!', 'success')
    return redirect(url_for('main.settings', tab='budget'))


@bp.route('/budgets/<budget_id>/invite', methods=['POST'])
@login_required
def invite_to_budget(budget_id):
    if not database.is_budget_member(budget_id, g.user_id):
        flash('You do not have access to this budget.', 'error')
        return redirect(url_for('main.settings', tab='budget'))

    budget = database.get_budget_by_id(budget_id)
    if not budget or not budget.is_shared:
        flash('Can only invite to shared budgets.', 'error')
        return redirect(url_for('main.settings', tab='budget'))

    email = request.form.get('email', '').strip()
    if not email:
        flash('Email address is required.', 'error')
        return redirect(url_for('main.settings', tab='budget'))

    user = database.get_user_by_email(email)
    if not user:
        flash(f'No user found with email "{email}".', 'error')
        return redirect(url_for('main.settings', tab='budget'))

    if database.is_budget_member(budget_id, user.id):
        flash(f'{email} already has access to this budget.', 'error')
        return redirect(url_for('main.settings', tab='budget'))

    database.add_budget_member(budget_id, user.id, "member")
    flash(f'{user.username} has been added to "{budget.name}"!', 'success')
    return redirect(url_for('main.settings', tab='budget'))


# --- Budget View ---

@bp.route('/')
@login_required
def budget():
    # Parse month from query param (default: current month)
    month_str = request.args.get('month', '')
    today = date.today()
    try:
        year, month = int(month_str[:4]), int(month_str[5:7])
    except (ValueError, IndexError):
        year, month = today.year, today.month

    month_label = f"{month_name[month]} {year}"
    month_prefix = f"{year:04d}-{month:02d}"

    # Compute prev/next month strings
    if month == 1:
        prev_month = f"{year - 1:04d}-12"
    else:
        prev_month = f"{year:04d}-{month - 1:02d}"
    if month == 12:
        next_month = f"{year + 1:04d}-01"
    else:
        next_month = f"{year:04d}-{month + 1:02d}"

    categories = database.get_categories(g.budget_id)
    all_transactions = database.get_transaction(g.budget_id)
    accounts = database.get_accounts(g.budget_id)
    groups = database.get_category_groups(g.budget_id)

    # Process recurring transactions due today or earlier
    _process_recurring(g.budget_id)

    # Filter transactions to selected month
    transactions = [t for t in all_transactions if t.date.startswith(month_prefix)]

    budgeted = {c.id: c.budgeted for c in categories}
    previous = {c.id: 0.0 for c in categories}

    result = run_budget_engine(previous, budgeted, transactions)

    # Calculate target info per category
    available = result.get('available', {})
    target_info = {}
    for c in categories:
        if c.target_type:
            avail = available.get(c.id, 0.0)
            monthly = calculate_monthly_needed(c.target_amount, c.target_type, c.target_date, avail)
            target_info[c.id] = {
                'monthly_needed': monthly,
                'on_track': c.budgeted >= monthly if monthly > 0 else True
            }

    # Organize categories by group
    grouped_categories = []
    ungrouped = []
    group_map = {gr.id: gr for gr in groups}
    cats_by_group = defaultdict(list)
    for c in categories:
        if c.group_id and c.group_id in group_map:
            cats_by_group[c.group_id].append(c)
        else:
            ungrouped.append(c)

    for gr in groups:
        grouped_categories.append({
            'group': gr,
            'categories': cats_by_group.get(gr.id, [])
        })

    return render_template('budget.html',
                           categories=categories,
                           accounts=accounts,
                           result=result,
                           target_info=target_info,
                           month_label=month_label,
                           prev_month=prev_month,
                           next_month=next_month,
                           grouped_categories=grouped_categories,
                           ungrouped_categories=ungrouped,
                           groups=groups)


@bp.route('/categories/<category_id>/budget', methods=['POST'])
@login_required
def update_budget(category_id):
    try:
        amount = float(request.form['budgeted'])
        database.update_category_budget(category_id, amount)
        flash('Budget updated!', 'success')
    except (ValueError, KeyError):
        flash('Please enter a valid number.', 'error')
    return redirect(url_for('main.budget'))


# --- Settings ---

@bp.route('/settings')
@login_required
def settings():
    accts = database.get_accounts(g.budget_id)
    plaid_status = {a.id: database.get_plaid_item_by_account(a.id) for a in accts}
    active_budget = database.get_budget_by_id(g.budget_id)
    cats = database.get_categories(g.budget_id)
    defaults = database.get_all_budget_defaults(g.budget_id)
    rules = database.get_rules(g.budget_id)
    category_map = {c.id: c.name for c in cats}
    account_map = {a.id: a.name for a in accts}
    return render_template('settings.html',
                           accounts=accts,
                           plaid_status=plaid_status,
                           budget=active_budget,
                           categories=cats,
                           defaults=defaults,
                           rules=rules,
                           category_map=category_map,
                           account_map=account_map)


@bp.route('/accounts')
@login_required
def accounts():
    return redirect(url_for('main.settings'))


@bp.route('/accounts/add', methods=['POST'])
@login_required
def add_account():
    name = request.form.get('name', '').strip()
    account_type = request.form.get('account_type', '').strip()
    institution = request.form.get('institution', '').strip()

    if not name:
        flash('Account name is required.', 'error')
        return redirect(url_for('main.settings', tab='accounts'))

    account = Account(
        id=str(uuid.uuid4()),
        name=name,
        account_type=account_type,
        institution=institution,
        balance=0.00,
        budget_id=g.budget_id
    )
    database.add_account(account)
    flash(f'Account "{name}" added!', 'success')
    return redirect(url_for('main.settings', tab='accounts'))


@bp.route('/accounts/<account_id>/delete', methods=['POST'])
@login_required
def delete_account(account_id):
    database.delete_account(account_id, g.budget_id)
    flash('Account deleted.', 'success')
    return redirect(url_for('main.settings', tab='accounts'))


# --- Settings: Defaults ---

@bp.route('/settings/defaults', methods=['POST'])
@login_required
def save_defaults():
    default_account = request.form.get('default_account_id', '')
    default_category = request.form.get('default_category_id', '')
    database.set_budget_default(g.budget_id, 'default_account_id', default_account)
    database.set_budget_default(g.budget_id, 'default_category_id', default_category)
    flash('Defaults saved!', 'success')
    return redirect(url_for('main.settings', tab='defaults'))


# --- Settings: Rules ---

@bp.route('/settings/rules/add', methods=['POST'])
@login_required
def add_rule():
    rule_type = request.form.get('rule_type', '').strip()
    match_type = request.form.get('match_type', '').strip()
    match_value = request.form.get('match_value', '').strip()
    action_type = request.form.get('action_type', '').strip()

    # For "between" amount rules, combine low|high
    if match_type == 'between':
        match_value_high = request.form.get('match_value_high', '').strip()
        if match_value and match_value_high:
            match_value = f"{match_value}|{match_value_high}"

    # Determine match_field from rule_type
    match_field = 'payee_name' if rule_type == 'payee' else 'amount'

    # Get the right action value based on action type
    if action_type == 'set_category':
        action_value = request.form.get('action_value_category', '')
    elif action_type == 'set_account':
        action_value = request.form.get('action_value_account', '')
    elif action_type == 'set_memo':
        action_value = request.form.get('action_value_text', '').strip()
    elif action_type == 'flag':
        action_value = 'true'
    else:
        action_value = ''

    if not match_value or not action_type:
        flash('Match value and action are required.', 'error')
        return redirect(url_for('main.settings', tab='rules'))

    if action_type != 'flag' and not action_value:
        flash('Action value is required.', 'error')
        return redirect(url_for('main.settings', tab='rules'))

    database.add_rule(str(uuid.uuid4()), rule_type, match_field, match_type, match_value, action_type, action_value, g.budget_id)
    flash('Rule added!', 'success')
    return redirect(url_for('main.settings', tab='rules'))


@bp.route('/settings/rules/<rule_id>/delete', methods=['POST'])
@login_required
def delete_rule(rule_id):
    database.delete_rule(rule_id)
    flash('Rule deleted.', 'success')
    return redirect(url_for('main.settings', tab='rules'))


# --- Categories ---

@bp.route('/categories')
@login_required
def categories():
    cats = database.get_categories(g.budget_id)
    groups = database.get_category_groups(g.budget_id)
    return render_template('categories.html', categories=cats, groups=groups)


@bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('main.categories'))

    group_id = request.form.get('group_id', '')
    category = Category(
        id=str(uuid.uuid4()),
        name=name,
        budgeted=0.00,
        activity=0.00,
        available=0.00,
        budget_id=g.budget_id,
        group_id=group_id
    )
    database.add_category(category)
    flash(f'Category "{name}" added!', 'success')
    return redirect(url_for('main.categories'))


@bp.route('/categories/<category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    cat = database.get_category_by_id(category_id)
    if not cat or cat.budget_id != g.budget_id:
        flash('Category not found.', 'error')
        return redirect(url_for('main.categories'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('main.edit_category', category_id=category_id))
        database.update_category(category_id, name, g.budget_id)
        flash(f'Category updated to "{name}".', 'success')
        return redirect(url_for('main.categories'))

    return render_template('edit_category.html', category=cat)


@bp.route('/categories/<category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    database.delete_category(category_id, g.budget_id)
    flash('Category deleted.', 'success')
    return redirect(url_for('main.categories'))


@bp.route('/categories/<category_id>/target', methods=['GET', 'POST'])
@login_required
def set_target(category_id):
    cat = database.get_category_by_id(category_id)
    if not cat or cat.budget_id != g.budget_id:
        flash('Category not found.', 'error')
        return redirect(url_for('main.budget'))

    if request.method == 'POST':
        target_type = request.form.get('target_type', '').strip()
        target_date = request.form.get('target_date', '').strip()
        try:
            target_amount = float(request.form.get('target_amount', 0))
        except ValueError:
            target_amount = 0.0

        if not target_type:
            target_amount = 0.0
            target_date = ''

        database.update_category_target(category_id, target_amount, target_type, target_date)
        flash(f'Target updated for "{cat.name}".', 'success')
        return redirect(url_for('main.budget'))

    return render_template('set_target.html', category=cat)


# --- Payees ---

@bp.route('/payees')
@login_required
def payees():
    all_payees = database.get_payees(g.budget_id)
    return render_template('payees.html', payees=all_payees)


@bp.route('/payees/add', methods=['POST'])
@login_required
def add_payee():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Payee name is required.', 'error')
        return redirect(url_for('main.payees'))

    payee = Payee(
        id=str(uuid.uuid4()),
        name=name,
        budget_id=g.budget_id
    )
    database.add_payee(payee)
    flash(f'Payee "{name}" added!', 'success')
    return redirect(url_for('main.payees'))


@bp.route('/payees/<payee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_payee(payee_id):
    payee = database.get_payee_by_id(payee_id)
    if not payee or payee.budget_id != g.budget_id:
        flash('Payee not found.', 'error')
        return redirect(url_for('main.payees'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Payee name is required.', 'error')
            return redirect(url_for('main.edit_payee', payee_id=payee_id))
        database.update_payee(payee_id, name, g.budget_id)
        flash(f'Payee updated to "{name}".', 'success')
        return redirect(url_for('main.payees'))

    return render_template('edit_payee.html', payee=payee)


@bp.route('/payees/<payee_id>/delete', methods=['POST'])
@login_required
def delete_payee(payee_id):
    database.delete_payee(payee_id, g.budget_id)
    flash('Payee deleted.', 'success')
    return redirect(url_for('main.payees'))


# --- Transactions ---

@bp.route('/transactions')
@login_required
def transactions():
    txns = database.get_transaction(g.budget_id)
    categories = database.get_categories(g.budget_id)
    accts = database.get_accounts(g.budget_id)
    payee_list = database.get_payees(g.budget_id)
    category_map = {c.id: c.name for c in categories}
    account_map = {a.id: a.name for a in accts}

    # Search & filter
    search = request.args.get('search', '').strip().lower()
    filter_category = request.args.get('category', '')
    filter_account = request.args.get('account', '')
    filter_payee = request.args.get('payee', '')
    filter_date_from = request.args.get('date_from', '')
    filter_date_to = request.args.get('date_to', '')
    filter_amount_min = request.args.get('amount_min', '')
    filter_amount_max = request.args.get('amount_max', '')

    if search:
        txns = [t for t in txns if search in t.payee.lower() or search in t.memo.lower()
                or search in category_map.get(t.category_id, '').lower()]
    if filter_category:
        txns = [t for t in txns if t.category_id == filter_category]
    if filter_account:
        txns = [t for t in txns if t.account_id == filter_account]
    if filter_payee:
        txns = [t for t in txns if t.payee.lower() == filter_payee.lower()]
    if filter_date_from:
        txns = [t for t in txns if t.date >= filter_date_from]
    if filter_date_to:
        txns = [t for t in txns if t.date <= filter_date_to]
    if filter_amount_min:
        try:
            amt_min = float(filter_amount_min)
            txns = [t for t in txns if t.amount >= amt_min]
        except ValueError:
            pass
    if filter_amount_max:
        try:
            amt_max = float(filter_amount_max)
            txns = [t for t in txns if t.amount <= amt_max]
        except ValueError:
            pass

    return render_template('transactions.html', transactions=txns, category_map=category_map,
                           account_map=account_map, categories=categories, accounts=accts,
                           payees=payee_list, search=request.args.get('search', ''),
                           filter_category=filter_category, filter_account=filter_account,
                           filter_payee=filter_payee, filter_date_from=filter_date_from,
                           filter_date_to=filter_date_to, filter_amount_min=filter_amount_min,
                           filter_amount_max=filter_amount_max)


@bp.route('/transactions/add', methods=['GET', 'POST'])
@login_required
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

        # Apply automation rules
        rule_actions = database.apply_rules(payee, amount, g.budget_id)
        if not category_id and rule_actions.get('category_id'):
            category_id = rule_actions['category_id']
        if not memo and rule_actions.get('memo'):
            memo = rule_actions['memo']
        if not account_id and rule_actions.get('account_id'):
            account_id = rule_actions['account_id']

        transaction = Transaction(
            id=str(uuid.uuid4()),
            date=txn_date,
            payee=payee,
            amount=amount,
            memo=memo,
            category_id=category_id,
            account_id=account_id,
            budget_id=g.budget_id
        )
        database.add_transaction(transaction)
        flash('Transaction added!', 'success')
        return redirect(url_for('main.transactions'))

    categories = database.get_categories(g.budget_id)
    accts = database.get_accounts(g.budget_id)
    defaults = database.get_all_budget_defaults(g.budget_id)
    return render_template('add_transaction.html',
                           categories=categories,
                           accounts=accts,
                           today=str(date.today()),
                           default_account_id=defaults.get('default_account_id', ''),
                           default_category_id=defaults.get('default_category_id', ''))


@bp.route('/transactions/<transaction_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    txn = database.get_transaction_by_id(transaction_id)
    if not txn or txn.budget_id != g.budget_id:
        flash('Transaction not found.', 'error')
        return redirect(url_for('main.transactions'))

    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
        except (ValueError, KeyError):
            flash('Please enter a valid amount.', 'error')
            return redirect(url_for('main.edit_transaction', transaction_id=transaction_id))

        payee = request.form.get('payee', '').strip()
        if not payee:
            flash('Payee is required.', 'error')
            return redirect(url_for('main.edit_transaction', transaction_id=transaction_id))

        memo = request.form.get('memo', '').strip()
        category_id = request.form.get('category_id', '')
        account_id = request.form.get('account_id', '')

        # Apply automation rules for empty fields
        rule_actions = database.apply_rules(payee, amount, g.budget_id)
        if not category_id and rule_actions.get('category_id'):
            category_id = rule_actions['category_id']
        if not memo and rule_actions.get('memo'):
            memo = rule_actions['memo']
        if not account_id and rule_actions.get('account_id'):
            account_id = rule_actions['account_id']

        txn.date = request.form.get('date', txn.date)
        txn.payee = payee
        txn.amount = amount
        txn.memo = memo
        txn.category_id = category_id
        txn.account_id = account_id

        database.update_transaction(txn)
        flash('Transaction updated!', 'success')
        return redirect(url_for('main.transactions'))

    categories = database.get_categories(g.budget_id)
    accts = database.get_accounts(g.budget_id)
    return render_template('edit_transaction.html', transaction=txn, categories=categories, accounts=accts)


@bp.route('/transactions/<transaction_id>/delete', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    database.delete_transaction(transaction_id, g.budget_id)
    flash('Transaction deleted.', 'success')
    return redirect(url_for('main.transactions'))


# --- Category Groups ---

@bp.route('/groups/add', methods=['POST'])
@login_required
def add_category_group():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Group name is required.', 'error')
        return redirect(url_for('main.categories'))

    groups = database.get_category_groups(g.budget_id)
    position = len(groups)

    group = CategoryGroup(
        id=str(uuid.uuid4()),
        name=name,
        position=position,
        budget_id=g.budget_id
    )
    database.add_category_group(group)
    flash(f'Group "{name}" added!', 'success')
    return redirect(url_for('main.categories'))


@bp.route('/groups/<group_id>/delete', methods=['POST'])
@login_required
def delete_category_group(group_id):
    database.delete_category_group(group_id, g.budget_id)
    flash('Group deleted. Categories moved to ungrouped.', 'success')
    return redirect(url_for('main.categories'))


@bp.route('/categories/<category_id>/set-group', methods=['POST'])
@login_required
def set_category_group(category_id):
    group_id = request.form.get('group_id', '')
    database.set_category_group(category_id, group_id, g.budget_id)
    flash('Category group updated.', 'success')
    return redirect(url_for('main.categories'))


# --- Recurring Transactions ---

def _advance_next_date(next_date_str, frequency):
    """Calculate the next occurrence date after the given date."""
    d = date.fromisoformat(next_date_str)
    if frequency == 'weekly':
        d += timedelta(weeks=1)
    elif frequency == 'biweekly':
        d += timedelta(weeks=2)
    elif frequency == 'monthly':
        month = d.month + 1
        year = d.year
        if month > 12:
            month = 1
            year += 1
        day = min(d.day, 28)  # Safe day for all months
        d = date(year, month, day)
    elif frequency == 'yearly':
        d = date(d.year + 1, d.month, min(d.day, 28))
    return d.isoformat()


def _process_recurring(budget_id):
    """Create transactions for any recurring transactions that are due."""
    today_str = str(date.today())
    recurring = database.get_recurring_transactions(budget_id)
    for rt in recurring:
        if not rt.is_active:
            continue
        while rt.next_date <= today_str:
            txn = Transaction(
                id=str(uuid.uuid4()),
                date=rt.next_date,
                payee=rt.payee,
                amount=rt.amount,
                memo=rt.memo,
                category_id=rt.category_id,
                account_id=rt.account_id,
                budget_id=budget_id
            )
            database.add_transaction(txn)
            rt.next_date = _advance_next_date(rt.next_date, rt.frequency)
            database.update_recurring_next_date(rt.id, rt.next_date)


@bp.route('/recurring')
@login_required
def recurring_transactions():
    recurring = database.get_recurring_transactions(g.budget_id)
    categories = database.get_categories(g.budget_id)
    accts = database.get_accounts(g.budget_id)
    category_map = {c.id: c.name for c in categories}
    account_map = {a.id: a.name for a in accts}
    return render_template('recurring.html', recurring=recurring, categories=categories,
                           accounts=accts, category_map=category_map, account_map=account_map)


@bp.route('/recurring/add', methods=['POST'])
@login_required
def add_recurring():
    payee = request.form.get('payee', '').strip()
    frequency = request.form.get('frequency', '').strip()
    next_date = request.form.get('next_date', '').strip()

    if not payee or not frequency or not next_date:
        flash('Payee, frequency, and start date are required.', 'error')
        return redirect(url_for('main.recurring_transactions'))

    try:
        amount = float(request.form['amount'])
    except (ValueError, KeyError):
        flash('Please enter a valid amount.', 'error')
        return redirect(url_for('main.recurring_transactions'))

    rt = RecurringTransaction(
        id=str(uuid.uuid4()),
        payee=payee,
        amount=amount,
        memo=request.form.get('memo', '').strip(),
        category_id=request.form.get('category_id', ''),
        account_id=request.form.get('account_id', ''),
        frequency=frequency,
        next_date=next_date,
        budget_id=g.budget_id
    )
    database.add_recurring_transaction(rt)
    flash(f'Recurring transaction "{payee}" added!', 'success')
    return redirect(url_for('main.recurring_transactions'))


@bp.route('/recurring/<rt_id>/delete', methods=['POST'])
@login_required
def delete_recurring(rt_id):
    database.delete_recurring_transaction(rt_id, g.budget_id)
    flash('Recurring transaction deleted.', 'success')
    return redirect(url_for('main.recurring_transactions'))


@bp.route('/recurring/<rt_id>/toggle', methods=['POST'])
@login_required
def toggle_recurring(rt_id):
    is_active = int(request.form.get('is_active', 0))
    database.toggle_recurring_transaction(rt_id, is_active, g.budget_id)
    flash('Recurring transaction updated.', 'success')
    return redirect(url_for('main.recurring_transactions'))


# --- Reports ---

@bp.route('/reports')
@login_required
def reports():
    categories = database.get_categories(g.budget_id)
    all_transactions = database.get_transaction(g.budget_id)
    accts = database.get_accounts(g.budget_id)
    category_map = {c.id: c.name for c in categories}

    # Spending by category (expenses only, current month by default)
    month_str = request.args.get('month', '')
    today = date.today()
    try:
        year, month = int(month_str[:4]), int(month_str[5:7])
    except (ValueError, IndexError):
        year, month = today.year, today.month
    month_prefix = f"{year:04d}-{month:02d}"
    month_label = f"{month_name[month]} {year}"

    month_txns = [t for t in all_transactions if t.date.startswith(month_prefix)]

    # Spending by category
    spending_by_cat = defaultdict(float)
    income_total = 0.0
    expense_total = 0.0
    for t in month_txns:
        if t.category_id == 'income' or t.amount > 0:
            income_total += abs(t.amount)
        else:
            cat_name = category_map.get(t.category_id, 'Uncategorized')
            spending_by_cat[cat_name] += abs(t.amount)
            expense_total += abs(t.amount)

    # Sort by amount descending
    spending_by_cat = dict(sorted(spending_by_cat.items(), key=lambda x: x[1], reverse=True))

    # Spending over time (last 6 months)
    monthly_data = {}
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        mp = f"{y:04d}-{m:02d}"
        ml = f"{month_name[m][:3]} {y}"
        m_income = 0.0
        m_expense = 0.0
        for t in all_transactions:
            if t.date.startswith(mp):
                if t.category_id == 'income' or t.amount > 0:
                    m_income += abs(t.amount)
                else:
                    m_expense += abs(t.amount)
        monthly_data[ml] = {'income': m_income, 'expense': m_expense}

    return render_template('reports.html',
                           spending_by_cat=spending_by_cat,
                           income_total=income_total,
                           expense_total=expense_total,
                           monthly_data=monthly_data,
                           month_label=month_label,
                           month_prefix=month_prefix)


# --- Plaid Integration ---

@bp.route('/accounts/<account_id>/connect')
@login_required
def plaid_connect(account_id):
    account = database.get_account(account_id)
    if not account or account.budget_id != g.budget_id:
        flash('Account not found.', 'error')
        return redirect(url_for('main.settings', tab='accounts'))
    return render_template('plaid_connect.html', account=account)


@bp.route('/plaid/create_link_token', methods=['POST'])
@login_required
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
        user=LinkTokenCreateRequestUser(client_user_id=g.user_id or "budgetry-user")
    )
    response = client.link_token_create(plaid_request)
    return jsonify({"link_token": response.link_token})


@bp.route('/plaid/exchange_token', methods=['POST'])
@login_required
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
@login_required
def plaid_sync(account_id):
    from app.plaid_client import get_plaid_client
    from plaid.model.transactions_sync_request import TransactionsSyncRequest
    from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest

    # Verify account belongs to active budget
    account = database.get_account(account_id)
    if not account or account.budget_id != g.budget_id:
        flash('Account not found.', 'error')
        return redirect(url_for('main.settings', tab='accounts'))

    plaid_item = database.get_plaid_item_by_account(account_id)
    if not plaid_item:
        flash('No bank connection found for this account.', 'error')
        return redirect(url_for('main.settings', tab='accounts'))

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

            txn_payee = txn.merchant_name or txn.name or "Unknown"
            txn_amount = -txn.amount  # Plaid: positive = debit, we negate
            txn_memo = txn.name or ""

            # Apply automation rules to synced transactions
            rule_actions = database.apply_rules(txn_payee, txn_amount, g.budget_id)
            txn_category = rule_actions.get('category_id', '')
            if rule_actions.get('memo'):
                txn_memo = rule_actions['memo']
            txn_account = rule_actions.get('account_id', account_id)

            transaction = Transaction(
                id=str(uuid.uuid4()),
                date=str(txn.date),
                payee=txn_payee,
                amount=txn_amount,
                memo=txn_memo,
                category_id=txn_category,
                account_id=txn_account,
                plaid_transaction_id=plaid_txn_id,
                budget_id=g.budget_id
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
    return redirect(url_for('main.settings', tab='accounts'))


# --- Profile ---

@bp.route('/profile')
@login_required
def profile():
    user = database.get_user_by_id(g.user_id)
    budgets = database.get_budgets_for_user(g.user_id)
    budget_roles = []
    for b in budgets:
        role = database.get_user_role_in_budget(g.user_id, b.id)
        budget_roles.append({"budget": b, "role": role})
    is_local_user = bool(user.password_hash) if user else False
    return render_template('profile.html', user=user, budget_roles=budget_roles,
                           auth0_enabled=is_auth0_enabled(), is_local_user=is_local_user)


@bp.route('/profile/update-name', methods=['POST'])
@login_required
def update_display_name():
    username = request.form.get('username', '').strip()
    if not username:
        flash('Display name cannot be empty.', 'error')
        return redirect(url_for('main.profile'))
    database.update_username(g.user_id, username)
    flash('Display name updated!', 'success')
    return redirect(url_for('main.profile'))


@bp.route('/profile/reset-password', methods=['POST'])
@login_required
def reset_password():
    user = database.get_user_by_id(g.user_id)
    if not user or not user.email:
        flash('No email address on file.', 'error')
        return redirect(url_for('main.profile'))
    from app.auth0_api import request_password_reset
    success = request_password_reset(user.email)
    if success:
        flash('Password reset email sent! Check your inbox.', 'success')
    else:
        flash('Could not send reset email. Try again later.', 'error')
    return redirect(url_for('main.profile'))


@bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    from werkzeug.security import generate_password_hash, check_password_hash
    user = database.get_user_by_id(g.user_id)
    if not user or not user.password_hash:
        flash('Password change not available for OAuth accounts.', 'error')
        return redirect(url_for('main.profile'))

    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not check_password_hash(user.password_hash, current_pw):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('main.profile'))

    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('main.profile'))

    if len(new_pw) < 8:
        flash('New password must be at least 8 characters.', 'error')
        return redirect(url_for('main.profile'))

    database.update_password_hash(user.id, generate_password_hash(new_pw))
    flash('Password updated successfully!', 'success')
    return redirect(url_for('main.profile'))


@bp.route('/profile/setup-mfa')
@login_required
def setup_mfa():
    """Show TOTP setup page for local users, or redirect to Auth0 for OAuth users."""
    user = database.get_user_by_id(g.user_id)
    if not user:
        return redirect(url_for('main.login'))

    # Auth0 users use Auth0's MFA enrollment
    if user.auth0_id and is_auth0_enabled():
        return oauth.auth0.authorize_redirect(
            redirect_uri=url_for('main.mfa_auth0_callback', _external=True),
            acr_values='http://schemas.openid.net/psp/mfa'
        )

    # Local users get TOTP setup
    import pyotp
    secret = pyotp.random_base32()
    session['totp_setup_secret'] = secret
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=user.username, issuer_name="Budgetry")
    return render_template('setup_mfa.html', secret=secret, provisioning_uri=provisioning_uri)


@bp.route('/profile/verify-mfa', methods=['POST'])
@login_required
def verify_mfa():
    """Verify TOTP code during MFA setup and enable it."""
    import pyotp
    secret = session.get('totp_setup_secret')
    code = request.form.get('code', '').strip()

    if not secret:
        flash('MFA setup expired. Please try again.', 'error')
        return redirect(url_for('main.profile'))

    totp = pyotp.TOTP(secret)
    if totp.verify(code):
        database.update_totp_secret(g.user_id, secret)
        database.update_user_mfa_status(g.user_id, 1)
        session.pop('totp_setup_secret', None)
        flash('MFA has been enabled on your account!', 'success')
    else:
        flash('Invalid verification code. Please try again.', 'error')
        return redirect(url_for('main.setup_mfa'))

    return redirect(url_for('main.profile'))


@bp.route('/profile/disable-mfa', methods=['POST'])
@login_required
def disable_mfa():
    """Disable TOTP MFA for local users."""
    user = database.get_user_by_id(g.user_id)
    if user and user.totp_secret:
        database.update_totp_secret(g.user_id, "")
        database.update_user_mfa_status(g.user_id, 0)
        flash('MFA has been disabled.', 'success')
    return redirect(url_for('main.profile'))


@bp.route('/auth/mfa-callback')
def mfa_auth0_callback():
    """Handle return from Auth0 MFA enrollment."""
    if not is_auth0_enabled():
        return redirect(url_for('main.profile'))
    token = oauth.auth0.authorize_access_token()
    user_id = session.get('user_id')
    if user_id:
        database.update_user_mfa_status(user_id, 1)
    flash('MFA has been enabled on your account!', 'success')
    return redirect(url_for('main.profile'))


# --- Admin ---

@bp.route('/admin/users')
@admin_required
def admin_users():
    users = database.get_all_users()
    return render_template('admin_users.html', users=users)


@bp.route('/admin/users/<user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_user_active(user_id):
    user = database.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('main.admin_users'))
    if user.id == g.user_id:
        flash('You cannot deactivate yourself.', 'error')
        return redirect(url_for('main.admin_users'))
    new_status = 0 if user.is_active else 1
    database.set_user_active(user_id, new_status)
    label = "activated" if new_status else "deactivated"
    flash(f'User {user.username} has been {label}.', 'success')
    return redirect(url_for('main.admin_users'))


@bp.route('/admin/users/<user_id>/refresh-mfa', methods=['POST'])
@admin_required
def refresh_user_mfa(user_id):
    """Fetch fresh MFA status from Auth0 for a specific user."""
    user = database.get_user_by_id(user_id)
    if user and user.auth0_id:
        from app.auth0_api import get_mfa_status
        mfa = get_mfa_status(user.auth0_id)
        database.update_user_mfa_status(user_id, 1 if mfa else 0)
        flash(f'MFA status refreshed for {user.username}.', 'success')
    return redirect(url_for('main.admin_users'))


@bp.route('/admin/users/<user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_user_admin(user_id):
    """Promote or demote a user's admin status."""
    user = database.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('main.admin_users'))
    if user.id == g.user_id:
        flash('You cannot change your own admin status.', 'error')
        return redirect(url_for('main.admin_users'))
    new_status = 0 if user.is_admin else 1
    connection = database.get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET is_admin = ? WHERE id = ?", (new_status, user_id))
    connection.commit()
    connection.close()
    label = "promoted to admin" if new_status else "demoted from admin"
    flash(f'User {user.username} has been {label}.', 'success')
    return redirect(url_for('main.admin_users'))


@bp.route('/admin/users/<user_id>/reset-password', methods=['POST'])
@admin_required
def admin_reset_password(user_id):
    """Admin force-resets a local user's password to a temporary one."""
    from werkzeug.security import generate_password_hash
    user = database.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('main.admin_users'))
    if not user.password_hash:
        flash('Cannot reset password for OAuth-only users.', 'error')
        return redirect(url_for('main.admin_users'))
    temp_password = str(uuid.uuid4())[:12]
    database.update_password_hash(user_id, generate_password_hash(temp_password))
    flash(f'Password reset for {user.username}. Temporary password: {temp_password}', 'success')
    return redirect(url_for('main.admin_users'))
