# app.py (Polished UI, Python 3.9 compatible)
import os
import streamlit as st

# ------------------------------
# Page config (MUST be first Streamlit command)
# ------------------------------
st.set_page_config(
    page_title="Gemini Chatbot V2",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Import backend after page config to avoid Streamlit command conflicts
from backend import generate_response, MODEL_NAME, log_feedback

# ------------------------------
# Custom CSS (scoped)
# ------------------------------
CUSTOM_CSS = """
<style>
/* Layout & typography */
.main .block-container { padding-top: 1.6rem; padding-bottom: 2rem; max-width: 820px; }
h1, h2, h3 { letter-spacing: .2px; }

/* Header badge */
.header-wrap { display:flex; justify-content:space-between; align-items:center; }
.header-badge {
  display:inline-block; padding:4px 10px; border-radius:999px; font-size:.78rem;
  background:linear-gradient(135deg, rgba(59,130,246,.12), rgba(16,185,129,.12));
  color: var(--text-color, #444); border:1px solid rgba(0,0,0,0.06);
}

/* Chat bubbles */
.chat-bubble {
  padding:.9rem 1rem; border-radius:14px; margin-bottom:.6rem; line-height:1.55;
  border:1px solid rgba(0,0,0,0.06); white-space:pre-wrap; word-wrap:break-word;
}
.chat-user {
  background: rgba(59,130,246,0.08);
  border-color: rgba(59,130,246,0.14);
}
.chat-assistant {
  background: rgba(16,185,129,0.08);
  border-color: rgba(16,185,129,0.14);
}

/* Avatars */
.avatar {
  width:28px; height:28px; border-radius:50%; display:inline-block; margin-right:8px;
  vertical-align:middle; background-size:cover; background-position:center;
  box-shadow: 0 0 0 1px rgba(0,0,0,.06) inset;
}
.user-avatar { background-image:url('https://avatars.githubusercontent.com/u/9919?s=40&v=4'); }
.bot-avatar { background-image:url('https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/googlecloud.svg'); background-color:#ffffff; }

/* Message row */
.msg-row { display:flex; gap:10px; align-items:flex-start; margin: 8px 0 14px 0; }
.msg-content { flex:1; }

/* Footer */
.footer {
  margin-top: 28px; padding-top: 12px; font-size: .85rem; opacity: .75;
  border-top: 1px dashed rgba(0,0,0,0.1); text-align: center;
}

/* Code blocks within bubbles */
.chat-bubble pre { border-radius:10px !important; border:1px solid rgba(0,0,0,0.08) !important; }

/* Divider subtle */
hr { opacity: .5; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ------------------------------
# Session state defaults
# ------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.4
if "api_base" not in st.session_state:
    st.session_state.api_base = (
        os.getenv("GOOGLE_GEMINI_BASE_URL") or "https://llm.lingarogroup.com"
    )
if "feedback" not in st.session_state:
    st.session_state.feedback = {}  # Store feedback ratings by message index
if "session_id" not in st.session_state:
    import uuid

    st.session_state.session_id = str(uuid.uuid4())  # Persistent session ID for tracing
if "user_id" not in st.session_state:
    # In production, this would come from authentication
    st.session_state.user_id = os.getenv("USER_ID", "anonymous")

# ------------------------------
# Header
# ------------------------------
col_left, col_right = st.columns([0.8, 0.2])
with col_left:
    st.title("🤖 Gemini Chatbot V2")
    st.caption(
        "Model: **{}** • Endpoint: `{}`".format(MODEL_NAME, st.session_state.api_base)
    )
with col_right:
    st.markdown(
        '<div class="header-badge">Streamlit UI • LiteLLM • Gemini</div>',
        unsafe_allow_html=True,
    )

st.write("")  # small spacer


# ------------------------------
# Sidebar (Settings, About, Connectivity)
# ------------------------------
def _connectivity_test():
    try:
        ans = generate_response(
            "Reply exactly: PONG",
            [],
            0.0,
            user_id="system",
            session_id="connectivity_test",
            prompt_template="connectivity_test",
        )
        return ans.strip() if isinstance(ans, str) else str(ans)
    except Exception as e:
        return "ERR: {}".format(e)


with st.sidebar:
    st.subheader("⚙️ Settings")
    st.session_state.temperature = st.slider(
        "Creativity (temperature)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.temperature,
        step=0.05,
        help="Lower = more deterministic. Higher = more creative.",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear chat", use_container_width=True):
            st.session_state.history = []
            st.toast("Chat cleared", icon="🧽")
    with col2:
        if st.button("📡 Connectivity test", use_container_width=True):
            with st.spinner("Checking proxy & model…"):
                pong = _connectivity_test()
                if isinstance(pong, str) and pong.upper().startswith("PONG"):
                    st.success("Connected ✅", icon="✅")
                else:
                    st.error("Connectivity issue ❌", icon="❌")
                    st.code(pong)

    st.divider()
    st.subheader("ℹ️ About")
    st.markdown("""
        **Gemini 3 Flash** chatbot demo powered by **LiteLLM** via Lingaro GenAI Proxy.  
        Built with **Streamlit**, includes polished chat bubbles, avatars, and sidebar controls.
        """)
    st.caption("Tip: Use *Connectivity test* after updating secrets or redeploying.")


# ------------------------------
# Chat history renderer (avatars + bubbles, markdown)
# ------------------------------
def render_message(role, content, msg_index=None):
    if role not in ("user", "assistant"):
        return
    avatar_class = "user-avatar" if role == "user" else "bot-avatar"
    bubble_class = "chat-user" if role == "user" else "chat-assistant"

    # Wrap markdown inside our styled bubble
    st.markdown(
        """
        <div class="msg-row">
            <span class="avatar {avatar}"></span>
            <div class="msg-content">
                <div class="chat-bubble {bubble}">
        """.format(avatar=avatar_class, bubble=bubble_class),
        unsafe_allow_html=True,
    )
    # Render markdown safely inside
    st.markdown(content if isinstance(content, str) else str(content))
    st.markdown(
        """
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Add feedback buttons for assistant messages
    if role == "assistant" and msg_index is not None:
        col1, col2, col3 = st.columns([0.05, 0.05, 0.9])

        feedback_key = f"feedback_{msg_index}"
        current_feedback = st.session_state.feedback.get(msg_index, None)

        with col1:
            if st.button(
                "👍",
                key=f"thumbs_up_{msg_index}",
                disabled=(current_feedback == "positive"),
                help="Helpful response",
            ):
                st.session_state.feedback[msg_index] = "positive"
                # Get request_id from history if available
                request_id = st.session_state.history[msg_index].get(
                    "request_id", "unknown"
                )
                log_feedback(request_id, msg_index, "positive")
                st.toast("Thanks for your feedback! 👍", icon="✅")

        with col2:
            if st.button(
                "👎",
                key=f"thumbs_down_{msg_index}",
                disabled=(current_feedback == "negative"),
                help="Unhelpful response",
            ):
                st.session_state.feedback[msg_index] = "negative"
                request_id = st.session_state.history[msg_index].get(
                    "request_id", "unknown"
                )
                log_feedback(request_id, msg_index, "negative")
                st.toast("Thanks for your feedback! We'll improve.", icon="📝")


# Render past messages
for idx, msg in enumerate(st.session_state.history):
    try:
        render_message(
            msg.get("role"),
            msg.get("content"),
            idx if msg.get("role") == "assistant" else None,
        )
    except Exception:
        # Fallback (should rarely happen)
        st.write(msg)

# ------------------------------
# Chat input & response
# ------------------------------
user_input = st.chat_input("Type your message…")

if user_input:
    # Append & render user turn
    st.session_state.history.append({"role": "user", "content": user_input})
    render_message("user", user_input)

    # Assistant response
    with st.spinner("Thinking…"):
        import uuid

        request_id = str(uuid.uuid4())
        try:
            response_text = generate_response(
                user_input,
                st.session_state.history,  # contains the new user message
                st.session_state.temperature,
                user_id=st.session_state.user_id,
                session_id=st.session_state.session_id,
                prompt_template="default",
            )
            if not response_text or not isinstance(response_text, str):
                response_text = (
                    "⚠️ Sorry, I couldn't generate a response. Please try again."
                )
        except Exception as e:
            response_text = "⚠️ Error: {}".format(e)

    # Render & store assistant message with request_id for feedback correlation
    msg_index = len(st.session_state.history)
    render_message("assistant", response_text, msg_index)
    st.session_state.history.append(
        {"role": "assistant", "content": response_text, "request_id": request_id}
    )

# ------------------------------
# Footer
# ------------------------------
st.markdown(
    """
    <div class="footer">
        Made with ❤️ using Streamlit · LiteLLM · Gemini · by Ashish
    </div>
    """,
    unsafe_allow_html=True,
)
