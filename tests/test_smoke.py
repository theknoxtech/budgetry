"""Smoke tests to verify the app starts and basic routes work."""


def test_app_creates(app):
    assert app is not None
    assert app.config["TESTING"] is True


def test_login_page_returns_200(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Budgetry" in resp.data


def test_unauthenticated_redirects_to_login(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_register_page_returns_200(client):
    resp = client.get("/auth/register")
    assert resp.status_code == 200


def test_register_and_login(client):
    # Register
    resp = client.post("/auth/register", data={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
    }, follow_redirects=True)
    assert resp.status_code == 200

    # Login
    resp = client.post("/auth/local-login", data={
        "username": "testuser",
        "password": "TestPass123!",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Budget" in resp.data


def test_version_endpoint(client):
    resp = client.get("/api/version")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "version" in data
    assert "latest" in data
