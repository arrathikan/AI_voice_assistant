import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

REALM_NAME = os.getenv("KEYCLOAK_REALM", "arrathikan")
ADMIN_REALM = "master"
USER_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT", "testclint")
SERVER_URL = os.getenv("KEYCLOAK_SERVER", "http://localhost:8080/")
TOKEN_URL = f"{SERVER_URL}realms/{REALM_NAME}/protocol/openid-connect/token"
ADMIN_TOKEN_URL = f"{SERVER_URL}realms/{ADMIN_REALM}/protocol/openid-connect/token"
USERS_URL = f"{SERVER_URL}admin/realms/{REALM_NAME}/users"
REALMS_URL = f"{SERVER_URL}admin/realms"


def get_admin_token():
    """Get an admin access token from the master realm."""
    resp = requests.post(ADMIN_TOKEN_URL, data={
        "client_id": "admin-cli",
        "username": os.getenv("KEYCLOAK_ADMIN", "admin"),
        "password": os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin"),
        "grant_type": "password"
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_keycloak_user(username: str, email: str, password: str):
    """Create a user directly in the REALM_NAME via REST API."""
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Create user
    user_payload = {
        "username": username,
        "email": email,
        "firstName": username,
        "lastName": "User",
        "enabled": True,
        "emailVerified": True
    }
    resp = requests.post(USERS_URL, json=user_payload, headers=headers)
    if resp.status_code not in (201, 409):
        resp.raise_for_status()

    # Get user ID
    search_resp = requests.get(f"{USERS_URL}?username={username}&exact=true", headers=headers)
    search_resp.raise_for_status()
    users = search_resp.json()
    if not users:
        raise Exception(f"User '{username}' not found after creation")
    user_id = users[0]["id"]

    # Set password
    pwd_resp = requests.put(
        f"{USERS_URL}/{user_id}/reset-password",
        json={"type": "password", "value": password, "temporary": False},
        headers=headers
    )
    pwd_resp.raise_for_status()

    # Clear any required actions (e.g., VERIFY_EMAIL) so login works immediately
    clear_resp = requests.put(
        f"{USERS_URL}/{user_id}",
        json={"requiredActions": [], "emailVerified": True, "enabled": True},
        headers=headers
    )
    clear_resp.raise_for_status()

    return user_id


def init_keycloak():
    """Ensure the VerdeAI realm and client exist with SSL disabled for local dev."""
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.get(REALMS_URL, headers=headers)
    resp.raise_for_status()
    existing = [r["realm"] for r in resp.json()]
    if REALM_NAME not in existing:
        print(f"Realm '{REALM_NAME}' does not exist. Creating it...")
        requests.post(
            REALMS_URL,
            json={"realm": REALM_NAME, "enabled": True, "sslRequired": "NONE"},
            headers=headers
        ).raise_for_status()
    else:
        # Ensure sslRequired is NONE for local development
        requests.put(
            f"{REALMS_URL}/{REALM_NAME}",
            json={"sslRequired": "NONE"},
            headers=headers
        ).raise_for_status()
        print(f"Realm '{REALM_NAME}' already exists.")

    # Ensure client exists
    clients_url = f"{SERVER_URL}admin/realms/{REALM_NAME}/clients"
    clients_resp = requests.get(clients_url, headers=headers)
    clients_resp.raise_for_status()
    existing_clients = [c.get("clientId") for c in clients_resp.json()]
    if USER_CLIENT_ID not in existing_clients:
        print(f"Client '{USER_CLIENT_ID}' does not exist. Creating it...")
        client_payload = {
            "clientId": USER_CLIENT_ID,
            "enabled": True,
            "publicClient": True,
            "directAccessGrantsEnabled": True,
            "standardFlowEnabled": True
        }
        requests.post(clients_url, json=client_payload, headers=headers).raise_for_status()
        print(f"✅ Client '{USER_CLIENT_ID}' created successfully.")
    else:
        print(f"Client '{USER_CLIENT_ID}' already exists.")


def get_user_id_by_username(username: str):
    """Retrieve the user ID from Keycloak given a username."""
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    search_resp = requests.get(f"{USERS_URL}?username={username}&exact=true", headers=headers)
    search_resp.raise_for_status()
    users = search_resp.json()
    if not users:
        return None
    return users[0]["id"]


def send_reset_password_email(user_id: str):
    """Trigger a reset password email for the given user ID."""
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{USERS_URL}/{user_id}/execute-actions-email"
    # Trigger the update password action via email
    resp = requests.put(url, json=["UPDATE_PASSWORD"], headers=headers)
    if resp.status_code != 204:
        resp.raise_for_status()
    return True