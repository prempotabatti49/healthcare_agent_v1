"""
Sunflower Health AI — Streamlit Frontend
=========================================
Minimalist, sober UI with a transparent sunflower watermark.

Run:
  streamlit run frontend/app.py
"""
import os
import requests
import streamlit as st
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🌻 Sunflower Health AI",
    page_icon="🌻",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Base ── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
        background-color: #fafaf8;
        color: #2c2c2c;
    }

    /* ── Sunflower watermark in chat area ── */
    .chat-container {
        position: relative;
    }
    .chat-container::before {
        content: "🌻";
        font-size: 260px;
        position: fixed;
        top: 50%;
        left: 55%;
        transform: translate(-50%, -50%);
        opacity: 0.04;
        pointer-events: none;
        z-index: 0;
        line-height: 1;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #fffff8;
        border-right: 1px solid #e8e8e0;
    }

    /* ── Chat bubbles ── */
    .msg-user {
        background: #f0f0e8;
        border-radius: 16px 16px 4px 16px;
        padding: 12px 16px;
        margin: 6px 0;
        max-width: 80%;
        margin-left: auto;
        font-size: 0.95rem;
        border: 1px solid #e0e0d0;
    }
    .msg-assistant {
        background: #ffffff;
        border-radius: 16px 16px 16px 4px;
        padding: 12px 16px;
        margin: 6px 0;
        max-width: 82%;
        font-size: 0.95rem;
        border: 1px solid #e8e8e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .msg-timestamp {
        font-size: 0.72rem;
        color: #aaa;
        margin-top: 2px;
    }

    /* ── Input area ── */
    .stTextInput > div > div > input {
        border-radius: 24px;
        border: 1px solid #ddd;
        padding: 10px 18px;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 20px;
        background-color: #f5c842;
        color: #2c2c2c;
        border: none;
        font-weight: 600;
        padding: 8px 22px;
    }
    .stButton > button:hover {
        background-color: #e6b930;
    }

    /* ── Disclaimer ── */
    .disclaimer {
        font-size: 0.78rem;
        color: #888;
        border-top: 1px solid #eee;
        margin-top: 8px;
        padding-top: 6px;
    }

    /* ── Quote card ── */
    .quote-card {
        background: linear-gradient(135deg, #fffde7, #fff8e1);
        border-left: 4px solid #f5c842;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 12px 0;
        font-style: italic;
        color: #555;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session state helpers ─────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "token": None,
        "username": None,
        "conversation_id": None,
        "messages": [],         # list of {"role": str, "content": str, "ts": str}
        "page": "login",        # "login" | "register" | "chat" | "documents"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _api(method: str, path: str, **kwargs):
    """Helper that attaches auth header automatically."""
    headers = kwargs.pop("headers", {})
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.request(method, f"{API_BASE}{path}", headers=headers, **kwargs)


# ── Auth pages ────────────────────────────────────────────────────────────────

def page_login():
    st.markdown("## 🌻 Welcome to Sunflower")
    st.markdown("*Your personal health companion*")
    st.markdown("---")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In")

    if submitted:
        resp = requests.post(
            f"{API_BASE}/api/users/login",
            data={"username": username, "password": password},
        )
        if resp.status_code == 200:
            st.session_state.token = resp.json()["access_token"]
            st.session_state.username = username
            st.session_state.page = "chat"
            st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")

    st.markdown("---")
    if st.button("Create an account →"):
        st.session_state.page = "register"
        st.rerun()


def page_register():
    st.markdown("## 🌻 Create Your Account")
    st.markdown("---")

    with st.form("register_form"):
        full_name = st.text_input("Full Name (optional)")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Register")

    if submitted:
        resp = requests.post(
            f"{API_BASE}/api/users/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name or None,
            },
        )
        if resp.status_code == 201:
            st.success("Account created! Please sign in.")
            st.session_state.page = "login"
            st.rerun()
        else:
            detail = resp.json().get("detail", "Registration failed")
            st.error(detail)

    if st.button("← Back to Sign In"):
        st.session_state.page = "login"
        st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("### 🌻 Sunflower")
        st.markdown(f"*Hello, {st.session_state.username}*")
        st.markdown("---")

        if st.button("💬 New Conversation"):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.session_state.page = "chat"
            st.rerun()

        if st.button("📄 My Documents"):
            st.session_state.page = "documents"
            st.rerun()

        if st.button("💬 Chat"):
            st.session_state.page = "chat"
            st.rerun()

        st.markdown("---")

        # Daily quote
        try:
            q_resp = _api("GET", "/api/quotes/daily")
            if q_resp.status_code == 200:
                q = q_resp.json()
                st.markdown(
                    f'<div class="quote-card">"{q["quote"]}"'
                    f'{"<br><small>— " + q["author"] + "</small>" if q.get("author") else ""}'
                    f"</div>",
                    unsafe_allow_html=True,
                )
        except Exception:
            pass

        st.markdown("---")
        if st.button("Sign Out"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.markdown(
            '<p class="disclaimer">Sunflower is a wellness companion, '
            "not a medical provider. Always consult a qualified doctor "
            "for medical advice.</p>",
            unsafe_allow_html=True,
        )


# ── Chat page ─────────────────────────────────────────────────────────────────

def page_chat():
    render_sidebar()
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown("## 💬 Chat with Sunflower")

    # Display conversation history
    for msg in st.session_state.messages:
        ts = msg.get("ts", "")
        if msg["role"] == "user":
            st.markdown(
                f'<div class="msg-user">{msg["content"]}'
                f'<div class="msg-timestamp">{ts}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="msg-assistant">{msg["content"]}'
                f'<div class="msg-timestamp">{ts}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

    # Input
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([9, 1])
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder="How are you feeling today?",
                label_visibility="collapsed",
            )
        with col2:
            send = st.form_submit_button("Send")

    if send and user_input.strip():
        ts_now = datetime.now().strftime("%H:%M")
        st.session_state.messages.append(
            {"role": "user", "content": user_input, "ts": ts_now}
        )

        with st.spinner("Sunflower is thinking…"):
            resp = _api(
                "POST",
                "/api/chat/message",
                json={
                    "message": user_input,
                    "conversation_id": st.session_state.conversation_id,
                    "include_daily_quote": False,
                },
            )

        if resp.status_code == 200:
            data = resp.json()
            st.session_state.conversation_id = data["conversation_id"]
            ai_text = data["response"]

            if data.get("was_crisis_flagged"):
                st.error("⚠️ Crisis resources have been included in the response below.")

            st.session_state.messages.append(
                {"role": "assistant", "content": ai_text, "ts": ts_now}
            )
        else:
            st.error("Something went wrong. Please try again.")

        st.rerun()


# ── Documents page ────────────────────────────────────────────────────────────

def page_documents():
    render_sidebar()
    st.markdown("## 📄 My Health Documents")
    st.markdown(
        "Upload your doctor's reports, prescriptions, lab results, and other "
        "health documents. Sunflower will learn from them to give you better guidance."
    )
    st.markdown("---")

    # Upload section
    with st.expander("➕ Upload a new document", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "jpg", "jpeg", "png", "webp", "pptx"],
        )
        doc_type = st.selectbox(
            "Document type",
            ["medical_report", "prescription", "lab_result", "doctor_notes", "imaging", "other"],
        )
        notes = st.text_area("Notes (optional)", placeholder="e.g. Ayurvedic consultation report, June 2024")

        if st.button("Upload & Process") and uploaded_file:
            with st.spinner("Processing document…"):
                resp = _api(
                    "POST",
                    "/api/documents/upload",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                    data={"document_type": doc_type, "notes": notes},
                )
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"✅ {data['message']}")
            else:
                detail = resp.json().get("detail", "Upload failed")
                st.error(f"Upload failed: {detail}")

    # Existing documents
    st.markdown("### Your uploaded documents")
    docs_resp = _api("GET", "/api/documents/")
    if docs_resp.status_code == 200:
        docs = docs_resp.json()
        if not docs:
            st.info("No documents yet. Upload your first health document above.")
        for doc in docs:
            with st.container():
                col1, col2, col3 = st.columns([5, 2, 2])
                col1.markdown(f"**{doc['filename']}**")
                col2.markdown(f"`{doc['document_type']}`")
                col3.markdown(doc["created_at"][:10])
                if doc.get("notes"):
                    st.caption(doc["notes"])
                st.markdown("---")
    else:
        st.error("Could not load documents.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    _init_state()

    if st.session_state.token is None:
        if st.session_state.page == "register":
            page_register()
        else:
            page_login()
    else:
        if st.session_state.page == "documents":
            page_documents()
        else:
            page_chat()


if __name__ == "__main__":
    main()
