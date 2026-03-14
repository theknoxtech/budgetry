from flask import Flask
from app import database


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-budgetry-key'

    database.init_db()

    from app.routes import bp
    app.register_blueprint(bp)

    return app
