import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.user_routes import router
from routes.history_routes import router as history_router
from keycloak_config import init_keycloak
from dependencies import init_jwks

app = FastAPI(title="VerdeAI Authentication API")

# Allow the Streamlit frontend (running on a different port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            init_keycloak()
            init_jwks()
            print("✅ Keycloak initialized successfully.")
            return
        except Exception as e:
            print(f"⏳ Keycloak not ready yet (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(3)
    print("❌ Failed to connect to Keycloak after all retries. Check Keycloak is running.")

app.include_router(router)
app.include_router(history_router)


@app.get("/")
def home():
    return {"message": "Authentication API running"}