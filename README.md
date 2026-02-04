# 🤖 Streamlit Chatbot with LiteLLM & Gemini

A production-ready chatbot application built with Streamlit, LiteLLM, and Google's Gemini models, featuring Langfuse tracing and comprehensive monitoring.

## ✨ Features

### Core Capabilities
- 💬 **Intelligent Conversations**: Powered by Google's Gemini-3-Flash model via LiteLLM
- 📝 **Chat History**: Maintains conversation context throughout the session
- 🎛️ **Adjustable Settings**: Temperature slider to control response creativity
- 🎨 **Modern UI**: Polished interface with chat bubbles, avatars, and responsive design
- 🔒 **Secure**: API keys managed through environment variables

### Monitoring & Observability 🔍
- 📊 **Request Tracking**: Correlation IDs, timestamps, and comprehensive request logging
- 💰 **Cost Tracking**: Real-time token usage and cost tracking with Gemini pricing
- ⚡ **Latency Metrics**: Response time tracking aggregated from Langfuse traces
- 🚨 **Error Categorization**: Structured error handling (rate limits, auth, timeouts, etc.)
- 📈 **Integrated Dashboard**: Real-time visualization of Langfuse metrics in the Monitor tab
- 🎯 **Langfuse Cloud Integration**: Production-grade observability with timestamp, name, tokens, latency, and cost tracking
- 💬 **User Feedback**: Thumbs up/down ratings for response quality tracking

### Resilience & Reliability
- 🔄 **Retry Logic**: Exponential backoff for transient failures
- ⏱️ **Timeout Configuration**: Prevents hanging requests
- 🛡️ **Circuit Breaker**: Protects against cascading failures
- 📉 **Rate Limiting**: Prevents API quota exhaustion

## 📋 Prerequisites

- Python 3.12.1 or higher
- API key for Lingaro GenAI Proxy (starts with `sk-`)
- Langfuse account for observability (free tier available at https://cloud.langfuse.com)

## 🚀 Quick Start

### 1. Clone or Download the Project

```bash
cd streamlit-chatbot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# API Configuration
GEMINI_API_KEY=your-api-key-here
GOOGLE_GEMINI_BASE_URL=https://llm.lingarogroup.com
LLM_PROVIDER=openai
BASE_MODEL_ID=gemini-3-flash

# Langfuse Observability (v2.12.0)
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 5. Run the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### 6. Configure Langfuse (Recommended for Production)

The chatbot integrates with Langfuse for production-grade observability:

#### Langfuse Observability

**Langfuse 2.12.0** provides trace tracking, cost monitoring, and analytics.

**Setup:**

1. Sign up at https://cloud.langfuse.com (free tier available)
2. Create a new project
3. Copy your API keys to `.env`:

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**View traces:**
- Visit the **Monitor** tab in the Streamlit app for integrated dashboard
- Access full Langfuse dashboard at https://cloud.langfuse.com
- View real-time statistics: traces, tokens, latency, costs
- Analyze individual requests with trace details

**Features:**
- Direct SDK integration (compatible with LiteLLM 1.49.7)
- Token usage estimation from cost data
- Latency monitoring aggregated from traces
- Session tracking across conversations
- Automatic trace synchronization to cloud
- Manual trace/generation creation for full control

**Tracked Metrics:**
- ✅ Timestamp (trace creation time)
- ✅ Name (e.g., "chat_completion")
- ✅ Tokens (input/output estimated from cost)
- ✅ Latency (seconds per request)
- ✅ Cost (USD per request, calculated by Langfuse)
- ❌ Input/Output text (not available in Langfuse 2.12.0)

**Known Limitations (Langfuse 2.12.0):**
- Input/Output text not displayed in Langfuse UI (version limitation)
- Token counts estimated from cost data using Gemini pricing
- Observations returned as IDs only in API (not full objects)

#### Monitoring Dashboard

Access the integrated monitoring dashboard:

```bash
# Navigate to the Monitor page in the sidebar
# Or visit: http://localhost:8501/Monitor
```

**Dashboard Features:**
- 🔍 **Langfuse Statistics**: Real-time trace count, tokens (estimated), average latency, and total cost
- 📊 **Aggregated Metrics**: Total traces, observations, token usage, and cost over time
- ⏱️ **Latency Analysis**: Average latency calculated from Langfuse trace data
- 🔢 **Token Metrics**: Estimated from cost data using Gemini pricing (input/output)
- 💰 **Cost Tracking**: Real-time cost aggregation from Langfuse traces
- 📋 **Recent Traces Table**: Individual trace details with timestamp, name, latency, tokens, cost
- 🔗 **Langfuse Integration**: Direct link to full Langfuse dashboard

**Data Sources:**
- **Langfuse Cloud API**: Trace data fetched via Public API with basic auth
- **Trace-Level Metrics**: Cost and latency aggregated from trace objects
- **Token Estimation**: Calculated from `totalCost` using Gemini pricing model

## 📁 Project Structure

```
streamlit-chatbot/
├── app.py                          # Main Streamlit chatbot UI
├── backend.py                      # LLM backend with Langfuse integration
├── requirements.txt                # Python dependencies (pinned versions)
├── .env                           # Environment configuration (not in git)
├── .env.example                   # Environment template
├── README.md                      # This file
│
├── pages/
│   └── 2_Monitor.py               # Langfuse monitoring dashboard
│
└── prompts/
    └── system_prompt.txt          # System prompt configuration
```

## 🎯 Usage

### Basic Chat

1. Type your message in the chat input at the bottom
2. Press Enter or click Send
3. Watch as the AI responds in real-time

### Adjust Settings

- Use the **Temperature slider** in the sidebar to control response randomness:
  - Lower values (0.0-0.5): More focused and deterministic
  - Medium values (0.5-1.0): Balanced creativity
  - Higher values (1.0-2.0): More creative and varied

### Clear Chat History

Click the **"🧹 Clear Chat"** button in the sidebar to start a fresh conversation.

### Rate Responses

After each AI response, use the 👍 or 👎 buttons to provide feedback. This data is logged locally and can be integrated with future analytics.

## 📊 Monitoring & Observability

### Overview

The chatbot includes production-grade observability via Langfuse:

1. **Langfuse Cloud Integration** - Direct SDK integration for trace tracking
2. **Integrated Dashboard** - Real-time Langfuse metrics in Monitor tab
3. **Cost Tracking** - Automatic cost calculation by Langfuse
4. **Latency Monitoring** - Request duration tracking

### Resilience Features

| Feature | Description | Configuration |
|---------|-------------|---------------|
| **Retry Logic** | 3 attempts with exponential backoff | Built-in (2s → 4s → 8s) |
| **Timeout** | Configurable request timeout | `REQUEST_TIMEOUT` (default: 30s) |

### Metrics Tracked

Every request automatically logs to Langfuse:

| Metric | Description | Availability |
|--------|-------------|--------------|
| `timestamp` | Trace creation time (ISO 8601 UTC) | ✅ Available |
| `name` | Trace name (e.g., "chat_completion") | ✅ Available |
| `latency` | Request duration in seconds | ✅ Available |
| `totalCost` | Cost in USD (auto-calculated) | ✅ Available |
| `tokens` | Estimated from cost | ✅ Estimated |
| `input/output` | Request/response text | ❌ Not in v2.12.0 |

### Metrics Storage

**Langfuse Cloud**: All traces synced to Langfuse via direct SDK integration:
- Manual trace/generation creation in [backend.py](backend.py)
- ModelUsage object with token counts and costs
- Session tracking via session_id
- User identification via user_id

### Monitoring Dashboard

Access the Monitor tab to view Langfuse metrics:

**Aggregated Statistics:**
- Total traces in selected time range
- Total observations (generations)
- Total tokens (estimated from cost)
- Average latency across all traces
- Total cost aggregation

**Individual Trace Table:**
- Timestamp of each trace
- Trace name
- Latency per request
- Tokens (estimated)
- Cost per request
- Trace ID for debugging

**Time Range Filters:**
- Last Hour
- Last 6 Hours
- Last 24 Hours
- Custom ranges via Langfuse dashboard
| **High Cost** | `ALERT_COST_THRESHOLD` | $1.00/hour | Triggered when hourly cost exceeds budget |

**Alert Cooldown:**
- Configurable via `ALERT_COOLDOWN_HOURS` (default: 1 hour)
- Prevents alert spam for ongoing issues
- Each alert type has independent cooldown

**Delivery Methods:**

**Email (SMTP):**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use app-specific password for Gmail
### Cost Tracking

Automatic cost calculation based on Gemini Flash pricing (2026):

| Token Type | Cost per 1M tokens |
|------------|-------------------|
| Input tokens | $0.075 |
| Output tokens | $0.30 |

**Cost is calculated by Langfuse** based on token usage:
- Cost tracked at trace level in `totalCost` field
- Aggregated in Monitor tab dashboard
- Individual trace costs visible in Recent Traces table

**View costs:**
- Real-time: Monitor tab shows total cost and per-trace breakdown
- Historical: Langfuse cloud dashboard with time-series analysis
- Trend Analysis: Export data from Langfuse for custom reporting

### Performance Optimization

**Tips for reducing latency:**
1. Use lower `max_tokens` for faster responses
2. Reduce conversation history length
3. Deploy closer to API regions
4. Monitor average latency in Monitor tab

**Tips for reducing cost:**
1. Use shorter system prompts
2. Implement message truncation for long conversations
3. Use lower temperature for deterministic responses
4. Monitor token usage in Monitor tab (estimated from cost)
5. Review costs in Langfuse dashboard regularly

## 🔧 Customization

### Change the System Prompt

Edit `prompts/system_prompt.txt` to customize the AI's behavior and personality. Changes take effect immediately (no restart required).

### Use a Different Model

In `.env`, modify:

```bash
LLM_PROVIDER=openai  # or 'gemini'
BASE_MODEL_ID=gemini-3-flash  # or 'gpt-4', 'claude-3', etc.
```

LiteLLM supports 100+ models. See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for full list.

### Customize the UI

Modify the CSS in `app.py` (search for `CUSTOM_CSS`):

```python
CUSTOM_CSS = """
<style>
    .chat-bubble { border-radius: 20px; /* Your changes */ }
</style>
"""
```

### Adjust Monitoring Thresholds

Edit `.env` to customize alert sensitivity:

```bash
ALERT_ERROR_RATE_THRESHOLD=5.0      # Alert if >5% errors
ALERT_LATENCY_P95_THRESHOLD=3.0     # Alert if p95 >3 seconds
ALERT_COST_THRESHOLD=0.50           # Alert if cost >$0.50/hour
```

### Add Custom Metrics

In `backend.py`, extend the `_log_metrics()` call:

```python
_log_metrics({
    # ... existing metrics ...
    "custom_field": your_value,
    "user_id": session_user_id,
    "conversation_length": len(history),
})
```

Then update dashboard queries to visualize your custom metrics.

## 🧪 Testing

Run the comprehensive test suite:

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_monitoring.py -v

# With coverage
pytest tests/ --cov=backend --cov=monitoring --cov-report=html

# Integration tests (requires API key)
pytest tests/ -v -m integration
```

**Test Categories:**
- Cost calculation accuracy
- Metrics logging
- Feedback capture
- Retry logic
- Error categorization
- Alert threshold detection
- Dashboard data parsing

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       USER BROWSER                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    Streamlit WebSocket
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   STREAMLIT APP (app.py)                     │
│  • Session state management                                  │
│  • User feedback capture (👍/👎)                            │
│  • Chat UI rendering                                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                   Function call (in-process)
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND MODULE (backend.py)                  │
│  • Request correlation IDs                                   │
│  • Structured logging                                        │
│  • Retry logic (3 attempts, exponential backoff)             │
│  • Cost calculation                                          │
│  • Metrics logging to JSONL                                  │
│  • Error categorization                                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    litellm.completion()
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│  LITELLM LIBRARY    │         │   LANGFUSE (opt)    │
│  • Provider routing │         │   • Tracing         │
│  • Request format   │────────▶│   • Cost tracking   │
│  • Response parsing │         │   • Prompt versions │
└──────────┬──────────┘         └─────────────────────┘
           │
           │ HTTPS POST
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│              LINGARO PROXY (llm.lingarogroup.com)           │
│  • Authentication                                            │
│  • Rate limiting                                             │
│  • Request forwarding                                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Google AI API
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   GOOGLE GEMINI API                          │
│  • gemini-3-flash model                                      │
│  • Token counting                                            │
│  • Response generation                                       │
└─────────────────────────────────────────────────────────────┘

                    Async/Scheduled Process
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MONITORING SYSTEM (monitoring/)                 │
│                                                              │
│  ┌──────────────────────────────────────────────┐          │
│  │   dashboard.py (Streamlit)                   │          │
│  │   • Reads metrics/requests.jsonl             │          │
│  │   • Visualizes trends, costs, errors         │          │
│  │   • User feedback analysis                   │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  ┌──────────────────────────────────────────────┐          │
│  │   alerts.py (Cron/Timer)                     │          │
│  │   • Analyzes recent metrics                  │          │
│  │   • Checks thresholds                        │          │
│  │   • Sends email/Slack alerts                 │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Streamlit captures message
2. **Request Tracking** → Generate UUID, start timer
3. **Backend Processing** → Build message history, add system prompt
4. **LLM Call** → LiteLLM routes to Gemini via proxy (with retries)
5. **Response** → Extract tokens, calculate cost, measure latency
6. **Metrics Logging** → Append to JSONL file
7. **Tracing** → Optional Langfuse trace created
8. **UI Update** → Render response with feedback buttons
9. **User Feedback** → Capture rating, log to feedback file
10. **Monitoring** → Dashboard reads JSONL, visualizes metrics
11. **Alerting** → Periodic checks trigger notifications if needed

### Key Design Decisions

**Why JSONL for metrics?**
- Simple, no database required
- Easy to parse, grep, and analyze
**Why direct Langfuse SDK integration?**
- Full control over trace/generation creation
- Compatible with LiteLLM 1.49.7 (stable version)
- No callback conflicts or version incompatibilities
- Manual ModelUsage object for precise tracking

**Why Langfuse 2.12.0?**
- Stable version with proven compatibility
- Direct SDK support without breaking changes
- Compatible with current LiteLLM version
- Input/output limitation acceptable for cost/latency tracking

**Why Monitor tab instead of separate dashboard?**
- Integrated experience in main app
- Real-time Langfuse data via Public API
- No separate deployment required
- Direct link to full Langfuse dashboard when needed

## 🔐 Security Best Practices

- ✅ API keys stored in `.env` file (not committed to version control)
- ✅ Environment variables loaded securely
- ✅ No hardcoded credentials
- ✅ `.env.example` provided for reference

## 🐛 Troubleshooting

### Configuration Issues

**"Missing or invalid GEMINI_API_KEY" Error**
- Ensure `.env` file exists in project root
- API key must start with `sk-`
- No quotes around the value
- Restart Streamlit after changes

**"Configuration error" in chat**
- Check all required variables in `.env`
- Ensure `GOOGLE_GEMINI_BASE_URL` starts with `https://`
- Model name must include provider prefix (e.g., `openai/gemini-3-flash`)

### Monitoring Issues

### Monitoring Issues

**Langfuse not receiving traces**
- Verify keys are correct (public key starts with `pk-lf-`, secret with `sk-lf-`)
- Check network connectivity to https://cloud.langfuse.com
- Look for Langfuse errors in application logs
- Test with Langfuse dashboard directly

**Monitor tab showing zeros**
- Ensure traces exist in Langfuse cloud dashboard first
- Check API key permissions for Public API access
- Verify time range filter includes your traces
- Token counts are estimated from cost (may be approximate)

**Token counts seem inaccurate**
- Tokens are estimated from `totalCost` using Gemini pricing
- Langfuse 2.12.0 limitation: observation data not fully available via API
- For exact tokens, check Langfuse cloud dashboard
- Cost tracking is accurate (calculated by Langfuse)
- Verify Slack webhook URL is correct
- Check `ALERT_COOLDOWN_HOURS` hasn't blocked alerts
- Ensure enough requests for threshold calculation (`ALERT_MIN_REQUESTS`)

### Performance Issues

**Slow response times**
- Check dashboard p95 latency
- Verify network connectivity to proxy
- Reduce `max_tokens` in `backend.py`
- Try a different model
- Check Langfuse overhead (disable temporarily)

**High costs**
- Review cost dashboard
- Shorten system prompt
- Reduce conversation history length
- Set `ALERT_COST_THRESHOLD` for early warning

**Memory usage growing**
- Streamlit session state grows with history
- Click "Clear Chat" button periodically
- Implement max history length in `app.py`

### API Errors

**Rate Limit Errors**
- Automatic retries with backoff
- Check proxy quotas
- Implement request throttling if persistent

**Authentication Errors**
- Verify API key is current
- Check proxy service status
- Ensure key has required permissions

**Timeout Errors**
- Increase `REQUEST_TIMEOUT` in `.env`
- Check network latency
- Try simpler prompts

## 📚 Dependencies

### Core Application
- **streamlit** `1.30.0` - Web application framework
- **litellm** `1.25.3` - Unified LLM interface (supports 100+ providers)
- **python-dotenv** `1.0.0` - Environment variable management
- **google-generativeai** `0.4.0` - Gemini SDK (used by LiteLLM)

### Monitoring & Observability
- **langfuse** `2.12.0` - LLM tracing and observability platform
- **tenacity** `8.2.3` - Retry logic with exponential backoff

### Dashboard & Analytics
- **pandas** `2.1.4` - Data manipulation and analysis
- **plotly** `5.18.0` - Interactive visualizations

### Alerting
- **requests** `2.31.0` - HTTP library for Slack webhooks

### Testing
- **pytest** `7.4.3` - Testing framework
- **pytest-asyncio** `0.21.1` - Async test support

All versions are pinned for reproducibility. Update carefully and test thoroughly.

## 🧪 Testing

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=backend --cov=monitoring --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

### Run Observability Tests

```bash
# Test logging, Prometheus, and secret masking
pytest tests/test_observability.py -v

# Run specific test
pytest tests/test_observability.py::TestLoggingConfiguration::test_litellm_logging_disabled_by_default -v
```

### Smoke Tests

Quick verification that everything works:

```bash
# Test 1: Verify backend imports
python -c "import backend; print('✅ Backend imports successfully')"

# Test 2: Check Prometheus endpoint (if enabled)
curl http://localhost:9090/metrics | grep chatbot_requests_total

# Test 3: Verify log rotation
ls -lh logs/

# Test 4: Check metrics file
tail -1 metrics/requests.jsonl | python -m json.tool

# Test 5: Run verification script
python verify_setup.py
```

### Test Categories

The test suite includes:

1. **Unit Tests** (`test_observability.py`)
   - Logging configuration
   - Prometheus metrics
   - Secret masking
   - Metrics logging
   - Callback registration
   - Environment configuration

2. **Integration Tests** (`test_monitoring.py`)
   - End-to-end request flow
   - Dashboard analytics
   - Alert system
   - Cost calculations

3. **Smoke Tests**
   - Basic imports
   - File permissions
   - Service availability

### Continuous Integration

Example GitHub Actions workflow:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov=backend --cov=monitoring
```

## 🚀 Deployment

### Streamlit Cloud

1. Push your code to GitHub (ensure `.env` is in `.gitignore`)
2. Connect repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Configure secrets in Streamlit Cloud dashboard:
   - Go to App Settings → Secrets
   - Add all variables from `.env` in TOML format:
   ```toml
   GEMINI_API_KEY = "sk-your-key"
   GOOGLE_GEMINI_BASE_URL = "https://llm.lingarogroup.com"
   LLM_PROVIDER = "openai"
   BASE_MODEL_ID = "gemini-3-flash"
   
   # Optional monitoring
   LANGFUSE_PUBLIC_KEY = "pk-lf-..."
   LANGFUSE_SECRET_KEY = "sk-lf-..."
   ```
4. Deploy!

**Note:** Metrics persist only during app runtime on Streamlit Cloud. For persistent storage, use external database or cloud storage.

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create metrics directory
RUN mkdir -p metrics

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

Build and run:
```bash
docker build -t chatbot .
docker run -p 8501:8501 --env-file .env -v $(pwd)/metrics:/app/metrics chatbot
```

### Production Recommendations

1. **Persistent Metrics Storage**
   - Mount `metrics/` directory to persistent volume
   - Or migrate to PostgreSQL/MongoDB
   - Implement log rotation

2. **Monitoring Dashboard**
   - Run dashboard on separate port (8502)
   - Consider read-only access controls
   - Enable authentication if exposed

3. **Alerting**
   - Set up cron job or systemd timer
   - Configure proper alert channels
   - Adjust thresholds for your use case

4. **Backup**
   - Regular backups of `metrics/` directory
   - Export to S3/GCS for long-term storage

5. **Security**
   - Never commit `.env` or secrets
   - Use secrets management (AWS Secrets Manager, Vault, etc.)
   - Enable HTTPS (Streamlit Cloud does this automatically)
   - Implement rate limiting for public deployments

6. **Scaling**
   - Streamlit Cloud auto-scales to handle traffic
   - For self-hosted: use load balancer with multiple instances
   - Share metrics via network file system or database

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Add PostgreSQL backend for metrics
- [ ] Implement conversation persistence
- [ ] Add user authentication
- [ ] Create Grafana dashboards
- [ ] Add Prometheus metrics exporter
- [ ] Support more LLM providers
- [ ] A/B testing framework for prompts
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Document upload and RAG

## 📄 License

This project is open source and available for personal and commercial use.

## 🔗 Resources

### Documentation
- [Streamlit Documentation](https://docs.streamlit.io/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Langfuse Documentation](https://langfuse.com/docs) - v2.12.0
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Tenacity (Retry Logic)](https://tenacity.readthedocs.io/)

### Monitoring & Observability
- [Langfuse Cloud](https://cloud.langfuse.com) - Free tier available
- [Langfuse v2 Docs](https://langfuse.com/docs/sdk/python/v2) - Legacy version documentation

### LLM Providers via LiteLLM
- [Supported Providers](https://docs.litellm.ai/docs/providers) - 100+ models
- [OpenAI](https://platform.openai.com/)
- [Anthropic Claude](https://www.anthropic.com/)
- [Google Gemini](https://ai.google.dev/)
- [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

## 💡 Tips & Best Practices

### For Development
- Start with low temperature (0.2-0.4) for consistent testing
- Monitor the Langfuse dashboard during development
- Test error scenarios (invalid keys, timeouts)
- Run tests before committing: `pytest tests/ -v`

### For Production
- Set up Langfuse project with proper access controls
- Monitor cost daily in Langfuse dashboard
- Review trace logs for patterns and issues
- Implement rate limiting for public access
- Use environment variables for all credentials

### For Cost Optimization
- Use Gemini Flash (cheaper) vs Pro (more capable)
- Keep system prompts concise
- Limit conversation history length
- Monitor token usage per request in Monitor tab
- Costs are automatically calculated by Langfuse

### For Performance
- Monitor average latency in Monitor tab
- Deploy in same region as API for lower latency
- Use retry logic (already implemented)

### For Reliability
- Monitor trace data regularly
- Review error patterns in Langfuse dashboard
- Keep dependencies updated (test in dev first)
- Have rollback plan for deployments

### Current Version Information
- **Python**: 3.12.1
- **Streamlit**: 1.30.0
- **LiteLLM**: 1.49.7 (pinned for compatibility)
- **Langfuse**: 2.12.0 (pinned for stability)
- **Known Limitation**: Input/output text not tracked (Langfuse 2.12.0 version constraint)

---

**Built with ❤️ for production LLM applications**

For questions, issues, or contributions, please open an issue on GitHub.

**Enjoy your monitored, production-ready chatbot! 🚀📊**
