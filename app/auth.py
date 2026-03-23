from functools import wraps
from flask import session, redirect, url_for
from authlib.integrations.flask_client import OAuth

oauth = OAuth()


def init_auth(app):
    """Initialize Auth0 OAuth client with the Flask app."""
    oauth.init_app(app)
    oauth.register(
        "auth0",
        client_id=app.config["AUTH0_CLIENT_ID"],
        client_secret=app.config["AUTH0_CLIENT_SECRET"],
        client_kwargs={"scope": "openid profile email"},
        server_metadata_url=f'https://{app.config["AUTH0_DOMAIN"]}/.well-known/openid-configuration'
    )


def login_required(f):
    """Decorator that redirects to login if user is not authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator that checks user is authenticated and is_admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        from app import database
        from flask import flash
        user = database.get_user_by_id(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.budget'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id():
    """Get the current logged-in user's ID from the session."""
    return session.get('user_id')


def get_active_budget_id():
    """Get the active budget ID from the session."""
    return session.get('active_budget_id', '')
