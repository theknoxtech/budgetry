import requests
import time
from flask import current_app

# Module-level token cache
_token_cache = {"token": None, "expires_at": 0}


def _get_mgmt_token():
    """Get a Management API token using client credentials, cached."""
    if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    domain = current_app.config["AUTH0_DOMAIN"]
    resp = requests.post(f"https://{domain}/oauth/token", json={
        "client_id": current_app.config["AUTH0_CLIENT_ID"],
        "client_secret": current_app.config["AUTH0_CLIENT_SECRET"],
        "audience": f"https://{domain}/api/v2/",
        "grant_type": "client_credentials"
    }, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 86400)
    return _token_cache["token"]


def request_password_reset(email):
    """Trigger Auth0 password reset email. Public endpoint, no token needed."""
    domain = current_app.config["AUTH0_DOMAIN"]
    resp = requests.post(f"https://{domain}/dbconnections/change_password", json={
        "client_id": current_app.config["AUTH0_CLIENT_ID"],
        "email": email,
        "connection": "Username-Password-Authentication"
    }, timeout=10)
    return resp.status_code == 200


def get_mfa_status(auth0_id):
    """Check if user has MFA enrolled via Management API."""
    domain = current_app.config["AUTH0_DOMAIN"]
    try:
        token = _get_mgmt_token()
        resp = requests.get(
            f"https://{domain}/api/v2/users/{auth0_id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"fields": "multifactor", "include_fields": "true"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return len(data.get("multifactor", [])) > 0
    except Exception:
        pass
    return False
