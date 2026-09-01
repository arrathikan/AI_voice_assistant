from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
import requests as http_requests
from database import users_collection
from models import UserRegister
from auth import hash_password
from keycloak_config import create_keycloak_user, TOKEN_URL, USER_CLIENT_ID
from dependencies import verify_token

router = APIRouter()


@router.post("/register")
def register(user: UserRegister):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = hash_password(user.password)
    users_collection.insert_one({
        "username": user.username,
        "email": user.email,
        "password": hashed
    })

    try:
        create_keycloak_user(user.username, user.email, user.password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keycloak user creation failed: {str(e)}")

    return {"message": "User registered successfully"}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    payload = {
        "client_id": USER_CLIENT_ID,
        "username": form_data.username,
        "password": form_data.password,
        "grant_type": "password"
    }
    response = http_requests.post(TOKEN_URL, data=payload)
    if response.status_code != 200:
        print("Keycloak token error:", response.text)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = response.json()
    return {
        "access_token": token_data.get("access_token"),
        "token_type": "bearer"
    }


@router.get("/protected")
def protected_data(token: str = Depends(verify_token)):
    return {
        "message": "This is protected data",
        "token": token
    }


@router.post("/forgot")
def forgot_password(username: str):
    """Trigger a password reset email for the user."""
    from keycloak_config import get_user_id_by_username, send_reset_password_email
    
    user_id = get_user_id_by_username(username)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        send_reset_password_email(user_id)
        return {"message": "Password reset email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reset email: {str(e)}")