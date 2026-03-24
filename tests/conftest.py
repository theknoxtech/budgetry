import pytest


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Create a test Flask app with a temporary database."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("app.database.DB_PATH", db_path)
    monkeypatch.setattr("app.database._instance_dir", str(tmp_path))
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    from app import create_app
    from app import database
    database.DB_PATH = db_path
    database.init_db()

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
