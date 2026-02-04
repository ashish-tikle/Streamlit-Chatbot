import os
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import litellm
from litellm import completion
from typing import Optional, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from pybreaker import CircuitBreaker
from ratelimit import limits, sleep_and_retry

# Check if running in Streamlit context
try:
    import streamlit as st

    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

# Langfuse (using LiteLLM's native callback for Langfuse 3.x)
try:
    from langfuse import Langfuse

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None

load_dotenv()

# ====== Logging Setup with Rotation ======
# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Get log file path from env or use default
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", str(LOGS_DIR / "chatbot.log"))

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # Console handler
        logging.StreamHandler(),
        # File handler with rotation (10MB max, 5 backups)
        RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)

# ====== PII Redaction Utility ======
import re


def redact_pii(text: str, redact_enabled: bool = True) -> str:
    """Redact personally identifiable information from text for privacy."""
    if not redact_enabled or not text:
        return text

    # Email addresses
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]", text
    )
    # Phone numbers (various formats)
    text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE_REDACTED]", text)
    text = re.sub(r"\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b", "[PHONE_REDACTED]", text)
    # SSN (US format)
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]", text)
    # Credit card numbers (basic pattern)
    text = re.sub(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[CC_REDACTED]", text)
    # API keys and tokens
    text = re.sub(r"\b(sk-|pk-|token-)[A-Za-z0-9]{20,}\b", "[TOKEN_REDACTED]", text)

    return text


# ====== LiteLLM Logging Configuration ======
# Enable/disable LiteLLM's built-in verbose logging
LITELLM_LOGGING = os.getenv("LITELLM_LOGGING", "false").lower() == "true"
if LITELLM_LOGGING:
    litellm.set_verbose = True
    logger.info("LiteLLM verbose logging enabled")
else:
    litellm.set_verbose = False

# Configure LiteLLM to not log sensitive data
litellm.suppress_debug_info = True  # Don't log full request/response bodies
litellm.drop_params = True  # Drop sensitive params from logs

# PII redaction configuration
ENABLE_PII_REDACTION = os.getenv("ENABLE_PII_REDACTION", "true").lower() == "true"


# Add custom callbacks for structured logging
def litellm_success_logger(kwargs, response_obj, start_time, end_time):
    """Log successful LiteLLM requests without sensitive data"""
    duration = end_time - start_time
    model = kwargs.get("model", "unknown")
    usage = getattr(response_obj, "usage", None)

    # Extract and redact response content for logging
    response_content = ""
    if hasattr(response_obj, "choices") and len(response_obj.choices) > 0:
        response_content = response_obj.choices[0].message.content[:100]
        response_content = redact_pii(response_content, ENABLE_PII_REDACTION)

    log_data = {
        "event": "litellm_success",
        "model": model,
        "duration_seconds": duration,
        "response_preview": response_content,
    }

    if usage:
        log_data["prompt_tokens"] = getattr(usage, "prompt_tokens", 0)
        log_data["completion_tokens"] = getattr(usage, "completion_tokens", 0)
        log_data["total_tokens"] = getattr(usage, "total_tokens", 0)

    logger.info(f"LiteLLM request successful: {json.dumps(log_data)}")


def litellm_failure_logger(kwargs, response_obj, start_time, end_time):
    """Log failed LiteLLM requests without sensitive data"""
    duration = end_time - start_time
    model = kwargs.get("model", "unknown")
    error_type = type(response_obj).__name__ if response_obj else "UnknownError"
    error_message = str(response_obj) if response_obj else "Unknown error"

    # Mask any API keys in error messages
    if "sk-" in error_message:
        error_message = error_message.replace(
            error_message[error_message.find("sk-") : error_message.find("sk-") + 20],
            "sk-***REDACTED***",
        )

    log_data = {
        "event": "litellm_failure",
        "model": model,
        "duration_seconds": duration,
        "error_type": error_type,
        "error_message": error_message[:200],  # Truncate long errors
    }

    logger.error(f"LiteLLM request failed: {json.dumps(log_data)}")


# ====== Metrics Storage ======
METRICS_DIR = Path("metrics")
METRICS_DIR.mkdir(exist_ok=True)
METRICS_FILE = METRICS_DIR / "requests.jsonl"
FEEDBACK_FILE = METRICS_DIR / "feedback.jsonl"

# ====== OpenTelemetry Tracing Setup (DISABLED - using Langfuse instead) ======
# OpenTelemetry has been removed in favor of Langfuse 3.x integration
tracer = None


# ====== Circuit Breaker ======
# Circuit breaker listener class
class CircuitBreakerListener:
    def before_call(self, cb, func, *args, **kwargs):
        pass

    def success(self, cb):
        pass

    def failure(self, cb, exc):
        pass

    def state_change(self, cb, old_state, new_state):
        if new_state.name == "open":
            logger.error(f"Circuit breaker opened after {cb.fail_counter} failures")
        elif new_state.name == "closed":
            logger.info("Circuit breaker closed - service recovered")


# Circuit breaker configuration: 5 failures in 60s = open for 30s
circuit_breaker = CircuitBreaker(
    fail_max=int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")),
    reset_timeout=int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "30")),
    name="LLM_API_Breaker",
    listeners=[CircuitBreakerListener()],
)


# def _get_secret(key: str, default: str | None = None) -> str | None:
def _get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Read config in priority order:
    1) st.secrets (Streamlit Cloud)
    2) environment variable
    Returns stripped string or default.
    """
    val = os.getenv(key, default)
    # Normalize: convert non-str types and strip whitespace/newlines
    if isinstance(val, (str, bytes)):
        val = val.decode() if isinstance(val, bytes) else val
        val = val.strip()
    return val


# ====== Configuration ======
API_BASE = (
    _get_secret("GOOGLE_GEMINI_BASE_URL")
    or _get_secret("LITELLM_API_BASE")
    or "https://llm.lingarogroup.com"
)
API_KEY = (
    _get_secret("GEMINI_API_KEY")
    or _get_secret("GOOGLE_API_KEY")
    or _get_secret("OPENAI_API_KEY")
)

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
        problems.append(
            "Invalid proxy base URL. Set GOOGLE_GEMINI_BASE_URL to full https URL."
        )
    # Model should include provider prefix
    if "/" not in MODEL_NAME:
        problems.append(
            "LLM model must include provider, e.g., 'openai/gemini-3-flash' or 'gemini/gemini-3-flash'."
        )
    # Provider/model consistency hints
    if LLM_PROVIDER == "openai" and not MODEL_NAME.startswith("openai/"):
        problems.append(
            "LLM_PROVIDER=openai but MODEL_NAME does not start with 'openai/'."
        )
    if LLM_PROVIDER == "gemini" and not MODEL_NAME.startswith("gemini/"):
        problems.append(
            "LLM_PROVIDER=gemini but MODEL_NAME does not start with 'gemini/'."
        )
    return problems


def _calculate_cost(usage: Dict[str, int]) -> float:
    """
    Calculate cost based on Gemini Flash pricing (as of Feb 2026).
    Input: $0.075 per 1M tokens
    Output: $0.30 per 1M tokens
    """
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    input_cost = (prompt_tokens / 1_000_000) * 0.075
    output_cost = (completion_tokens / 1_000_000) * 0.30

    return input_cost + output_cost


def _get_trace_metadata(
    request_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    prompt_template: str = "default",
) -> Dict[str, Any]:
    """Build metadata dictionary for tracing systems."""
    metadata = {
        "request_id": request_id,
        "prompt_template": prompt_template,
        "service": "streamlit-chatbot",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }

    # Add user/session IDs if provided
    if user_id:
        metadata["user_id"] = user_id
    if session_id:
        metadata["session_id"] = session_id

    # Add redacted info for privacy
    metadata["pii_redaction_enabled"] = ENABLE_PII_REDACTION

    return metadata


def _log_metrics(metrics: Dict[str, Any]) -> None:
    """Log metrics to JSONL file for analysis."""
    try:
        with open(METRICS_FILE, "a", encoding="utf-8") as f:
            json.dump(metrics, f)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to log metrics: {e}")


def log_feedback(
    request_id: str, message_index: int, rating: str, comment: str = ""
) -> None:
    """Log user feedback for a specific message."""
    try:
        feedback = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "message_index": message_index,
            "rating": rating,
            "comment": comment,
        }
        with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
            json.dump(feedback, f)
            f.write("\n")
        logger.info(f"Feedback logged: {rating} for request {request_id}")
    except Exception as e:
        logger.error(f"Failed to log feedback: {e}")


# Configure Langfuse - Direct SDK integration (LiteLLM callback incompatible)
try:
    # Check if Langfuse is explicitly enabled
    ENABLE_LANGFUSE = os.getenv("ENABLE_LANGFUSE", "true").lower() == "true"

    langfuse_client = None
    if ENABLE_LANGFUSE and LANGFUSE_AVAILABLE:
        langfuse_public_key = _get_secret("LANGFUSE_PUBLIC_KEY")
        langfuse_secret_key = _get_secret("LANGFUSE_SECRET_KEY")
        langfuse_host = _get_secret("LANGFUSE_HOST") or "https://cloud.langfuse.com"

        if langfuse_public_key and langfuse_secret_key:
            try:
                # Initialize Langfuse client directly
                langfuse_client = Langfuse(
                    public_key=langfuse_public_key,
                    secret_key=langfuse_secret_key,
                    host=langfuse_host,
                )
                logger.info(
                    f"Langfuse tracing enabled via direct SDK (host: {langfuse_host})"
                )
            except Exception as e:
                logger.warning(f"Failed to configure Langfuse: {e}")
        else:
            logger.info("Langfuse credentials not configured (optional)")
    elif not LANGFUSE_AVAILABLE:
        logger.info("Langfuse SDK not available (langfuse package not installed)")
    else:
        logger.info("Langfuse tracing disabled via ENABLE_LANGFUSE=false")

except Exception as e:
    logger.warning(f"Langfuse setup failed: {e}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
@circuit_breaker
@sleep_and_retry
@limits(
    calls=int(os.getenv("RATE_LIMIT_CALLS", "60")),
    period=int(os.getenv("RATE_LIMIT_PERIOD", "60")),
)
def _call_llm_with_retry(
    model: str,
    api_key: str,
    api_base: str,
    messages: list,
    temperature: float,
    timeout: int,
) -> dict:
    """
    Call LiteLLM with comprehensive resilience patterns:
    - Rate limiting (default: 60 requests/minute)
    - Circuit breaker (opens after 5 failures for 30s)
    - Retry logic with exponential backoff (3 attempts)
    - Timeout protection
    """
    return completion(
        model=model,
        api_key=api_key,
        api_base=api_base,
        messages=messages,
        temperature=temperature,
        stream=False,
        max_tokens=1024,
        timeout=timeout,
    )


def generate_response(
    user_message: str,
    history: list,
    temperature: float = 0.4,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    prompt_template: str = "default",
) -> str:
    """
    Generate a chat response via LiteLLM routed to Lingaro's GenAI Proxy.
    Includes monitoring, cost tracking, retry logic, error categorization, and distributed tracing.

    :param user_message: latest user text
    :param history: prior turns in OpenAI chat format: [{"role":"user"|"assistant","content":"..."}]
    :param temperature: 0.0 - 1.0
    :param user_id: optional user identifier for tracing
    :param session_id: optional session identifier for tracing
    :param prompt_template: name of the prompt template used
    :return: response text or error message
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    timeout = int(_get_secret("REQUEST_TIMEOUT") or "30")

    # Build trace metadata
    trace_metadata = _get_trace_metadata(
        request_id, user_id, session_id, prompt_template
    )

    logger.info(
        f"[{request_id}] New request: temp={temperature}, msg_len={len(user_message)}, tracing=Langfuse"
    )

    env_issues = _validate_env()
    if env_issues:
        bullet = " • " + "\n • ".join(env_issues)
        hint_location = (
            "Streamlit → Settings → Secrets"
            if _HAS_STREAMLIT
            else "your environment/.env"
        )
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
    if (
        not history
        or history[-1].get("role") != "user"
        or history[-1].get("content") != user_message
    ):
        messages.append({"role": "user", "content": user_message})

    # Attempt LLM call with retry logic and monitoring
    error_type = None
    error_message = None
    response_text = None
    usage = {}
    cost = 0.0

    try:
        # Prepare LiteLLM call parameters with metadata for Langfuse tracing
        llm_params = {
            "model": MODEL_NAME,
            "api_key": API_KEY,
            "api_base": API_BASE,
            "messages": messages,
            "temperature": temperature,
            "timeout": timeout,
            "metadata": {
                "request_id": request_id,
                "user_id": user_id or "anonymous",
                "session_id": session_id or request_id,
                "prompt_template": prompt_template,
                "environment": os.getenv("ENVIRONMENT", "development"),
            },
        }

        resp = _call_llm_with_retry(
            model=llm_params["model"],
            api_key=llm_params["api_key"],
            api_base=llm_params["api_base"],
            messages=llm_params["messages"],
            temperature=llm_params["temperature"],
            timeout=llm_params["timeout"],
        )

        response_text = resp["choices"][0]["message"]["content"]
        usage = resp.get("usage", {})
        cost = _calculate_cost(usage)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Log to Langfuse if enabled (Langfuse 2.12.0 - tracks metrics only)
        if langfuse_client:
            try:
                from langfuse.model import ModelUsage

                # Create trace with environment tag
                environment = os.getenv("ENVIRONMENT", "development")
                trace = langfuse_client.trace(
                    name="chat_completion",
                    user_id=user_id or "anonymous",
                    session_id=session_id or request_id,
                    metadata={"request_id": request_id, "environment": environment},
                    tags=[environment],
                )

                # Create usage object with cost details
                usage_obj = ModelUsage(
                    input=usage.get("prompt_tokens", 0),
                    output=usage.get("completion_tokens", 0),
                    total=usage.get("total_tokens", 0),
                    unit="TOKENS",
                    input_cost=(usage.get("prompt_tokens", 0) / 1_000_000) * 0.075,
                    output_cost=(usage.get("completion_tokens", 0) / 1_000_000) * 0.30,
                    total_cost=cost,
                )

                # Create generation (tracks: timestamp, name, tokens, latency, cost)
                trace.generation(
                    name="llm_completion",
                    model=MODEL_NAME,
                    model_parameters={"temperature": temperature},
                    start_time=start_time,
                    end_time=end_time,
                    usage=usage_obj,
                    metadata={"request_id": request_id},
                )

                langfuse_client.flush()
            except Exception as e:
                logger.warning(f"[{request_id}] Langfuse logging failed: {e}")

        logger.info(
            f"[{request_id}] Success: "
            f"tokens={usage.get('total_tokens', 0)}, "
            f"cost=${cost:.6f}, "
            f"duration={duration:.2f}s"
        )

        # Log metrics
        _log_metrics(
            {
                "request_id": request_id,
                "timestamp": start_time.isoformat(),
                "model": MODEL_NAME,
                "temperature": temperature,
                "user_message_length": len(user_message),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "cost_usd": cost,
                "duration_seconds": duration,
                "success": True,
                "error_type": None,
            }
        )

        return response_text

    except Exception as e:
        # Categorize errors
        from litellm.exceptions import (
            RateLimitError,
            AuthenticationError,
            ServiceUnavailableError,
            Timeout as LiteLLMTimeout,
            BadRequestError,
        )

        duration = (datetime.utcnow() - start_time).total_seconds()
        error_type = type(e).__name__
        error_message = str(e)

        logger.error(f"[{request_id}] Error: {error_type} - {error_message}")

        if isinstance(e, RateLimitError):
            logger.warning(f"[{request_id}] Rate limit hit: {e}")
            response_text = (
                "⚠️ Rate limit exceeded. Please wait a moment and try again."
            )
        elif isinstance(e, AuthenticationError):
            logger.error(f"[{request_id}] Authentication failed: {e}")
            response_text = "⚠️ Authentication error. Please check API credentials."
        elif isinstance(e, (LiteLLMTimeout, TimeoutError)):
            logger.warning(f"[{request_id}] Request timeout: {e}")
            response_text = "⚠️ Request timed out. Please try again."
        elif isinstance(e, ServiceUnavailableError):
            logger.error(f"[{request_id}] Service unavailable: {e}")
            response_text = (
                "⚠️ Service temporarily unavailable. Please try again later."
            )
        elif isinstance(e, BadRequestError):
            logger.error(f"[{request_id}] Bad request: {e}")
            response_text = (
                "⚠️ Invalid request format. Please try rephrasing your message."
            )
        else:
            logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
            details = [
                f"Provider mode: {LLM_PROVIDER}",
                f"Model: {MODEL_NAME}",
                f"Base URL: {API_BASE}",
                f"Key set: {'yes' if bool(API_KEY) else 'no'} "
                f"(format ok: {'yes' if (API_KEY and str(API_KEY).startswith('sk-')) else 'no'})",
                f"Using st.secrets: {'yes' if _HAS_STREAMLIT else 'no'}",
            ]
            response_text = (
                f"⚠️ Error: {error_type}: {error_message}\n\nDiagnostics:\n- "
                + "\n- ".join(details)
            )

        # Log error metrics
        _log_metrics(
            {
                "request_id": request_id,
                "timestamp": start_time.isoformat(),
                "model": MODEL_NAME,
                "temperature": temperature,
                "user_message_length": len(user_message),
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost_usd": 0.0,
                "duration_seconds": duration,
                "success": False,
                "error_type": error_type,
                "error_message": error_message,
            }
        )

        return response_text
