import os
import secrets
from flask import Flask, session
from dotenv import load_dotenv
from app import database

load_dotenv()


def _get_secret_key():
    """Get SECRET_KEY from env, or auto-generate and persist one."""
    key = os.environ.get('SECRET_KEY', '')
    if key:
        return key
    # Auto-generate and save to instance/.secret_key
    key_file = os.path.join('instance', '.secret_key')
    os.makedirs('instance', exist_ok=True)
    if os.path.exists(key_file):
        with open(key_file, 'r') as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(key_file, 'w') as f:
        f.write(key)
    return key


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = _get_secret_key()
    app.config['PLAID_CLIENT_ID'] = os.environ.get('PLAID_CLIENT_ID', '')
    app.config['PLAID_SECRET'] = os.environ.get('PLAID_SECRET', '')
    app.config['PLAID_ENV'] = os.environ.get('PLAID_ENV', 'sandbox')
    app.config['AUTH0_DOMAIN'] = os.environ.get('AUTH0_DOMAIN', '')
    app.config['AUTH0_CLIENT_ID'] = os.environ.get('AUTH0_CLIENT_ID', '')
    app.config['AUTH0_CLIENT_SECRET'] = os.environ.get('AUTH0_CLIENT_SECRET', '')

    database.init_db()

    from app.auth import init_auth
    init_auth(app)  # Will skip Auth0 registration if env vars not set

    from app.routes import bp
    app.register_blueprint(bp)

    @app.context_processor
    def inject_sidebar():
        if 'user_id' not in session:
            return dict(sidebar_accounts=[], current_user=None, user_budgets=[], active_budget=None)

        budget_id = session.get('active_budget_id', '')
        user_id = session.get('user_id', '')

        return dict(
            sidebar_accounts=database.get_accounts(budget_id),
            current_user=database.get_user_by_id(user_id),
            user_budgets=database.get_budgets_for_user(user_id),
            active_budget=database.get_budget_by_id(budget_id),
        )

    return app
