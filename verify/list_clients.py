import json, os
from keycloak import KeycloakAdmin
admin = KeycloakAdmin(
    server_url="http://127.0.0.1:8080/",
    username="admin", password="admin",
    realm_name="master", client_id="admin-cli", verify=True
)
admin.realm_name = "VerdeAI"
clients = admin.get_clients()
print(json.dumps([c for c in clients if c.get("clientId") == "fastapi-client"], indent=2))
