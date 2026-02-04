# CI/CD Setup and Deployment Guide

## ✅ Completed Implementation

### Critical Fixes (P0)
- ✅ Fixed `_HAS_STREAMLIT` undefined variable bug in `backend.py`
- ✅ Added `.python-version` (3.12.1) for consistent Python versioning
- ✅ Added `ENVIRONMENT` variable to `.env.example`
- ✅ Added Langfuse environment tagging for trace separation

### CI/CD Infrastructure (P1)
- ✅ Created `.github/workflows/ci.yml` with:
  - Lint job (ruff, mypy)
  - Unit tests with coverage
  - Smoke tests (imports, config, Streamlit health)
  - Security scan (hardcoded secrets, .env check)
  - Dependency verification
- ✅ Created `tests/test_smoke.py` with comprehensive smoke tests
- ✅ Created `pyproject.toml` with tooling configuration
- ✅ Created `.streamlit/config.toml` for production settings

---

## 🚀 Deployment Instructions

### Stage 1: Enable GitHub Actions

1. **Push changes to GitHub:**
   ```powershell
   git add .github/ tests/test_smoke.py .python-version pyproject.toml .streamlit/
   git commit -m "feat: Add CI/CD pipeline and production configuration"
   git push origin main
   ```

2. **Verify CI workflow:**
   - Go to GitHub → Actions tab
   - CI pipeline should trigger automatically
   - All jobs should pass (lint may have warnings)

### Stage 2: Deploy to Streamlit Cloud

#### **Production Environment (main branch)**

1. **Go to Streamlit Cloud:**
   - Visit https://share.streamlit.io
   - Click "New app"
   - Connect your GitHub repository

2. **Configure deployment:**
   - Branch: `main`
   - Main file path: `app.py`
   - Python version: 3.12

3. **Add secrets** (Settings → Secrets):
   ```toml
   GEMINI_API_KEY = "sk-your-production-key"
   GOOGLE_GEMINI_BASE_URL = "https://llm.lingarogroup.com"
   LLM_PROVIDER = "openai"
   BASE_MODEL_ID = "gemini-3-flash"
   
   LANGFUSE_PUBLIC_KEY = "pk-lf-production-key"
   LANGFUSE_SECRET_KEY = "sk-lf-production-key"
   LANGFUSE_HOST = "https://cloud.langfuse.com"
   ENVIRONMENT = "production"
   ```

4. **Deploy:**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Access at `https://<username>-chatbot.streamlit.app`

#### **Staging Environment (optional)**

1. **Create staging branch:**
   ```powershell
   git checkout -b staging
   git push -u origin staging
   ```

2. **Deploy separate Streamlit app:**
   - Repeat above steps
   - Use different Langfuse project keys
   - Set `ENVIRONMENT = "staging"`
   - URL: `https://<username>-chatbot-staging.streamlit.app`

---

## 🔐 GitHub Branch Protection (Recommended)

1. **Go to repository Settings → Branches**
2. **Add branch protection rule for `main`:**
   - Require pull request reviews (1 reviewer)
   - Require status checks to pass:
     - ✅ lint
     - ✅ test
     - ✅ smoke-test
     - ✅ security
   - Do not allow bypassing

---

## 📊 Environment Separation

Your Langfuse traces are now tagged by environment:

- **Development**: Local testing with `ENVIRONMENT=development`
- **Staging**: Pre-prod testing with `ENVIRONMENT=staging`
- **Production**: Live app with `ENVIRONMENT=production`

Filter traces in Langfuse dashboard by environment tag.

---

## 🧪 Local Testing

### Run all tests:
```powershell
pytest tests/ -v
```

### Run only smoke tests:
```powershell
pytest tests/test_smoke.py -v
```

### Run with coverage:
```powershell
pytest tests/ -v --cov=backend --cov=app --cov-report=html
```

### Lint code:
```powershell
ruff check .
```

### Type check:
```powershell
mypy backend.py app.py --ignore-missing-imports
```

---

## 📝 Deployment Checklist

- [x] CI workflow configured
- [x] Smoke tests passing locally
- [x] `.python-version` added
- [x] `pyproject.toml` configured
- [x] `.streamlit/config.toml` created
- [ ] GitHub repository created/connected
- [ ] GitHub Actions enabled
- [ ] Streamlit Cloud account created
- [ ] Production secrets configured
- [ ] Branch protection enabled
- [ ] First deployment successful
- [ ] Monitor tab showing Langfuse data
- [ ] Environment tags visible in Langfuse

---

## 🔄 Deployment Workflow

```
Developer → PR → CI (lint/test/smoke) → Review → Merge → main
                                                           ↓
                                                    Streamlit Cloud
                                                    Auto-redeploy
```

---

## 📞 Support

- **CI failing?** Check `.github/workflows/ci.yml` logs
- **Deployment failing?** Check Streamlit Cloud logs
- **Missing secrets?** Verify in Streamlit Cloud Settings → Secrets
- **Langfuse not working?** Check `ENVIRONMENT` variable and API keys

---

## 🎉 What's Next?

### Optional Improvements (P2/P3):
1. Add `pre-commit` hooks for local validation
2. Enable strict `mypy` type checking gradually
3. Add integration tests with mock LLM responses
4. Set up Codecov for coverage tracking
5. Add performance benchmarks
6. Create Docker deployment option
7. Add monitoring alerts (Langfuse webhooks)

All P0 and P1 items are ✅ **COMPLETE** and ready for deployment!
