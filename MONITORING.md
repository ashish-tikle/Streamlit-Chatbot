# Quick Reference: Monitoring Commands

## ✨ NEW: Integrated Langfuse Statistics in Monitoring Tab

The monitoring dashboard now displays **real-time Langfuse tracing statistics** directly in the UI!

Navigate to the **Monitor** tab in the Streamlit app to view:
- Total traces captured by Langfuse
- Token usage (input + output)
- Average latency with percentiles (P50, P95)
- Total cost calculated from actual usage
- Recent traces table with detailed metrics
- Direct link to full Langfuse dashboard

**No additional setup required** - it automatically pulls data from your configured Langfuse account.

## Running the Application

```bash
# Main chatbot with integrated monitoring
streamlit run app.py

# Then navigate to the "Monitor" page in the UI
# - View Langfuse statistics at the top
# - View local metrics below

# Monitoring dashboard (in separate terminal) - DEPRECATED
cd monitoring
streamlit run dashboard.py

# Run alert check manually
python monitoring/alerts.py
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov=monitoring --cov-report=html

# Run integration tests (requires API key)
pytest tests/ -v -m integration
```

## Langfuse API Integration

The monitoring dashboard uses Langfuse Public API to fetch real-time statistics:

```bash
# API endpoint used by the dashboard
GET https://cloud.langfuse.com/api/public/traces

# Parameters:
# - fromTimestamp: Start time (ISO 8601)
# - toTimestamp: End time (ISO 8601)  
# - page: Page number
# - limit: Results per page (default: 50)

# Authentication: Basic Auth
# Header: Authorization: Basic <base64(public_key:secret_key)>
```

**Configuration in .env:**
```env
ENABLE_LANGFUSE=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Metrics Displayed:**
- Total traces in time range
- Aggregated token usage (input + output)
- Cost calculations from Langfuse
- Latency statistics (avg, median, P95)
- Recent trace details with status

**Error Handling:**
- 401: Check API keys in .env
- 403: Verify Langfuse permissions
- Timeout: Network or API latency
- No data: No traces in selected time range

## Prometheus Metrics (Removed)

**Note:** Prometheus integration has been removed in favor of Langfuse tracing.

The following commands are deprecated:

```bash
# DEPRECATED - Prometheus removed
# View metrics endpoint
curl http://localhost:9090/metrics

# Test specific metrics
curl http://localhost:9090/metrics | grep chatbot_requests_total
curl http://localhost:9090/metrics | grep chatbot_request_duration

# Check active requests (gauge)
curl -s http://localhost:9090/metrics | grep "chatbot_active_requests " | grep -v "#"

# Monitor in real-time
watch -n 1 'curl -s http://localhost:9090/metrics | grep chatbot_requests_total'
```

## Circuit Breaker Commands

```bash
# Check circuit breaker state in logs
tail -f logs/chatbot.log | grep -i "circuit"

# Test circuit breaker (simulate failures)
export CIRCUIT_BREAKER_THRESHOLD=2
export CIRCUIT_BREAKER_TIMEOUT=10
# Then make requests that will fail

# Monitor circuit breaker state via Prometheus
curl -s http://localhost:9090/metrics | grep "chatbot_errors_total" | grep circuit_breaker
```

## Rate Limiting Commands

```bash
# Check current rate limit settings
grep RATE_LIMIT .env

# Monitor rate limiting in logs
tail -f logs/chatbot.log | grep -i "rate limit"

# Test rate limiting (make burst requests)
for i in {1..100}; do curl http://localhost:8501 & done
```

## Log Rotation

```bash
# View current log
tail -f logs/chatbot.log

# View rotated logs
ls -lh logs/
cat logs/chatbot.log.1
cat logs/chatbot.log.2

# Search across all logs
grep "ERROR" logs/chatbot.log*

# Check log sizes
du -sh logs/*

# Manual rotation (if needed)
timestamp=$(date +%Y%m%d_%H%M%S)
mv logs/chatbot.log logs/chatbot_${timestamp}.log
gzip logs/chatbot_${timestamp}.log
```

## Metrics Analysis (JSONL)

```bash
# View all metrics
cat metrics/requests.jsonl | jq .

# Total cost
cat metrics/requests.jsonl | jq -s 'map(.cost_usd) | add'

# Average latency
cat metrics/requests.jsonl | jq -s 'map(.duration_seconds) | add/length'

# Error count
cat metrics/requests.jsonl | jq -s 'map(select(.success == false)) | length'

# Today's requests
cat metrics/requests.jsonl | jq -s --arg date "$(date +%Y-%m-%d)" 'map(select(.timestamp | startswith($date)))'

# Error types breakdown
cat metrics/requests.jsonl | jq -s 'group_by(.error_type) | map({error_type: .[0].error_type, count: length})'
```

## Maintenance

```bash
# Archive old metrics (manual rotation)
mv metrics/requests.jsonl metrics/requests_$(date +%Y%m%d).jsonl
gzip metrics/requests_*.jsonl

# Clean up old archives (keep last 30 days)
find metrics/ -name "requests_*.jsonl.gz" -mtime +30 -delete
```

## Environment Variables Quick Reference

### Required
- `GEMINI_API_KEY` - API key (must start with sk-)
- `GOOGLE_GEMINI_BASE_URL` - Proxy URL

### Optional Monitoring
- `LANGFUSE_PUBLIC_KEY` - Langfuse public key
- `LANGFUSE_SECRET_KEY` - Langfuse secret key

### Resilience & Rate Limiting (NEW)
- `REQUEST_TIMEOUT` - Default: 30 (seconds)
- `RATE_LIMIT_CALLS` - Default: 60 (requests)
- `RATE_LIMIT_PERIOD` - Default: 60 (seconds)
- `CIRCUIT_BREAKER_THRESHOLD` - Default: 5 (failures)
- `CIRCUIT_BREAKER_TIMEOUT` - Default: 30 (seconds)

### Prometheus Metrics (NEW)
- `PROMETHEUS_PORT` - Default: 9090

### Optional Alerts
- `ALERT_ERROR_RATE_THRESHOLD` - Default: 10.0 (%)
- `ALERT_LATENCY_P95_THRESHOLD` - Default: 5.0 (seconds)
- `ALERT_COST_THRESHOLD` - Default: 1.0 (USD/hour)
- `SMTP_USER`, `SMTP_PASSWORD`, `ALERT_EMAIL_TO` - Email alerts
- `SLACK_WEBHOOK_URL` - Slack alerts

## Troubleshooting

```bash
# Check Python version
python --version  # Should be 3.9+

# Verify dependencies
pip list | grep -E "streamlit|litellm|langfuse|prometheus"

# Test API connection
python -c "from backend import generate_response; print(generate_response('test', [], 0.0))"

# View recent logs (with rotation)
tail -f logs/chatbot.log

# Test Prometheus endpoint
curl http://localhost:9090/metrics

# Check circuit breaker state
grep "circuit" logs/chatbot.log | tail -10

# Check rate limiting
grep -i "rate" logs/chatbot.log | tail -10

# Check disk space for metrics and logs
du -sh metrics/ logs/
```

## Deployment Checklist

- [ ] Copy `.env.example` to `.env` and fill in values
- [ ] Test locally: `streamlit run app.py`
- [ ] Verify metrics are being logged
- [ ] Test dashboard: `cd monitoring && streamlit run dashboard.py`
- [ ] Configure alerts (email or Slack)
- [ ] Run tests: `pytest tests/ -v`
- [ ] Set up alert cron job (if self-hosting)
- [ ] Configure metrics backup/rotation
- [ ] Document custom configurations
- [ ] Set up monitoring dashboard access

## Common Issues

**"No metrics found"**
→ Use the chatbot first to generate requests

**"GEMINI_API_KEY not found"**
→ Create .env file from .env.example

**"RateLimitError"**
→ Wait a moment, automatic retries are configured

**"Circuit breaker opened"**
→ Service is experiencing failures, wait for recovery or check logs

**Dashboard empty**
→ Check metrics/requests.jsonl exists and has data

**Alerts not sending**
→ Verify SMTP/Slack credentials, check cooldown period

**Prometheus metrics not available**
→ Check if prometheus-client is installed: `pip list | grep prometheus`

**Logs growing too large**
→ Automatic rotation at 10MB, check logs/ directory for rotated files

**Rate limiting too aggressive**
→ Increase `RATE_LIMIT_CALLS` in .env
