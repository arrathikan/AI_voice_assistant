# AI Voice Assistant (with sign-in and per-user history)

An AI voice assistant (Streamlit + OpenRouter) that now sits behind a
sign-in screen backed by the `verify/` auth service (FastAPI + Keycloak +
MongoDB). Each person has their own account and their own saved
conversation history, which is loaded automatically when they sign in.

## How it fits together

- `verify/` — FastAPI service. Handles register/login against Keycloak,
  and now also exposes `GET/POST/DELETE /history`, which reads/writes a
  MongoDB document keyed by the signed-in person's username (identified
  from their JWT, via `get_current_username` in `verify/dependencies.py`).
- `app.py` — Streamlit app. Shows a Sign In / Create Account screen first.
  Once signed in, it stores the JWT in `st.session_state`, loads that
  person's history from `/history`, and after every voice exchange saves
  the new turn back to `/history` so it's there next time they log in.

## Running it

1. **Start Keycloak + MongoDB:**
   ```bash
   cd verify
   docker-compose up -d
   ```

2. **Start the auth/history API:**
   ```bash
   cd verify
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
   This runs on `http://localhost:8000` by default.

3. **Start the Streamlit agent** (in a separate terminal, from the project root):
   ```bash
   pip install -r requirement.txt
   streamlit run app.py
   ```

4. Open the Streamlit app, create an account on the **Create Account**
   tab, then sign in. You'll only see the voice assistant after signing in.

## Configuration

- `.streamlit/secrets.toml` — needs `OPENROUTER_API_KEY`, and optionally
  `AUTH_API_URL` (defaults to `http://localhost:8000`) if the auth API
  runs somewhere other than localhost.
- `verify/.env` — Mongo connection, DB name, and Keycloak settings (already present).

## Notes / things worth tightening later

- CORS on the FastAPI app is currently wide open (`allow_origins=["*"]`)
  to make local dev easy — restrict this to your Streamlit URL before
  deploying anywhere public.
- The JWT is only kept in Streamlit's `st.session_state`, so it does not
  survive a page refresh — the person will need to sign in again after a
  refresh. That's normal for Streamlit; if you want persistent sessions
  across refreshes you'd need to store the token in a browser cookie via
  a components library.
