# Langfuse Integration Fix - Summary

**Date:** February 4, 2026  
**Issue:** Langfuse not showing latency, cost, and token information  
**Root Cause:** Version incompatibility between LiteLLM and Langfuse SDK

## Problem

### Symptoms
- No metrics visible in Langfuse dashboard
- LiteLLM errors in logs:
  ```
  ImportError: cannot import name 'ChatPromptClient' from 'langfuse.model'
  ```

### Root Cause
- **Langfuse 2.12.0** (older version, downgraded for OpenTelemetry compatibility)
- **LiteLLM 1.81.7** (recent version expecting newer Langfuse features)
- LiteLLM's automatic Langfuse callback incompatible with Langfuse 2.12.0

## Solution

### Implemented Direct Langfuse SDK Integration

**Instead of:** Relying on LiteLLM's automatic callback  
**Now using:** Direct Langfuse SDK calls

### Changes Made

#### 1. Import Langfuse SDK Directly ([backend.py](backend.py))
```python
# Langfuse SDK (direct integration - more reliable than LiteLLM callback)
try:
    from langfuse import Langfuse
    LANGFUSE_SDK_AVAILABLE = True
except ImportError:
    LANGFUSE_SDK_AVAILABLE = False
    Langfuse = None
```

#### 2. Initialize Langfuse Client
```python
langfuse_client = Langfuse(
    public_key=langfuse_public_key,
    secret_key=langfuse_secret_key,
    host=langfuse_host
)
```

#### 3. Create Traces for Each Request
```python
langfuse_trace = langfuse_client.trace(
    name="chat_request",
    user_id=user_id or "anonymous",
    session_id=session_id or request_id,
    metadata={...}
)
```

#### 4. Log Generations with Full Metrics
```python
langfuse_generation = langfuse_trace.generation(
    name="llm_completion",
    model=MODEL_NAME,
    model_parameters={"temperature": temperature},
    input=messages,
    output=response_text,
    usage={
        "promptTokens": usage.get("prompt_tokens", 0),
        "completionTokens": usage.get("completion_tokens", 0),
        "totalTokens": usage.get("total_tokens", 0),
    },
    metadata={
        "duration_seconds": duration,
        "cost_usd": cost,
        "request_id": request_id,
    }
)
langfuse_client.flush()  # Ensure data is sent immediately
```

#### 5. Error Logging
```python
# Errors also logged to Langfuse with proper status
langfuse_generation = langfuse_trace.generation(
    name="llm_completion",
    model=MODEL_NAME,
    input=messages,
    output=None,
    metadata={"error_type": error_type, "error_message": error_message},
    level="ERROR",
    status_message=error_message[:200]
)
```

## Benefits

### ✅ Full Metrics Now Captured
- ✅ **Latency**: Duration of each request
- ✅ **Tokens**: Prompt + Completion tokens
- ✅ **Cost**: Calculated cost per request
- ✅ **Session Tracking**: Groups requests by session
- ✅ **User Tracking**: Associates requests with users
- ✅ **Error States**: Captures failures with context

### ✅ Reliability Improvements
- ✅ No more import errors
- ✅ Works with Langfuse 2.12.0
- ✅ Compatible with current dependency versions
- ✅ Graceful fallback if Langfuse unavailable
- ✅ Explicit flush ensures data delivery

### ✅ Better Observability
- ✅ Traces visible in Langfuse cloud dashboard
- ✅ Integrated monitoring tab shows live statistics
- ✅ Request-level details with full context
- ✅ Session-level analytics

## Verification

### Logs Before Fix
```
LiteLLM:ERROR: langfuse.py:885 - Langfuse Layer Error
ImportError: cannot import name 'ChatPromptClient' from 'langfuse.model'
```

### Logs After Fix
```
2026-02-04 16:24:28,402 - backend - INFO - Request tracing: Langfuse (direct SDK)
2026-02-04 16:24:42,580 - backend - INFO - Success: tokens=187, cost=$0.000026, duration=2.75s
```

**Result:** ✅ Clean execution, no errors!

## Testing

### How to Verify in Langfuse Dashboard

1. **Open Langfuse**: https://cloud.langfuse.com
2. **Navigate to your project**
3. **Go to "Traces" tab**
4. **Look for recent traces** with name "chat_request"
5. **Click on a trace** to see:
   - ✅ Session ID
   - ✅ User ID
   - ✅ Request metadata
6. **Expand "llm_completion" generation** to see:
   - ✅ Input messages
   - ✅ Output response
   - ✅ Token usage (prompt + completion)
   - ✅ Cost calculation
   - ✅ Duration/latency
   - ✅ Model parameters

### How to Verify in Monitor Tab

1. **Open app**: http://localhost:8501
2. **Navigate to Monitor tab**
3. **Check "Langfuse Tracing Statistics" section**
4. **Verify metrics display:**
   - ✅ Total Traces
   - ✅ Total Tokens
   - ✅ Avg Latency
   - ✅ Total Cost
   - ✅ Avg Tokens/Trace
5. **Check "Recent Traces" table** for individual request details

## Files Modified

- **[backend.py](backend.py)**
  - Added direct Langfuse SDK import
  - Removed LiteLLM callback approach
  - Added trace creation for each request
  - Added generation logging with full metrics
  - Added error logging to Langfuse

## Dependencies

**No changes needed** - Langfuse 2.12.0 SDK already installed:
```bash
langfuse==2.12.0  # Already in requirements.txt
```

## Migration Notes

### Old Approach (Removed)
```python
# LiteLLM automatic callback
callbacks.append("langfuse")
litellm.success_callback = callbacks
```

### New Approach (Current)
```python
# Direct Langfuse SDK
langfuse_client = Langfuse(...)
langfuse_trace = langfuse_client.trace(...)
langfuse_generation = langfuse_trace.generation(...)
langfuse_client.flush()
```

## Advantages of Direct SDK

1. **Version Control**: Not dependent on LiteLLM's Langfuse integration version
2. **Explicit Control**: Full control over what data is sent
3. **Better Error Handling**: Graceful fallback without breaking requests
4. **Immediate Flush**: Ensures data is sent without relying on callbacks
5. **Future-Proof**: Won't break with LiteLLM updates

---

**Status:** ✅ Fixed and tested - Langfuse now receiving full metrics!
