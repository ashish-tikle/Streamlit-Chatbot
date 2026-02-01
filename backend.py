import os
from dotenv import load_dotenv
from litellm import completion

# Try to import streamlit to access st.secrets when running on Streamlit Cloud
try:
    import streamlit as st
    _HAS_STREAMLIT = True
except Exception:
    _HAS_STREAMLIT = False

load_dotenv()

def _get_secret(key: str, default: str | None = None) -> str | None:
    """
    Read config in priority order:
    1) st.secrets (Streamlit Cloud)
    2) environment variable
    Returns stripped string or default.
    """
    val = None
    if _HAS_STREAMLIT:
        try:
            if key in st.secrets:
                val = st.secrets.get(key, None)
        except Exception:
            # st.secrets may not be available in local runs
            pass
    if val is None:
        val = os.getenv(key, default)
    # Normalize: convert non-str types and strip whitespace/newlines
    if isinstance(val, (str, bytes)):
        val = val.decode() if isinstance(val, bytes) else val
        val = val.strip()
    return val

# ====== Configuration ======
API_BASE = _get_secret("GOOGLE_GEMINI_BASE_URL") or _get_secret("LITELLM_API_BASE") or "https://llm.lingarogroup.com"
API_KEY = _get_secret("GEMINI_API_KEY") or _get_secret("GOOGLE_API_KEY") or _get_secret("OPENAI_API_KEY")

LLM_PROVIDER = (_get_secret("LLM_PROVIDER") or "openai").lower()
if LLM_PROVIDER not in {"openai", "gemini"}:
    LLM_PROVIDER = "openai"

BASE_MODEL_ID = _get_secret("BASE_MODEL_ID") or "gemini-3-flash"

# Allow complete override; otherwise construct provider-prefixed model
MODEL_NAME = _get_secret("LLM_MODEL_NAME")
if not MODEL_NAME:
    MODEL_NAME = f"{LLM_PROVIDER}/{BASE_MODEL_ID}"

def load_system_prompt():
    try:
        with open("prompts/system_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return (
            "You are a helpful, concise, and professional AI assistant. "
            "Be factual, avoid chain-of-thought, and ask clarifying questions when needed."
        )

def _validate_env():
    problems = []
    # Key should exist and start with sk-
    if not API_KEY or not str(API_KEY).startswith("sk-"):
        problems.append("Missing or invalid GEMINI_API_KEY (should start with 'sk-').")
    # Base URL should be a proper URL
    if not API_BASE or not str(API_BASE).startswith("http"):
        problems.append("Invalid proxy base URL. Set GOOGLE_GEMINI_BASE_URL to full https URL.")
    # Model should include provider prefix
    if "/" not in MODEL_NAME:
        problems.append("LLM model must include provider, e.g., 'openai/gemini-3-flash' or 'gemini/gemini-3-flash'.")
    # Provider/model consistency hints
    if LLM_PROVIDER == "openai" and not MODEL_NAME.startswith("openai/"):
        problems.append("LLM_PROVIDER=openai but MODEL_NAME does not start with 'openai/'.")
    if LLM_PROVIDER == "gemini" and not MODEL_NAME.startswith("gemini/"):
        problems.append("LLM_PROVIDER=gemini but MODEL_NAME does not start with 'gemini/'.")
    return problems

def generate_response(user_message: str, history: list, temperature: float = 0.4) -> str:
    """
    Generate a chat response via LiteLLM routed to Lingaro's GenAI Proxy.
    :param user_message: latest user text
    :param history: prior turns in OpenAI chat format: [{"role":"user"|"assistant","content":"..."}]
    :param temperature: 0.0 - 1.0
    """
    env_issues = _validate_env()
    if env_issues:
        bullet = " • " + "\n • ".join(env_issues)
        hint_location = "Streamlit → Settings → Secrets" if _HAS_STREAMLIT else "your environment/.env"
        return (
            "⚠️ Configuration error:\n"
            f"{bullet}\n\n"
            f"Fix:\n"
            f"- Set GEMINI_API_KEY=sk-... (proxy key) in {hint_location}\n"
            f"- Set GOOGLE_GEMINI_BASE_URL=https://llm.lingarogroup.com\n"
            f"- Ensure MODEL_NAME includes provider; current resolved MODEL_NAME is '{MODEL_NAME}'."
        )

    system_prompt = load_system_prompt()

    # Build messages (avoid double-adding the current user turn)
    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        if m.get("role") in {"user", "assistant"} and isinstance(m.get("content"), str):
            messages.append(m)
    if not history or history[-1].get("role") != "user" or history[-1].get("content") != user_message:
        messages.append({"role": "user", "content": user_message})

    try:
        resp = completion(
            model=MODEL_NAME,
            api_key=API_KEY,
            api_base=API_BASE,
            messages=messages,
            temperature=temperature,
            stream=False,
            max_tokens=1024,
        )
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        details = [
            f"Provider mode: {LLM_PROVIDER}",
            f"Model: {MODEL_NAME}",
            f"Base URL: {API_BASE}",
            f"Key set: {'yes' if bool(API_KEY) else 'no'} "
            f"(format ok: {'yes' if (API_KEY and str(API_KEY).startswith('sk-')) else 'no'})",
            f"Using st.secrets: {'yes' if _HAS_STREAMLIT else 'no'}",
        ]
        return f"⚠️ Error: {type(e).__name__}: {str(e)}\n\nDiagnostics:\n- " + "\n- ".join(details)