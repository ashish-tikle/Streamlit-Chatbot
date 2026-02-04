# Minimal CI/CD for Streamlit Chatbot with LiteLLM + Langfuse

## 🔄 Deployment Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEVELOPER WORKFLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  Local Dev                 GitHub                    Streamlit Cloud
  ─────────                 ──────                    ───────────────

┌─────────┐              ┌──────────┐
│  Code   │──git push──▶ │   PR     │
│ Changes │              │  Branch  │
└─────────┘              └──────────┘
                              │
                              │ triggers
                              ▼
                         ┌──────────┐
                         │  GitHub  │
                         │ Actions  │
                         │   CI     │
                         └──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
    ┌──────┐            ┌─────────┐          ┌─────────┐
    │ Lint │            │  Tests  │          │  Smoke  │
    │ruff  │            │ pytest  │          │  Test   │
    │mypy  │            │ + cov   │          │Streamlit│
    └──────┘            └─────────┘          └─────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                         ✅ All Pass
                              │
                        ┌──────────┐
                        │  Review  │
                        │  Approve │
                        └──────────┘
                              │
                         Merge to main
                              │
                              ▼
                      ┌───────────────┐
                      │  Streamlit    │◀──Watches branch 'main'
                      │  Cloud        │   Auto-detects changes
                      │               │
                      │  ┌─────────┐  │
                      │  │ Staging │  │  branch: staging
                      │  │   App   │  │  LANGFUSE_TRACING_ENVIRONMENT=staging
                      │  └─────────┘  │
                      │               │
                      │  ┌─────────┐  │
                      │  │  Prod   │  │  branch: main
                      │  │   App   │  │  LANGFUSE_TRACING_ENVIRONMENT=production
                      │  └─────────┘  │
                      └───────────────┘
                              │
                              ▼
                      ┌───────────────┐
                      │   Langfuse    │
                      │   Dashboard   │
                      │               │
                      │  Filter by:   │
                      │  - staging    │
                      │  - production │
                      └───────────────┘
```

---

## 📊 Environment Variable Matrix

| Variable | Local Dev | CI (GitHub Actions) | Streamlit Cloud (Staging) | Streamlit Cloud (Prod) |
|----------|-----------|---------------------|---------------------------|------------------------|
| **API Configuration** |
| `GEMINI_API_KEY` | `.env` file | ❌ Not set (dummy) | ✅ Streamlit Secrets | ✅ Streamlit Secrets |
| `GOOGLE_GEMINI_BASE_URL` | `.env` file | `https://llm.lingarogroup.com` | ✅ Streamlit Secrets | ✅ Streamlit Secrets |
| `LLM_PROVIDER` | `.env` / default | `openai` | ✅ Streamlit Secrets | ✅ Streamlit Secrets |
| `BASE_MODEL_ID` | `.env` / default | `gemini-3-flash` | ✅ Streamlit Secrets | ✅ Streamlit Secrets |
| **Langfuse Observability** |
| `LANGFUSE_PUBLIC_KEY` | `.env` file | `pk-lf-test-dummy` | ✅ Streamlit Secrets (staging project) | ✅ Streamlit Secrets (prod project) |
| `LANGFUSE_SECRET_KEY` | `.env` file | `sk-lf-test-dummy` | ✅ Streamlit Secrets (staging project) | ✅ Streamlit Secrets (prod project) |
| `LANGFUSE_HOST` | `.env` / default | `https://cloud.langfuse.com` | ✅ Streamlit Secrets | ✅ Streamlit Secrets |
| `ENVIRONMENT` | `development` | `ci` | **`staging`** | **`production`** |
| `ENABLE_LANGFUSE` | `true` | `false` (CI tests only) | `true` | `true` |
| **Optional** |
| `ENABLE_PII_REDACTION` | `true` | `true` | ✅ `true` | ✅ `true` |
| `LITELLM_LOGGING` | `false` | `false` | `false` | `false` |

### 🔑 Key Differences by Environment

**Local Development:**
- All secrets in `.env` (gitignored)
- `ENVIRONMENT=development`
- Full logging for debugging

**CI (GitHub Actions):**
- **NO real API keys** (uses dummy values)
- Tests run with `ENABLE_LANGFUSE=false`
- Smoke tests verify imports and config validation only
- Security scan checks for hardcoded secrets

**Streamlit Cloud - Staging:**
- Separate Langfuse project for staging traces
- `ENVIRONMENT=staging` → traces tagged accordingly
- Can test risky changes before production

**Streamlit Cloud - Production:**
- Production Langfuse project
- `ENVIRONMENT=production` → traces tagged accordingly
- Branch protection ensures only reviewed code deploys

---

## 🏗️ CI/CD Architecture

### **CI Pipeline (`.github/workflows/ci.yml`)**

Already implemented with 5 jobs:

1. **Lint** (`ruff` + `mypy`)
   - Fast feedback on code quality
   - Non-blocking initially (warnings only)

2. **Unit Tests** (`pytest` + coverage)
   - Tests backend logic without API calls
   - Coverage report to Codecov

3. **Smoke Tests**
   - Import validation
   - Config validation
   - Streamlit health check (headless mode)

4. **Security Scan**
   - Check for hardcoded API keys
   - Verify `.env` is gitignored
   - Verify `.env.example` exists

5. **Dependency Check**
   - Verify `requirements.txt` is valid
   - Check for pinned versions

**Runtime:** ~3-5 minutes per PR

### **CD Pipeline (Streamlit Cloud)**

**How Auto-Redeploy Works:**

1. **Initial Setup:**
   - Go to https://share.streamlit.io → "New app"
   - Connect GitHub repository
   - Select branch (`main` or `staging`)
   - Specify entrypoint (`app.py`)
   - Streamlit Cloud creates a webhook on your GitHub repo

2. **Auto-Redeploy Mechanism:**
   ```
   GitHub Push → Webhook → Streamlit Cloud
                              ↓
                         git pull
                              ↓
                    pip install -r requirements.txt
                              ↓
                      streamlit run app.py
                              ↓
                         App Live ✅
   ```

3. **Why This Works:**
   - Streamlit Cloud monitors specific branch
   - On every push, redeploys automatically (~2-3 min)
   - Zero configuration deployment
   - Free SSL certificate included
   - CDN-backed for global performance

---

## 🔐 Secrets Management

### **Why Streamlit Cloud Secrets UI?**

**Technical Reasons:**
1. **No `.env` in Git:** Streamlit Cloud doesn't have access to your `.env` file (correctly gitignored)
2. **Runtime Injection:** Secrets are injected as environment variables at runtime
3. **Isolation:** Each app deployment has separate secrets (staging ≠ production)
4. **No Dockerfile Needed:** Streamlit Cloud handles environment setup automatically

**Security Reasons:**
1. **Encrypted at Rest:** Secrets stored in encrypted cloud vault
2. **Never Logged:** Streamlit redacts secrets from logs automatically
3. **Auditable:** Changes to secrets are logged
4. **Role-Based Access:** Only app owners can view/edit secrets

**Format in Streamlit Secrets (TOML):**
```toml
# Settings → Secrets in Streamlit Cloud Dashboard

GEMINI_API_KEY = "sk-your-actual-key-here"
GOOGLE_GEMINI_BASE_URL = "https://llm.lingarogroup.com"
LLM_PROVIDER = "openai"
BASE_MODEL_ID = "gemini-3-flash"

LANGFUSE_PUBLIC_KEY = "pk-lf-production-key"
LANGFUSE_SECRET_KEY = "sk-lf-production-key"
LANGFUSE_HOST = "https://cloud.langfuse.com"
ENVIRONMENT = "production"
ENABLE_PII_REDACTION = "true"
```

**Code Access (already implemented in `backend.py`):**
```python
def _get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Read config in priority order:
    1) st.secrets (Streamlit Cloud)  # Automatically works!
    2) environment variable
    """
    val = os.getenv(key, default)
    return val.strip() if isinstance(val, (str, bytes)) else val
```

Streamlit automatically loads TOML secrets into `os.environ` - no code changes needed!

---

## ⚠️ Risk Assessment & Mitigation

### **Security Risks**

| Risk | Severity | Mitigation (Current) | Status |
|------|----------|---------------------|--------|
| **Hardcoded API keys in code** | 🔴 CRITICAL | Security scan in CI checks for `sk-*` patterns | ✅ Protected |
| **`.env` committed to Git** | 🔴 CRITICAL | `.gitignore` excludes `.env`, CI verifies | ✅ Protected |
| **Secrets in logs** | 🟡 HIGH | `litellm.suppress_debug_info = True`, PII redaction | ✅ Protected |
| **PII in Langfuse traces** | 🟡 HIGH | `ENABLE_PII_REDACTION=true` by default | ✅ Protected |
| **Unreviewed code to prod** | 🟡 HIGH | Branch protection (require PR approval) | ⚠️ Manual setup |
| **Staging/prod trace mixing** | 🟢 MEDIUM | `ENVIRONMENT` tags separate traces | ✅ Protected |
| **Missing environment validation** | 🟢 MEDIUM | `_validate_env()` checks on startup | ✅ Protected |

### **PII Redaction Details**

**Current Implementation (`backend.py:69-88`):**
```python
def redact_pii(text: str, redact_enabled: bool = True) -> str:
    """Redact personally identifiable information from text for privacy."""
    if not redact_enabled or not text:
        return text
    
    # Email addresses → [EMAIL_REDACTED]
    # Phone numbers → [PHONE_REDACTED]
    # SSN → [SSN_REDACTED]
    # Credit cards → [CC_REDACTED]
    # API keys/tokens → [TOKEN_REDACTED]
```

**What's Redacted:**
- ✅ Email addresses
- ✅ Phone numbers (multiple formats)
- ✅ Social Security Numbers
- ✅ Credit card numbers
- ✅ API keys starting with `sk-`, `pk-`, `token-`

**What's NOT Redacted (Langfuse Limitation):**
- ❌ Input/output text (Langfuse 2.12.0 doesn't support input/output fields)
- ✅ Only logs preview text (~50 chars) after redaction
- ✅ Full requests never logged to disk

**Recommendation:** For sensitive data, consider:
1. User consent before processing PII
2. Additional redaction patterns for your domain
3. Upgrade to Langfuse 3.x when LiteLLM compatibility is resolved

---

## 🚀 Deployment Checklist

### **One-Time Setup**

- [x] ✅ CI workflow created (`.github/workflows/ci.yml`)
- [x] ✅ Smoke tests created (`tests/test_smoke.py`)
- [x] ✅ `pyproject.toml` configured
- [x] ✅ `.python-version` added
- [x] ✅ `.streamlit/config.toml` created
- [ ] ⬜ Create GitHub repository (if not exists)
- [ ] ⬜ Push code to GitHub
- [ ] ⬜ Create Streamlit Cloud account
- [ ] ⬜ Create separate Langfuse projects (staging, production)

### **Per-Environment Setup**

**Staging App:**
- [ ] ⬜ Deploy new app on Streamlit Cloud
- [ ] ⬜ Select branch: `staging`
- [ ] ⬜ Add secrets with `ENVIRONMENT=staging`
- [ ] ⬜ Add staging Langfuse project keys
- [ ] ⬜ Verify deployment works
- [ ] ⬜ Check traces in Langfuse with `staging` tag

**Production App:**
- [ ] ⬜ Deploy new app on Streamlit Cloud
- [ ] ⬜ Select branch: `main`
- [ ] ⬜ Add secrets with `ENVIRONMENT=production`
- [ ] ⬜ Add production Langfuse project keys
- [ ] ⬜ Enable branch protection on GitHub
- [ ] ⬜ Verify deployment works
- [ ] ⬜ Check traces in Langfuse with `production` tag

### **Ongoing Operations**

- [ ] ⬜ Monitor Langfuse dashboard daily
- [ ] ⬜ Review CI failures on PRs
- [ ] ⬜ Test changes on staging before merging to main
- [ ] ⬜ Rotate API keys quarterly
- [ ] ⬜ Review PII redaction logs monthly

---

## 📝 Example: Full Deployment Flow

```bash
# 1. Developer creates feature branch
git checkout -b feature/new-prompt

# 2. Make changes to prompts/system_prompt.txt
vim prompts/system_prompt.txt

# 3. Test locally
streamlit run app.py
# Verify in Langfuse → traces tagged with "development"

# 4. Commit and push
git add prompts/system_prompt.txt
git commit -m "feat: Update system prompt for better responses"
git push origin feature/new-prompt

# 5. Create PR on GitHub
# GitHub Actions CI automatically runs:
#   - ✅ Lint passes
#   - ✅ Tests pass
#   - ✅ Smoke tests pass
#   - ✅ Security scan passes

# 6. Team reviews PR
# Approve and merge to main

# 7. Streamlit Cloud detects push to main
# Auto-redeploys in ~2 minutes

# 8. Verify in production
# https://yourapp.streamlit.app
# Check Langfuse → traces now tagged with "production"
```

---

## 🎯 Why This Minimal Setup Works

### **Advantages:**

1. **Zero Infrastructure Management**
   - No Docker, Kubernetes, or cloud VMs
   - Streamlit Cloud handles everything

2. **Fast Feedback Loop**
   - CI runs in 3-5 minutes
   - Deploy in 2-3 minutes
   - Total: ~8 minutes from commit to live

3. **Free Tier Sufficient**
   - Streamlit Cloud: Free for public repos
   - Langfuse: Free tier (50K traces/month)
   - GitHub Actions: 2000 minutes/month free

4. **Environment Separation**
   - Langfuse tags prevent trace mixing
   - Separate apps for staging/prod
   - Easy rollback (revert Git commit)

5. **Security Built-In**
   - No secrets in Git
   - Automatic HTTPS
   - PII redaction by default

### **Trade-offs:**

1. **Limited Resources**
   - 1 GB RAM on free tier
   - May need upgrade for high traffic

2. **Public URL Required**
   - Custom domain needs paid tier
   - Authentication needs custom implementation

3. **Streamlit-Only**
   - Can't deploy non-Streamlit apps
   - Locked into Streamlit Cloud ecosystem

---

## 🔗 References

**Already Implemented:**
- `.github/workflows/ci.yml` - Full CI pipeline
- `tests/test_smoke.py` - Smoke test suite
- `backend.py:25-30` - `_HAS_STREAMLIT` check
- `backend.py:69-88` - PII redaction
- `backend.py:456-471` - Langfuse environment tagging
- `.env.example` - Template with `ENVIRONMENT` variable

**Next Steps:** See `CI_CD_SETUP.md` for deployment instructions.

**Monitoring:** Langfuse dashboard at https://cloud.langfuse.com with environment filtering.

---

## 💡 Pro Tips

1. **Test on Staging First:** Always merge to `staging` branch, verify, then merge to `main`
2. **Monitor Costs:** Check Langfuse usage to avoid exceeding free tier
3. **Branch Protection:** Enable on `main` to prevent accidental direct pushes
4. **Secrets Rotation:** Update Streamlit Cloud secrets, not `.env` files
5. **Incident Response:** Streamlit Cloud allows instant rollback to previous deployment

All components are ready to deploy! 🚀
