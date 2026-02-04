#  Streamlit Community Cloud Deployment Checklist

## Repository: streamlit-chatbot
## Target: https://share.streamlit.io

---

##  Pre-Deployment Verification

### 1. Confirm Entrypoint Path
- **File**: `app.py` (root directory) 
- **Location**: `c:\streamlit-chatbot\app.py`
- **Streamlit Cloud will auto-detect this file** 

### 2. Confirm Python Version
- **File**: `.python-version` contains `3.12.1` 
- **requirements.txt**: Up to date with pinned versions 
  - streamlit==1.30.0
  - litellm==1.49.7 (pinned for Langfuse 2.12.0 compatibility)
  - langfuse==2.12.0
  - All dependencies listed

**Note**: Streamlit Cloud automatically uses Python version from `.python-version` file.

---

##  Step-by-Step Deployment

### Step 1: Push Code to GitHub
```powershell
# Ensure all changes are committed
git status
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

** What triggers redeployment**: Any push to the watched branch (`main`) automatically redeploys the app.

---

### Step 2: Create App on Streamlit Community Cloud

** UI Actions (Streamlit Cloud Dashboard):**

1. Go to: https://share.streamlit.io
2. Sign in with GitHub account
3. Click: **"New app"** button
4. Select:
   - Repository: `your-username/streamlit-chatbot`
   - Branch: **`main`**  (auto-redeploy on push)
   - Main file path: `app.py` (auto-detected)
5. Click: **"Deploy"**

**Expected**: App deploys with errors (missing secrets) - normal initial state.

---

### Step 3: Configure Secrets

** UI Actions (Streamlit Cloud Dashboard):**

1. Navigate to: Your app   **Settings**  **"Secrets"**
2. Click: **"Edit Secrets"**
3. **Paste this TOML** (replace placeholder values with your actual credentials):

```toml
# =============================================================================
# STREAMLIT COMMUNITY CLOUD SECRETS
# =============================================================================
# Paste into: App Settings  Secrets
# These are exposed as st.secrets dict AND os.environ at runtime
# DO NOT commit secrets to GitHub repository

# -----------------------------------------------------------------------------
# LLM Provider (Gemini via LiteLLM)
# -----------------------------------------------------------------------------
GEMINI_API_KEY = "sk-your-actual-gemini-api-key-from-lingaro"
GOOGLE_GEMINI_BASE_URL = "https://llm.lingarogroup.com"
LLM_PROVIDER = "openai"
BASE_MODEL_ID = "gemini-3-flash"

# -----------------------------------------------------------------------------
# Langfuse Tracing & Observability
# -----------------------------------------------------------------------------
ENABLE_LANGFUSE = "true"
LANGFUSE_PUBLIC_KEY = "pk-lf-your-actual-public-key"
LANGFUSE_SECRET_KEY = "sk-lf-your-actual-secret-key"
LANGFUSE_HOST = "https://cloud.langfuse.com"

# Environment tag for trace filtering in Langfuse UI
# For production: use "production"
# For staging: use "staging"
ENVIRONMENT = "production"

# -----------------------------------------------------------------------------
# Optional: Observability Settings
# -----------------------------------------------------------------------------
ENABLE_PII_REDACTION = "true"
LITELLM_LOGGING = "false"
```

4. Click: **"Save"**
5. **App automatically restarts** with new secrets 

** Security Notes:**
- Secrets are encrypted and never shown in logs
- Each app (prod/staging) has separate isolated secrets
- No secrets should ever be in your GitHub repository

---

### Step 4: Verify Deployment Success

** In Streamlit Cloud UI:**

1. **Check status**: App should show "Running" (green dot)
2. **View logs**: Click "Manage app"  "Logs" tab
   - Look for: `"Langfuse tracing enabled via direct SDK"`
   - No errors about missing `GEMINI_API_KEY`
3. **Copy app URL**: e.g., `https://your-username-streamlit-chatbot-app-abc123.streamlit.app`

---

##  Post-Deployment Sanity Check

### Step 5: Test Live Application

1. **Open the app** in browser (use URL from Streamlit Cloud)

2. **Create a test conversation**:
   - Type: `"Hello, what is AI?"`
   - Wait for response (should appear in 2-5 seconds)
   - Type: `"Can you explain machine learning?"`
   - Wait for second response

3. **Verify app functionality**:
   -  Messages render correctly in chat interface
   -  No "Configuration error" messages appear
   -  Responses come from LLM (coherent answers, not error text)
   -  Temperature slider adjusts (try moving it)
   -  "Clear chat" button works

4. **Verify Langfuse trace** (critical step):
   - **Go to**: https://cloud.langfuse.com
   - **Navigate to**: "Traces" page
   - **Filter by**: 
     - Tag: `production` (or `staging` if you used that)
     - Time: Last 5 minutes
   - **Confirm you see**:
     -  At least 2 traces (one per chat message)
     -  Trace metadata includes: `environment: production`
     -  Token counts tracked: `prompt_tokens`, `completion_tokens`
     -  Cost calculated: small amount like `$0.0001`
     -  Latency logged: typically 1-3 seconds

**Example trace metadata you should see**:
```json
{
  "request_id": "abc-123-def-456",
  "environment": "production",
  "user_id": "anonymous",
  "session_id": "xyz-789-session"
}
```

5. **Optional - Check Monitor page**:
   - Click sidebar  "Monitor" page (if implemented)
   - Verify recent activity displays
   - Check cost tracking

---

##  Auto-Redeploy Behavior

### What Triggers Automatic Redeployment:

 **Push to `main` branch** (watched branch)
 **Changing secrets** in Streamlit Cloud UI
 **Clicking "Reboot app"** button in UI

### What Does NOT Trigger Redeployment:

 Pushes to other branches (unless you deploy separate apps for them)
 Opening pull requests
 Commits without push

### Redeployment Process (1-2 minutes):

1. Streamlit Cloud detects push to `main`
2. Pulls latest code from GitHub
3. Installs dependencies from `requirements.txt`
4. Restarts app with existing secrets
5. App becomes available again

**Test auto-redeploy**:
```powershell
# Make a small change (e.g., update page title)
# Edit app.py line 7: page_title="My Gemini Chatbot v2"

git add app.py
git commit -m "Test auto-redeploy"
git push origin main

# Watch Streamlit Cloud dashboard - status changes to "Building..."
# After 1-2 minutes, app restarts with your change visible
```

---

##  Optional: Create Staging Environment

**For staging/production separation:**

1. **Create staging branch**:
   ```powershell
   git checkout -b staging
   git push origin staging
   ```

2. **Deploy second app in Streamlit Cloud**:
   - Click "New app"
   - Same repository
   - Branch: **`staging`** (instead of main)
   - Same entrypoint: `app.py`

3. **Configure separate secrets**:
   - Use same TOML template
   - Change: `ENVIRONMENT = "staging"`
   - Optionally use different Langfuse project

4. **Result**: Two isolated apps
   - `main` branch  production app (`ENVIRONMENT=production`)
   - `staging` branch  staging app (`ENVIRONMENT=staging`)
   - Filter traces in Langfuse by environment tag to separate them

---

##  Troubleshooting

### App shows "Configuration error"
- **Cause**: Missing or invalid secrets
- **Fix**: Settings  Secrets, ensure all required keys present
- **Verify**: `GEMINI_API_KEY` starts with `sk-`, not placeholder text

### No traces in Langfuse
- **Cause**: `ENABLE_LANGFUSE="false"` or invalid credentials
- **Fix**: Check Secrets  `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`
- **Verify**: Keys start with `pk-lf-` and `sk-lf-` respectively

### App won't start / Build failed
- **Cause**: Dependency conflict in `requirements.txt`
- **Fix**: Check logs for pip errors
- **Common**: Ensure `litellm==1.49.7` (newer versions conflict with langfuse 2.12.0)

### "_HAS_STREAMLIT = False" in logs
- **Cause**: Normal - `backend.py` handles both Streamlit and non-Streamlit contexts
- **Should see**: `_HAS_STREAMLIT = True` when running in Streamlit Cloud

---

##  Summary

### Handled by Streamlit Cloud UI:
-  Creating app (New app button)
-  Configuring secrets (Settings  Secrets)
-  Selecting branch to watch (main, staging, etc.)
-  Auto-installing dependencies from `requirements.txt`
-  Auto-redeploying on git push to watched branch

### Handled by Git/GitHub:
-  Code changes (commit + push triggers redeploy)
-  Dependency updates (requirements.txt changes)
-  Branch management (main, staging, feature branches)

### Final Verification Checklist:
- [ ] App URL loads without errors
- [ ] Test conversation generates LLM responses
- [ ] Langfuse shows traces with correct `production` tag
- [ ] Token counts and costs are tracked in traces
- [ ] Auto-redeploy works (test with small code change)

---

** Deployment Complete!**

- **App live at**: `https://your-username-streamlit-chatbot-app-[id].streamlit.app`
- **Traces visible at**: https://cloud.langfuse.com (filter by tag: `production`)
- **Auto-redeploys on**: Every push to `main` branch