import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

# ====== Configuration ======

# Proxy base URL (Lingaro GenAI Proxy)
API_BASE = (
    os.getenv("GOOGLE_GEMINI_BASE_URL")
    or os.getenv("LITELLM_API_BASE")
    or "https://llm.lingarogroup.com"
)

# API key from the proxy (format: sk-xxxxxxxx)
API_KEY = (
    os.getenv("GEMINI_API_KEY")        # preferred
    or os.getenv("GOOGLE_API_KEY")     # fallback if someone reused this name
    or os.getenv("OPENAI_API_KEY")     # last-resort fallback
)

# Provider selection:
#   - "openai" -> use OpenAI-compatible path with model "openai/gemini-3-flash"
#   - "gemini" -> use native Gemini provider "gemini/gemini-3-flash"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()
if LLM_PROVIDER not in {"openai", "gemini"}:
    LLM_PROVIDER = "openai"

# Model id from the proxy models list:
# The proxy returns:
#   { "id": "gemini-3-flash", "owned_by": "openai", ... }
# So in OpenAI-compatible mode we call: model="openai/gemini-3-flash"
BASE_MODEL_ID = os.getenv("BASE_MODEL_ID", "gemini-3-flash").strip()

MODEL_NAME = os.getenv("LLM_MODEL_NAME")  # optional override
if not MODEL_NAME:
    if LLM_PROVIDER == "openai":
        MODEL_NAME = f"openai/{BASE_MODEL_ID}"
    else:
        MODEL_NAME = f"gemini/{BASE_MODEL_ID}"

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
    if not API_KEY or not API_KEY.startswith("sk-"):
        problems.append("Missing or invalid GEMINI_API_KEY (should start with 'sk-').")
    if not API_BASE.startswith("http"):
        problems.append("Invalid proxy base URL (GOOGLE_GEMINI_BASE_URL). Expected full https URL.")
    # For LiteLLM, model should usually include provider prefix.
    if "/" not in MODEL_NAME:
        problems.append("LLM model must include provider, e.g., 'openai/gemini-3-flash' or 'gemini/gemini-3-flash'.")
    # Small consistency hint if provider/model mismatch is likely
    if LLM_PROVIDER == "openai" and not MODEL_NAME.startswith("openai/"):
        problems.append("LLM_PROVIDER=openai but MODEL_NAME does not start with 'openai/'.")
    if LLM_PROVIDER == "gemini" and not MODEL_NAME.startswith("gemini/"):
        problems.append("LLM_PROVIDER=gemini but MODEL_NAME does not start with 'gemini/'.")
    return problems

def generate_response(user_message: str, history: list, temperature: float = 0.4) -> str:
    """
    Generate a chat response via LiteLLM routed to Lingaro's GenAI Proxy.

    :param user_message: latest user text
    :param history: prior turns in OpenAI chat format: [{"role": "user"|"assistant", "content": "..."}]
    :param temperature: 0.0 - 1.0
    :return: assistant response text
    """
    env_issues = _validate_env()
    if env_issues:
        bullet = " • " + "\n • ".join(env_issues)
        return (
            "⚠️ Configuration error:\n"
            f"{bullet}\n\n"
            "Fix:\n"
            "- Set GEMINI_API_KEY=sk-... (proxy key)\n"
            "- Set GOOGLE_GEMINI_BASE_URL=https://llm.lingarogroup.com\n"
            "- Ensure MODEL_NAME includes provider, e.g., 'openai/gemini-3-flash' (OpenAI mode) "
            "or 'gemini/gemini-3-flash' (native Gemini mode)."
        )

    system_prompt = load_system_prompt()

    # Build messages (avoid double-adding current user turn)
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
            api_base=API_BASE,           # route through Lingaro proxy
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
            f"(format ok: {'yes' if (API_KEY and API_KEY.startswith('sk-')) else 'no'})",
        ]
        return f"⚠️ Error: {type(e).__name__}: {str(e)}\n\nDiagnostics:\n- " + "\n- ".join(details)