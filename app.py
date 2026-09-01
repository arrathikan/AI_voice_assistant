import streamlit as st
import requests
import base64


# ============================================================
# CONFIG
# ============================================================

OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")

# Base URL of the FastAPI auth/history service in verify/ (run separately,
# e.g. `uvicorn main:app --reload` from inside the verify/ folder).
AUTH_API_URL = st.secrets.get("AUTH_API_URL", "http://localhost:8000")

if not OPENROUTER_API_KEY:
    st.error(
        "OPENROUTER_API_KEY is not set in .streamlit/secrets.toml"
    )
    st.stop()


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Voice Assistant",
    page_icon="🎙️",
    layout="centered"
)


# ============================================================
# SESSION STATE
# ============================================================

if "token" not in st.session_state:
    st.session_state.token = None

if "username" not in st.session_state:
    st.session_state.username = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False


# ============================================================
# AUTH API HELPERS (talks to the FastAPI service in verify/)
# ============================================================

def register_account(username, email, password):
    return requests.post(
        f"{AUTH_API_URL}/register",
        json={"username": username, "email": email, "password": password},
        timeout=30,
    )


def login_account(username, password):
    # /login expects OAuth2PasswordRequestForm -> form-encoded, not JSON
    return requests.post(
        f"{AUTH_API_URL}/login",
        data={"username": username, "password": password},
        timeout=30,
    )


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def fetch_remote_history():
    """Load this particular signed-in person's saved conversation."""
    try:
        response = requests.get(
            f"{AUTH_API_URL}/history", headers=auth_headers(), timeout=30
        )
        if response.status_code == 200:
            return response.json().get("messages", [])
    except requests.exceptions.RequestException:
        pass
    return []


def save_remote_history(new_messages):
    """Append just the newly created messages to this person's history."""
    try:
        requests.post(
            f"{AUTH_API_URL}/history",
            json={"messages": new_messages},
            headers=auth_headers(),
            timeout=30,
        )
    except requests.exceptions.RequestException:
        pass


def clear_remote_history():
    try:
        requests.delete(
            f"{AUTH_API_URL}/history", headers=auth_headers(), timeout=30
        )
    except requests.exceptions.RequestException:
        pass


def logout():
    st.session_state.token = None
    st.session_state.username = None
    st.session_state.messages = []
    st.session_state.history_loaded = False


# ============================================================
# SIGN IN / REGISTER SCREEN
# ============================================================

def render_login_screen():
    st.title("🎙️ AI Voice Assistant")
    st.write("Sign in to talk to your assistant. Your conversation history is saved to your own account.")

    login_tab, register_tab = st.tabs(["Sign In", "Create Account"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")

        if submitted:
            if not username or not password:
                st.warning("Please enter both a username and password.")
            else:
                try:
                    response = login_account(username, password)
                except requests.exceptions.RequestException as e:
                    st.error(f"Could not reach the authentication server: {e}")
                else:
                    if response.status_code == 200:
                        st.session_state.token = response.json()["access_token"]
                        st.session_state.username = username
                        st.session_state.history_loaded = False
                        st.success("Signed in!")
                        st.rerun()
                    else:
                        detail = response.json().get("detail", "Invalid credentials")
                        st.error(detail)

    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Choose a password", type="password")
            registered = st.form_submit_button("Create Account")

        if registered:
            if not new_username or not new_email or not new_password:
                st.warning("Please fill in every field.")
            else:
                try:
                    response = register_account(new_username, new_email, new_password)
                except requests.exceptions.RequestException as e:
                    st.error(f"Could not reach the authentication server: {e}")
                else:
                    if response.status_code == 200:
                        st.success("Account created! Switch to Sign In to log in.")
                    else:
                        detail = response.json().get("detail", "Registration failed")
                        st.error(detail)


# ============================================================
# GATE: must be signed in to reach the agent
# ============================================================

if not st.session_state.token:
    render_login_screen()
    st.stop()

# Load this particular person's own saved history exactly once after sign-in
if not st.session_state.history_loaded:
    st.session_state.messages = fetch_remote_history()
    st.session_state.history_loaded = True


# ============================================================
# AGENT FUNCTIONS
# ============================================================

def generate_ai_response(user_text):
    """
    Send the user's transcribed voice message
    + conversation history to OpenRouter, and persist
    the new turn to this person's own history.
    """

    user_message = {"role": "user", "content": user_text}
    st.session_state.messages.append(user_message)

    # Keep only the latest 20 messages sent to the model
    messages_to_send = st.session_state.messages[-20:]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-5",
        "messages": messages_to_send
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code == 200:

        result = response.json()

        answer = result["choices"][0]["message"]["content"]

        assistant_message = {"role": "assistant", "content": answer}
        st.session_state.messages.append(assistant_message)

        # Persist just this turn to the signed-in user's own history
        save_remote_history([user_message, assistant_message])

        return answer

    else:

        raise Exception(
            f"OpenRouter Error {response.status_code}: "
            f"{response.text}"
        )


def transcribe_audio(audio_bytes):
    """
    Convert recorded audio into text using
    OpenRouter Whisper.
    """

    audio_base64 = base64.b64encode(
        audio_bytes
    ).decode("utf-8")

    transcription_headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    transcription_payload = {
        "model": "openai/whisper-1",

        "input_audio": {
            "data": audio_base64,
            "format": "wav"
        },

        "language": "en"
    }

    transcription_response = requests.post(
        "https://openrouter.ai/api/v1/audio/transcriptions",
        headers=transcription_headers,
        json=transcription_payload,
        timeout=60
    )

    if transcription_response.status_code == 200:

        transcription_result = (
            transcription_response.json()
        )

        transcribed_text = (
            transcription_result.get("text", "")
        )

        return transcribed_text

    else:

        raise Exception(
            f"Speech-to-text error "
            f"{transcription_response.status_code}: "
            f"{transcription_response.text}"
        )


# ============================================================
# TITLE
# ============================================================

st.title("🎙️ AI Voice Assistant")

st.write(
    f"Welcome back, **{st.session_state.username}**! "
    "Ask your questions using your voice."
)


# ============================================================
# SIDEBAR - ACCOUNT + MEMORY CONTROLS
# ============================================================

with st.sidebar:

    st.header("👤 Account")
    st.write(f"welcome** {st.session_state.username}**")

    if st.button("🚪 Log out"):
        logout()
        st.rerun()

    st.divider()

    st.header("🧠 Memory")

    if st.session_state.messages:
        with st.expander("📜 Conversation History", expanded=True):
            for msg in st.session_state.messages:
                role_label = "🧑 You" if msg["role"] == "user" else "🤖 Assistant"
                st.markdown(f"**{role_label}:**\n{msg['content']}")
                st.divider()
    else:
        st.caption("No past history yet.")

    if st.button("🗑️ Clear My History"):
        st.session_state.messages = []
        clear_remote_history()
        st.success("Your history has been cleared!")
        st.rerun()


# ============================================================
# DISPLAY CURRENT CONVERSATION
# ============================================================

if st.session_state.messages:

    st.subheader("💬 Conversation")

    for message in st.session_state.messages:

        if message["role"] == "user":

            with st.chat_message("user"):
                st.write(message["content"])

        elif message["role"] == "assistant":

            with st.chat_message("assistant"):
                st.write(message["content"])


# ============================================================
# VOICE INPUT
# ============================================================

st.subheader("🎤 Voice Input")

audio_value = st.audio_input(
    "Record your question"
)


# ============================================================
# SUBMIT BUTTON
# ============================================================

if st.button("🚀 Submit"):

    if audio_value is not None:

        st.audio(audio_value)

        with st.spinner(
            "🎤 Converting speech to text..."
        ):

            try:

                audio_bytes = audio_value.getvalue()

                transcribed_text = transcribe_audio(
                    audio_bytes
                )

                if not transcribed_text:

                    st.error(
                        "The transcription returned empty text."
                    )

                else:

                    st.success(
                        "✅ Speech converted to text!"
                    )

                    st.subheader(
                        "📝 You said:"
                    )

                    st.write(
                        transcribed_text
                    )

                    with st.spinner(
                        "🤖 Generating AI response..."
                    ):

                        answer = generate_ai_response(
                            transcribed_text
                        )

                    st.subheader(
                        "🤖 AI Assistant"
                    )

                    st.write(answer)

            except requests.exceptions.RequestException as e:

                st.error(
                    f"Connection error: {e}"
                )

            except Exception as e:

                st.error(
                    f"An error occurred: {e}"
                )

    else:

        st.warning(
            "🎤 Please record your voice first."
        )
