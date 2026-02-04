# 🔌 External Services Integration Plan

**Project:** Streamlit Chatbot with Monitoring  
**Date:** February 4, 2026  
**Status:** Pre-Production Integration

---

## 📋 External Service Dependencies

### ✅ **Required Services** (Must Have)

#### 1. **Lingaro GenAI Proxy (Gemini API)**
- **Purpose**: LLM inference via Google Gemini models
- **Type**: Third-party API
- **Endpoint**: `https://llm.lingarogroup.com`
- **Authentication**: API Key (starts with `sk-`)
- **Cost**: Pay-per-token (see model pricing)
- **Status**: ⚠️ REQUIRED - App won't work without this

#### 2. **Python Package Dependencies**
- **Purpose**: Core application libraries
- **Type**: PyPI packages
- **Authentication**: None (public packages)
- **Cost**: Free
- **Status**: ✅ Listed in requirements.txt

---

### 🔧 **Optional Services** (Enhances Features)

#### 3. **Langfuse** (Distributed Tracing)
- **Purpose**: Request tracing, observability, debugging
- **Type**: SaaS or Self-Hosted
- **Options**:
  - **SaaS**: `https://cloud.langfuse.com` (Free tier: 50k events/month)
  - **Self-Hosted**: Docker deployment (free, unlimited)
- **Authentication**: Public Key + Secret Key
- **Cost**: 
  - Free: 50k events/month
  - Pro: $59/month for 500k events
  - Enterprise: Custom pricing
- **Status**: 🟡 OPTIONAL - Fallback to OTEL or logs

#### 4. **Prometheus** (Metrics Storage)
- **Purpose**: Time-series metrics database
- **Type**: Self-Hosted (open source)
- **Options**:
  - Local installation
  - Docker container
  - Cloud provider (AWS, GCP, Azure)
- **Authentication**: None (default) or Basic Auth
- **Cost**: Free (self-hosted)
- **Status**: 🟡 OPTIONAL - Fallback to local JSONL files

#### 5. **OpenTelemetry Collector** (Telemetry Export)
- **Purpose**: Unified telemetry collection (fallback from Langfuse)
- **Type**: Self-Hosted (open source)
- **Options**:
  - Local installation
  - Docker container
  - Sidecar container (Kubernetes)
- **Authentication**: None (default)
- **Cost**: Free
- **Status**: 🟡 OPTIONAL - Only if Langfuse disabled

#### 6. **SMTP Server** (Email Alerts)
- **Purpose**: Send alert emails for errors/thresholds
- **Type**: Email service
- **Options**:
  - Gmail SMTP (`smtp.gmail.com:587`)
  - SendGrid (`smtp.sendgrid.net:587`)
  - AWS SES (`email-smtp.region.amazonaws.com:587`)
  - Office 365 (`smtp.office365.com:587`)
- **Authentication**: Username + Password (or App Password for Gmail)
- **Cost**: 
  - Gmail: Free (with limits)
  - SendGrid: Free tier 100 emails/day
  - AWS SES: $0.10 per 1000 emails
- **Status**: 🟡 OPTIONAL - For alerting only

#### 7. **Slack** (Webhook Alerts)
- **Purpose**: Send alert messages to Slack channels
- **Type**: Webhook integration
- **Options**: Slack Incoming Webhooks
- **Authentication**: Webhook URL (secret token embedded)
- **Cost**: Free
- **Status**: 🟡 OPTIONAL - Alternative to email alerts

#### 8. **Grafana** (Visualization)
- **Purpose**: Advanced metrics dashboards
- **Type**: Self-Hosted or Cloud
- **Options**:
  - Self-hosted (Docker)
  - Grafana Cloud (free tier)
- **Authentication**: Username + Password
- **Cost**: 
  - Self-hosted: Free
  - Cloud: Free tier (10k metrics)
- **Status**: 🟢 NICE-TO-HAVE - Built-in Streamlit dashboard exists

---

## 🗺️ Integration Roadmap

### **Phase 1: Minimum Viable Setup** ⏱️ 15 minutes

**Goal**: Get the chatbot working with basic functionality

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Core Chatbot Only                            │
├─────────────────────────────────────────────────────────┤
│  ✅ Lingaro GenAI Proxy (Gemini API) - REQUIRED        │
│  ✅ Python Dependencies                                 │
│  ✅ Local File Storage (JSONL)                          │
└─────────────────────────────────────────────────────────┘
```

**Steps:**
1. ✅ Install Python dependencies
2. ✅ Get Gemini API key from Lingaro
3. ✅ Configure `.env` file
4. ✅ Test connection
5. ✅ Verify chatbot works

**What Works:**
- ✅ Chat interface
- ✅ LLM responses
- ✅ Basic logging to files
- ✅ Metrics saved to JSONL
- ✅ Monitoring dashboard (using demo data)

**What Doesn't:**
- ❌ Real-time metrics in Prometheus
- ❌ Distributed tracing
- ❌ Email/Slack alerts

---

### **Phase 2: Observability Stack** ⏱️ 30 minutes

**Goal**: Add monitoring and tracing for production readiness

```
┌─────────────────────────────────────────────────────────┐
│  Phase 2: + Monitoring & Tracing                        │
├─────────────────────────────────────────────────────────┤
│  ✅ Phase 1 services                                    │
│  ✅ Langfuse (SaaS - easiest)                           │
│  ✅ Prometheus (local Docker)                           │
└─────────────────────────────────────────────────────────┘
```

**Steps:**
1. ✅ Sign up for Langfuse Cloud (free tier)
2. ✅ Get Langfuse keys (public + secret)
3. ✅ Start Prometheus with Docker
4. ✅ Update `.env` with tracing config
5. ✅ Test monitoring dashboard

**What Works:**
- ✅ Everything from Phase 1
- ✅ Distributed tracing in Langfuse UI
- ✅ Real-time metrics in Prometheus
- ✅ Monitoring dashboard with live data
- ✅ Performance analysis

**What Doesn't:**
- ❌ Automated alerts

---

### **Phase 3: Alerting** ⏱️ 20 minutes

**Goal**: Get notified when things go wrong

```
┌─────────────────────────────────────────────────────────┐
│  Phase 3: + Alerting                                    │
├─────────────────────────────────────────────────────────┤
│  ✅ Phase 2 services                                    │
│  ✅ SMTP (Gmail or SendGrid)                            │
│  ✅ Slack Webhook (optional)                            │
└─────────────────────────────────────────────────────────┘
```

**Steps:**
1. ✅ Set up Gmail App Password OR SendGrid account
2. ✅ Create Slack Incoming Webhook (optional)
3. ✅ Update `.env` with alert config
4. ✅ Test alert script manually
5. ✅ Schedule alert checks (cron/Task Scheduler)

**What Works:**
- ✅ Everything from Phase 2
- ✅ Email alerts on errors/latency/cost
- ✅ Slack notifications
- ✅ Configurable thresholds

---

### **Phase 4: Production Hardening** ⏱️ 1-2 hours

**Goal**: Production-ready deployment

```
┌─────────────────────────────────────────────────────────┐
│  Phase 4: Production Deployment                         │
├─────────────────────────────────────────────────────────┤
│  ✅ Phase 3 services                                    │
│  ✅ Grafana (optional - better dashboards)              │
│  ✅ Prometheus persistent storage                       │
│  ✅ Log aggregation (optional)                          │
│  ✅ SSL/TLS for endpoints                               │
└─────────────────────────────────────────────────────────┘
```

**Steps:**
1. ✅ Configure Prometheus retention and storage
2. ✅ Set up Grafana dashboards (optional)
3. ✅ Implement SSL/TLS for public endpoints
4. ✅ Configure backup/restore for metrics
5. ✅ Set up monitoring for monitors (meta-monitoring)

---

## 📝 Step-by-Step Integration Guide

### **STEP 1: Local Environment Setup** (Phase 1)

#### 1.1 Install Dependencies

```bash
cd c:\streamlit-chatbot

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install packages
pip install -r requirements.txt
```

**Verify Installation:**
```bash
python test_monitor.py
```

**Expected Output:**
```
✅ PASSED: Imports
✅ PASSED: Demo Data
✅ PASSED: Monitoring Page
✅ PASSED: Directories
```

---

#### 1.2 Configure Gemini API (REQUIRED)

**Option A: Lingaro Proxy (Recommended)**

1. **Get API Key** from Lingaro team:
   - Contact: Your Lingaro account manager
   - Format: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Endpoint: `https://llm.lingarogroup.com`

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env`:**
   ```bash
   GEMINI_API_KEY=sk-your-actual-key-here
   GOOGLE_GEMINI_BASE_URL=https://llm.lingarogroup.com
   LLM_PROVIDER=openai
   BASE_MODEL_ID=gemini-3-flash
   ```

**Option B: Direct Google AI (Alternative)**

If not using Lingaro proxy:

```bash
# Get key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your-google-ai-api-key
GOOGLE_GEMINI_BASE_URL=https://generativelanguage.googleapis.com
LLM_PROVIDER=gemini
BASE_MODEL_ID=gemini-1.5-flash
```

---

#### 1.3 Test Basic Functionality

```bash
# Start the app
streamlit run app.py
```

**Test Checklist:**
- [ ] App opens in browser (http://localhost:8501)
- [ ] No connection errors in sidebar
- [ ] Can send a message
- [ ] Receives response from Gemini
- [ ] Monitor page shows demo data (http://localhost:8501/2_Monitor)

**If Errors:**
- Check API key is correct
- Verify internet connection
- Check endpoint URL
- Review logs: `type logs\chatbot.log` (Windows) or `cat logs/chatbot.log` (Linux/Mac)

---

### **STEP 2: Add Tracing** (Phase 2a)

#### 2.1 Sign Up for Langfuse (5 minutes)

**Option A: SaaS (Easiest)**

1. **Visit:** https://cloud.langfuse.com
2. **Sign up** with Google/GitHub
3. **Create project:** "chatbot-production"
4. **Get API keys:**
   - Go to Settings → API Keys
   - Copy `Public Key` (starts with `pk-lf-`)
   - Copy `Secret Key` (starts with `sk-lf-`)

**Option B: Self-Hosted (Advanced)**

```bash
# Using Docker Compose
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker-compose up -d

# Wait 30 seconds for startup
# Access: http://localhost:3000
# Create account, then get API keys
```

---

#### 2.2 Configure Tracing

**Edit `.env`:**
```bash
# Langfuse Configuration
ENABLE_LANGFUSE=true
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
LANGFUSE_HOST=https://cloud.langfuse.com

# Privacy
ENABLE_PII_REDACTION=true
```

**Restart app:**
```bash
# Stop (Ctrl+C), then restart
streamlit run app.py
```

---

#### 2.3 Verify Tracing

1. **Send test messages** in chatbot
2. **Go to Langfuse UI:** https://cloud.langfuse.com
3. **Check "Traces" tab** - should see new entries
4. **Click a trace** to see:
   - Request ID
   - User/Session IDs
   - Model name
   - Latency
   - Token counts
   - Cost
   - Full request/response (PII redacted)

**If Not Working:**
- Check Langfuse keys are correct
- Verify `ENABLE_LANGFUSE=true`
- Check logs for "Langfuse" errors
- Try disabling: `ENABLE_LANGFUSE=false` (will fallback to OTEL console)

---

### **STEP 3: Add Prometheus** (Phase 2b)

#### 3.1 Install Prometheus (10 minutes)

**Option A: Docker (Easiest)**

```bash
# Pull Prometheus image
docker pull prom/prometheus

# Start Prometheus with included config
docker run -d \
  --name prometheus \
  -p 9091:9090 \
  -v %cd%\prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Verify
curl http://localhost:9091
```

**Option B: Native Install**

**Windows:**
```bash
# Download from: https://prometheus.io/download/
# Extract to C:\prometheus
cd C:\prometheus
.\prometheus.exe --config.file=prometheus.yml
```

**macOS:**
```bash
brew install prometheus
prometheus --config.file=prometheus.yml
```

**Linux:**
```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*
./prometheus --config.file=prometheus.yml
```

---

#### 3.2 Enable Prometheus Metrics

**Edit `.env`:**
```bash
# Prometheus Configuration
LITELLM_PROMETHEUS_METRICS=true
PROMETHEUS_PORT=9090
```

**Restart app:**
```bash
streamlit run app.py
```

---

#### 3.3 Verify Prometheus

1. **Check metrics endpoint:**
   ```bash
   curl http://localhost:9090/metrics
   ```
   Should see metrics like:
   ```
   chatbot_requests_total 25
   chatbot_tokens_total 3600
   chatbot_cost_usd_total 0.0832
   ```

2. **Check Prometheus UI:**
   - Open: http://localhost:9091
   - Go to: Graph tab
   - Query: `chatbot_requests_total`
   - Click "Execute"
   - Should see data

3. **Check Monitor dashboard:**
   - In app, go to Monitor page
   - Sidebar: Select "Auto (Prometheus → Local)"
   - Should see: "✅ Connected to Prometheus"

---

### **STEP 4: Add Alerting** (Phase 3)

#### 4.1 Set Up Email Alerts (10 minutes)

**Option A: Gmail (Personal Use)**

1. **Enable 2FA** on Gmail account
2. **Create App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Windows Computer" (or Other)
   - Click "Generate"
   - Copy 16-character password

3. **Edit `.env`:**
   ```bash
   # Email Alert Configuration
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   ALERT_EMAIL_FROM=your-email@gmail.com
   ALERT_EMAIL_TO=alerts@yourcompany.com
   
   # Alert Thresholds
   ALERT_ERROR_RATE_THRESHOLD=10.0       # Alert if error rate > 10%
   ALERT_LATENCY_P95_THRESHOLD=5.0       # Alert if P95 latency > 5s
   ALERT_COST_THRESHOLD=1.0              # Alert if hourly cost > $1
   ALERT_COOLDOWN_HOURS=1                # Don't spam alerts (1 hour cooldown)
   ```

**Option B: SendGrid (Production Use)**

1. **Sign up:** https://sendgrid.com (free tier: 100 emails/day)
2. **Create API Key:**
   - Settings → API Keys → Create API Key
   - Name: "chatbot-alerts"
   - Permissions: "Mail Send" (Full Access)
   - Copy API key

3. **Edit `.env`:**
   ```bash
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=your-sendgrid-api-key-here
   ALERT_EMAIL_FROM=noreply@yourdomain.com
   ALERT_EMAIL_TO=alerts@yourcompany.com
   ```

---

#### 4.2 Set Up Slack Alerts (Optional, 5 minutes)

1. **Create Incoming Webhook:**
   - Go to: https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name: "Chatbot Alerts"
   - Pick workspace
   - Go to "Incoming Webhooks" → Enable
   - Click "Add New Webhook to Workspace"
   - Select channel (e.g., #alerts)
   - Copy webhook URL

2. **Edit `.env`:**
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

---

#### 4.3 Test Alerts

**Manual Test:**
```bash
python monitoring/alerts.py
```

**Expected Output:**
```
Checking metrics for alerts...
✅ Error rate OK: 8.0% (threshold: 10.0%)
⚠️  P95 latency high: 5.2s (threshold: 5.0s)
📧 Alert email sent
💬 Slack notification sent
```

**Schedule Alerts:**

**Windows (Task Scheduler):**
```powershell
# Run every 15 minutes
schtasks /create /tn "Chatbot Alerts" /tr "python c:\streamlit-chatbot\monitoring\alerts.py" /sc minute /mo 15
```

**Linux/Mac (Cron):**
```bash
# Add to crontab
crontab -e

# Add line:
*/15 * * * * cd /path/to/streamlit-chatbot && python monitoring/alerts.py
```

---

### **STEP 5: Local Testing** (Phase 1-3 Complete)

#### 5.1 Full Integration Test

**Test Matrix:**

| Component | Test | Expected Result |
|-----------|------|-----------------|
| **Chatbot** | Send message | Receives response |
| **Logging** | Check `logs/chatbot.log` | New log entries |
| **Metrics** | Check `metrics/requests.jsonl` | New request logged |
| **Prometheus** | Visit http://localhost:9091 | Metrics visible |
| **Langfuse** | Visit cloud.langfuse.com | Trace visible |
| **Monitor** | Check dashboard | Live data shows |
| **Alerts** | Run `python monitoring/alerts.py` | Email/Slack sent |

---

#### 5.2 Load Test (Optional)

```bash
# Install locust
pip install locust

# Create test script: locustfile.py
# (See example below)

# Run load test
locust -f locustfile.py --host=http://localhost:8501
```

**Example `locustfile.py`:**
```python
from locust import HttpUser, task, between

class ChatbotUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def send_message(self):
        self.client.post("/api/chat", json={
            "message": "What is machine learning?",
            "temperature": 0.7
        })
```

**Monitor during load test:**
- Watch dashboard for latency spikes
- Check Prometheus for request rates
- Verify Langfuse traces being created
- Ensure no errors in logs

---

### **STEP 6: Production Deployment** (Phase 4)

#### 6.1 Pre-Production Checklist

**Security:**
- [ ] All secrets in environment variables (not hardcoded)
- [ ] `.env` file in `.gitignore`
- [ ] PII redaction enabled (`ENABLE_PII_REDACTION=true`)
- [ ] API keys rotated from test keys
- [ ] Prometheus endpoint secured (if public)
- [ ] SSL/TLS for all external endpoints

**Performance:**
- [ ] Log rotation configured (10MB, 5 backups)
- [ ] Prometheus retention set (30 days)
- [ ] Circuit breaker enabled
- [ ] Rate limiting configured
- [ ] Timeout settings reasonable (30s)

**Monitoring:**
- [ ] Langfuse tracing working
- [ ] Prometheus scraping metrics
- [ ] Monitor dashboard accessible
- [ ] Alerts configured and tested
- [ ] Alert cooldown set (avoid spam)

**Documentation:**
- [ ] Runbook created for incidents
- [ ] Alert thresholds documented
- [ ] Contact info for on-call updated

---

#### 6.2 Deployment Options

**Option A: Streamlit Cloud (Easiest)**

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for production"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud:**
   - Go to: https://share.streamlit.io
   - Connect GitHub repo
   - Add secrets (Settings → Secrets):
     ```toml
     GEMINI_API_KEY = "sk-..."
     LANGFUSE_PUBLIC_KEY = "pk-lf-..."
     LANGFUSE_SECRET_KEY = "sk-lf-..."
     # ... other secrets
     ```

3. **Deploy!**

**Option B: Docker (Self-Hosted)**

```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

```bash
# Build
docker build -t chatbot .

# Run
docker run -d \
  --name chatbot \
  -p 8501:8501 \
  --env-file .env \
  chatbot
```

**Option C: Kubernetes (Enterprise)**

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatbot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chatbot
  template:
    metadata:
      labels:
        app: chatbot
    spec:
      containers:
      - name: chatbot
        image: your-registry/chatbot:latest
        ports:
        - containerPort: 8501
        envFrom:
        - secretRef:
            name: chatbot-secrets
```

---

#### 6.3 Post-Deployment Verification

**Within 5 Minutes:**
- [ ] App accessible at production URL
- [ ] Can send messages and receive responses
- [ ] No errors in logs
- [ ] Metrics appearing in Prometheus
- [ ] Traces appearing in Langfuse

**Within 1 Hour:**
- [ ] Monitor dashboard shows production data
- [ ] Alert system triggers test (if threshold crossed)
- [ ] Email/Slack alerts received

**Within 24 Hours:**
- [ ] Review error rates (should be <5%)
- [ ] Check P95 latency (should be <3s)
- [ ] Verify cost tracking accuracy
- [ ] Analyze user feedback (if any)

---

#### 6.4 Rollback Plan

**If Issues:**

1. **Immediate:**
   ```bash
   # Stop new traffic
   # Revert to previous version
   git revert HEAD
   git push
   ```

2. **Disable Features:**
   ```bash
   # In production .env, disable problematic features:
   ENABLE_LANGFUSE=false
   LITELLM_PROMETHEUS_METRICS=false
   ```

3. **Emergency Shutdown:**
   ```bash
   # Stop all services
   docker-compose down
   # Or
   kubectl delete deployment chatbot
   ```

---

## 🔍 Service Connection Summary

```
┌────────────────────────────────────────────────────────────────┐
│                     Service Topology                           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│   User Browser                                                  │
│        │                                                        │
│        ├── HTTP ───▶ Streamlit App (localhost:8501)            │
│        │                    │                                   │
│        │                    ├── HTTPS ──▶ Gemini API           │
│        │                    │   (llm.lingarogroup.com)         │
│        │                    │   Auth: API Key                   │
│        │                    │                                   │
│        │                    ├── HTTPS ──▶ Langfuse             │
│        │                    │   (cloud.langfuse.com)           │
│        │                    │   Auth: PK + SK                   │
│        │                    │                                   │
│        │                    ├── HTTP ──▶ Prometheus             │
│        │                    │   (localhost:9090)               │
│        │                    │   Auth: None                      │
│        │                    │                                   │
│        │                    └── Local Files                     │
│        │                        • logs/chatbot.log             │
│        │                        • metrics/requests.jsonl       │
│        │                                                        │
│        └── HTTP ───▶ Monitor Dashboard (localhost:8501/2_Monitor)
│                            │                                    │
│                            ├── Query ──▶ Prometheus            │
│                            └── Read ──▶ Local Files            │
│                                                                 │
│   Alert Script (cron)                                           │
│        │                                                        │
│        ├── SMTP ──▶ Email Server                               │
│        │   (smtp.gmail.com:587)                                │
│        │   Auth: Username + App Password                       │
│        │                                                        │
│        └── HTTPS ──▶ Slack Webhook                             │
│            (hooks.slack.com)                                    │
│            Auth: Webhook URL (token embedded)                  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 Service Status Dashboard

| Service | Status | Priority | Fallback |
|---------|--------|----------|----------|
| **Gemini API** | 🔴 REQUIRED | P0 | None - app won't work |
| **Python Packages** | 🔴 REQUIRED | P0 | None - must install |
| **Local Storage** | 🟢 ACTIVE | P1 | None - always works |
| **Langfuse** | 🟡 OPTIONAL | P2 | OTEL console logs |
| **Prometheus** | 🟡 OPTIONAL | P2 | Local JSONL files |
| **SMTP/Slack** | 🟢 OPTIONAL | P3 | Manual monitoring |
| **Grafana** | ⚪ OPTIONAL | P4 | Built-in dashboard |

---

## 💰 Cost Estimation

### Development (Local Testing)
- **Gemini API**: ~$0.01 - $0.10/day (50-500 requests)
- **Langfuse SaaS**: Free (under 50k events/month)
- **Prometheus**: Free (self-hosted)
- **SMTP (Gmail)**: Free
- **Slack**: Free
- **Total**: ~$0.01 - $0.10/day

### Production (1000 requests/day)
- **Gemini API**: ~$2 - $5/day ($60 - $150/month)
- **Langfuse SaaS**: Free or $59/month (if >50k events)
- **Prometheus**: ~$10/month (small VM)
- **SendGrid**: Free (under 100/day) or $15/month
- **Slack**: Free
- **Hosting**: $5 - $50/month (depends on platform)
- **Total**: ~$70 - $250/month

---

## 🚨 Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| **"API key invalid"** | Check `GEMINI_API_KEY` in `.env` |
| **"Connection refused"** | Check service is running (Prometheus, Langfuse) |
| **"Module not found"** | Run `pip install -r requirements.txt` |
| **"No traces in Langfuse"** | Check keys, verify `ENABLE_LANGFUSE=true` |
| **"Prometheus has no data"** | Check metrics endpoint: `curl localhost:9090/metrics` |
| **"Alerts not sending"** | Test SMTP: `python monitoring/alerts.py` |
| **"Dashboard shows demo data"** | Send real messages, click Refresh |

---

## ✅ Final Checklist

### Before Production:
- [ ] All dependencies installed
- [ ] Gemini API key configured and tested
- [ ] Langfuse tracing working
- [ ] Prometheus collecting metrics
- [ ] Monitoring dashboard shows live data
- [ ] Alerts configured and tested
- [ ] PII redaction enabled
- [ ] Logs rotating properly
- [ ] Load testing completed
- [ ] Rollback plan documented
- [ ] On-call contacts updated

### After Deployment:
- [ ] Monitor error rates (first hour)
- [ ] Check latency (first hour)
- [ ] Verify costs (first day)
- [ ] Review traces (first day)
- [ ] Analyze feedback (first week)
- [ ] Adjust thresholds if needed
- [ ] Document lessons learned

---

**Ready to Start?** → Begin with **STEP 1** above! 🚀
