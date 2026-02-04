# 🚀 Production Deployment Guide

Quick reference for deploying the chatbot to production.

---

## Prerequisites

✅ Local testing complete (app runs at http://localhost:8501)  
✅ Integration check passed (`python check_integration.py`)  
✅ All required environment variables in `.env`

---

## Deployment Options

### Option 1: Streamlit Cloud (Fastest - 5 min)

**Best for**: Quick demos, small teams, managed hosting

1. **Prepare Repository**
   ```powershell
   # Ensure .env is in .gitignore (already done)
   git add .
   git commit -m "Production ready chatbot"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your GitHub repo
   - Set main file: `app.py`
   - Add secrets (Settings → Secrets):
     ```toml
     GEMINI_API_KEY = "sk-k_NlW..."
     GEMINI_API_BASE = "https://llm.lingarogroup.com"
     GEMINI_MODEL = "gemini-2.0-flash-exp"
     
     # Optional (if using):
     # LANGFUSE_PUBLIC_KEY = "pk-lf-..."
     # LANGFUSE_SECRET_KEY = "sk-lf-..."
     # LANGFUSE_HOST = "https://cloud.langfuse.com"
     ```
   - Click "Deploy"

3. **Verify**
   - Wait 2-3 minutes for deployment
   - Access at `https://<your-username>-chatbot.streamlit.app`
   - Test chat functionality
   - Check monitoring dashboard

**Limitations**: 
- 1 GB RAM limit
- Public URL (unless on Teams/Enterprise plan)
- No custom domain (free tier)

---

### Option 2: Docker Container (Recommended)

**Best for**: Full control, scalability, any cloud provider

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.12-slim

   WORKDIR /app

   # Copy requirements first (better caching)
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application code
   COPY . .

   # Expose Streamlit port
   EXPOSE 8501

   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:8501/_stcore/health || exit 1

   # Run app
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Create .dockerignore**
   ```
   venv/
   __pycache__/
   *.pyc
   .env
   .git/
   .vscode/
   logs/*
   metrics/*
   *.md
   ```

3. **Build Image**
   ```powershell
   docker build -t streamlit-chatbot:latest .
   ```

4. **Test Locally**
   ```powershell
   docker run -p 8501:8501 --env-file .env streamlit-chatbot:latest
   # Access at http://localhost:8501
   ```

5. **Push to Registry**
   ```powershell
   # Docker Hub
   docker tag streamlit-chatbot:latest yourusername/streamlit-chatbot:latest
   docker push yourusername/streamlit-chatbot:latest

   # OR AWS ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
   docker tag streamlit-chatbot:latest <account>.dkr.ecr.us-east-1.amazonaws.com/streamlit-chatbot:latest
   docker push <account>.dkr.ecr.us-east-1.amazonaws.com/streamlit-chatbot:latest

   # OR GCP Artifact Registry
   gcloud auth configure-docker us-central1-docker.pkg.dev
   docker tag streamlit-chatbot:latest us-central1-docker.pkg.dev/<project>/chatbot/streamlit-chatbot:latest
   docker push us-central1-docker.pkg.dev/<project>/chatbot/streamlit-chatbot:latest
   ```

6. **Deploy to Cloud**

   **AWS ECS/Fargate**:
   ```bash
   # Create task definition with environment variables
   # Deploy service with load balancer
   # Set desired count = 2 (for HA)
   ```

   **GCP Cloud Run**:
   ```bash
   gcloud run deploy streamlit-chatbot \
     --image us-central1-docker.pkg.dev/<project>/chatbot/streamlit-chatbot:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8501 \
     --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY},GEMINI_API_BASE=${GEMINI_API_BASE}"
   ```

   **Azure Container Instances**:
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name streamlit-chatbot \
     --image yourusername/streamlit-chatbot:latest \
     --cpu 2 --memory 4 \
     --ports 8501 \
     --environment-variables GEMINI_API_KEY=$GEMINI_API_KEY
   ```

---

### Option 3: Cloud VM (Traditional)

**Best for**: Full OS control, custom configurations

1. **Provision VM**
   - **AWS EC2**: t3.medium (2 vCPU, 4 GB RAM) - ~$30/month
   - **GCP Compute Engine**: e2-medium - ~$25/month
   - **Azure VM**: Standard_B2s - ~$30/month
   - **DigitalOcean Droplet**: $18/month

2. **SSH and Setup**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python 3.12
   sudo apt install python3.12 python3.12-venv python3-pip -y

   # Clone repository
   git clone https://github.com/yourusername/streamlit-chatbot.git
   cd streamlit-chatbot

   # Create virtual environment
   python3.12 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Copy .env file (secure method)
   nano .env  # Paste your local .env contents
   chmod 600 .env
   ```

3. **Run with Systemd** (auto-restart on failure)
   ```bash
   sudo nano /etc/systemd/system/streamlit-chatbot.service
   ```

   Paste:
   ```ini
   [Unit]
   Description=Streamlit Chatbot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/streamlit-chatbot
   Environment="PATH=/home/ubuntu/streamlit-chatbot/venv/bin"
   ExecStart=/home/ubuntu/streamlit-chatbot/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable streamlit-chatbot
   sudo systemctl start streamlit-chatbot
   sudo systemctl status streamlit-chatbot
   ```

4. **Configure Nginx Reverse Proxy**
   ```bash
   sudo apt install nginx -y
   sudo nano /etc/nginx/sites-available/streamlit-chatbot
   ```

   Paste:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 86400;
       }
   }
   ```

   Enable:
   ```bash
   sudo ln -s /etc/nginx/sites-available/streamlit-chatbot /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Enable HTTPS** (Let's Encrypt)
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d your-domain.com
   ```

---

### Option 4: Kubernetes (Enterprise Scale)

**Best for**: High availability, auto-scaling, multi-region

1. **Create Kubernetes Manifests**

   `deployment.yaml`:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: streamlit-chatbot
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: streamlit-chatbot
     template:
       metadata:
         labels:
           app: streamlit-chatbot
       spec:
         containers:
         - name: chatbot
           image: yourusername/streamlit-chatbot:latest
           ports:
           - containerPort: 8501
           env:
           - name: GEMINI_API_KEY
             valueFrom:
               secretKeyRef:
                 name: chatbot-secrets
                 key: gemini-api-key
           resources:
             requests:
               memory: "1Gi"
               cpu: "500m"
             limits:
               memory: "2Gi"
               cpu: "1000m"
           livenessProbe:
             httpGet:
               path: /_stcore/health
               port: 8501
             initialDelaySeconds: 30
             periodSeconds: 10
   ```

   `service.yaml`:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: streamlit-chatbot
   spec:
     type: LoadBalancer
     ports:
     - port: 80
       targetPort: 8501
     selector:
       app: streamlit-chatbot
   ```

2. **Create Secrets**
   ```bash
   kubectl create secret generic chatbot-secrets \
     --from-literal=gemini-api-key=$GEMINI_API_KEY
   ```

3. **Deploy**
   ```bash
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   kubectl get pods
   kubectl get services
   ```

4. **Auto-scaling**
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: streamlit-chatbot-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: streamlit-chatbot
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

---

## Post-Deployment Checklist

### Functional Testing
- [ ] Chat interface loads correctly
- [ ] Bot responds to messages (test 3-5 conversations)
- [ ] Conversation history persists across sessions
- [ ] Monitoring dashboard shows data
- [ ] Feedback submission works
- [ ] Error handling displays user-friendly messages

### Performance Testing
- [ ] Response time < 3 seconds
- [ ] Page load time < 2 seconds
- [ ] Handles 10 concurrent users
- [ ] Memory usage stable over 1 hour

### Security Checklist
- [ ] .env file NOT committed to Git
- [ ] HTTPS enabled (if not Streamlit Cloud)
- [ ] API keys stored securely (env vars or secrets manager)
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Input validation working

### Monitoring Setup
- [ ] Error logs accessible
- [ ] Metrics being collected
- [ ] Alerts configured (if using Phase 3)
- [ ] Uptime monitoring enabled
- [ ] Cost tracking setup

---

## Rollback Plan

If issues occur in production:

1. **Streamlit Cloud**: 
   - Click "Reboot app" or "Manage app" → "Revert to previous version"

2. **Docker**:
   ```bash
   docker pull yourusername/streamlit-chatbot:previous
   docker stop chatbot-container
   docker run -d --name chatbot-container -p 8501:8501 --env-file .env yourusername/streamlit-chatbot:previous
   ```

3. **VM/Systemd**:
   ```bash
   cd /home/ubuntu/streamlit-chatbot
   git log --oneline  # Find previous commit
   git reset --hard <commit-hash>
   sudo systemctl restart streamlit-chatbot
   ```

4. **Kubernetes**:
   ```bash
   kubectl rollout undo deployment/streamlit-chatbot
   kubectl rollout status deployment/streamlit-chatbot
   ```

---

## Maintenance

### Daily
- Check error logs: `tail -f logs/app.log`
- Monitor dashboard for anomalies
- Verify API key hasn't expired

### Weekly
- Review metrics (request count, latency, errors)
- Check disk usage (logs/, metrics/)
- Verify backups working

### Monthly
- Update dependencies: `pip list --outdated`
- Review security advisories
- Cost analysis
- Performance optimization

---

## Estimated Costs

| Deployment Method | Small (< 100 users) | Medium (100-1K users) | Large (1K+ users) |
|-------------------|---------------------|----------------------|-------------------|
| **Streamlit Cloud** | $0 (Free) | $250/mo (Teams) | $5K+/mo (Enterprise) |
| **Docker + Cloud Run** | $10-30/mo | $50-200/mo | $500+/mo |
| **VM (t3.medium)** | $30-50/mo | $100-300/mo | $1K+/mo (multi-VM) |
| **Kubernetes (EKS/GKE)** | $150-250/mo | $500-1K/mo | $2K-10K/mo |

*Plus Gemini API costs (~$0.50-5/1K requests depending on model)*

---

## Support

**Issues during deployment?**

1. Check [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) → Troubleshooting section
2. Run `python check_integration.py` to diagnose
3. Review logs: `logs/app.log`
4. Test locally first before re-deploying

**Common Issues**:
- Port 8501 in use → Change to 8502: `streamlit run app.py --server.port=8502`
- Module not found → Reinstall: `pip install -r requirements.txt`
- API errors → Check .env has valid keys
- Memory issues → Increase VM/container RAM to 4GB+

---

**Status**: 📄 Deployment guide ready  
**Last Updated**: 2025-01-XX  
**Recommended**: Option 2 (Docker) for production
