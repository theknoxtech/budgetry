import os
from flask import Flask
from dotenv import load_dotenv
from app import database

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-budgetry-key')
    app.config['PLAID_CLIENT_ID'] = os.environ.get('PLAID_CLIENT_ID', '')
    app.config['PLAID_SECRET'] = os.environ.get('PLAID_SECRET', '')
    app.config['PLAID_ENV'] = os.environ.get('PLAID_ENV', 'sandbox')

    database.init_db()

    from app.routes import bp
    app.register_blueprint(bp)

    return app
