import os
import streamlit as st
from backend import generate_response, MODEL_NAME

st.set_page_config(page_title="Gemini-3-Flash Chatbot", page_icon="🤖")

if "history" not in st.session_state:
    st.session_state.history = []

st.title("🤖 Gemini-3-Flash Chatbot")
API_BASE = os.getenv("GOOGLE_GEMINI_BASE_URL") or "https://llm.lingarogroup.com"
st.caption(f"Model: **{MODEL_NAME}** • Endpoint: `{API_BASE}`")


with st.sidebar:
    st.header("⚙️ Settings")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.4)
    if st.button("Clear Chat"):
        st.session_state.history = []

# Display chat history
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = generate_response(user_input, st.session_state.history, temperature)
        placeholder.write(full_response)

    st.session_state.history.append({"role": "assistant", "content": full_response})