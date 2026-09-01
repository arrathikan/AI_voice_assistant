from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import requests
import os
from dotenv import load_dotenv

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "VerdeAI")
KEYCLOAK_SERVER = os.getenv("KEYCLOAK_SERVER", "http://localhost:8080/")

JWKS_URL = f"{KEYCLOAK_SERVER}realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"

jwks = None

def init_jwks():
    global jwks
    try:
        response = requests.get(JWKS_URL)
        response.raise_for_status()
        jwks = response.json()
    except Exception as e:
        print(f"Failed to fetch JWKS: {e}")
        jwks = None
        raise e

def get_jwks():
    global jwks
    if jwks is None:
        init_jwks()
    return jwks


def decode_token(token: str = Depends(oauth2_scheme)) -> dict:
    """Verify the token's signature and return its decoded claims."""
    keys = get_jwks()
    if not keys:
        raise HTTPException(status_code=500, detail="Authentication server unavailable")
    try:
        payload = jwt.decode(token, keys, algorithms=["RS256"], options={"verify_aud": False})
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_token(token: str = Depends(oauth2_scheme)):
    decode_token(token)
    return token


def get_current_username(payload: dict = Depends(decode_token)) -> str:
    """Identify which particular signed-in person is making the request."""
    username = payload.get("preferred_username")
    if not username:
        raise HTTPException(status_code=401, detail="Token missing username claim")
    return username