# Railway Deployment Guide

## Prerequisites
1. Railway account (sign up at https://railway.app/)
2. GitHub account (connect your repo to Railway)
3. Your project pushed to GitHub

## Railway Services Required

Your application needs **4 services**:

### 1. Web Service (Django Application)
### 2. Celery Worker Service
### 3. Celery Beat Service  
### 4. PostgreSQL Database (Railway provides)
### 5. Redis (Railway provides)

---

## Deployment Steps

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Create Railway Project
1. Go to https://railway.app/
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### Step 3: Add PostgreSQL Database
1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically set `DATABASE_URL` variable

### Step 4: Add Redis
1. Click "New" → "Database" → "Redis"
2. Railway will automatically set `REDIS_URL` variable

### Step 5: Configure Web Service Environment Variables

In your **web service**, add these environment variables:

```env
# Django Settings
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<generate-a-strong-random-key-here>
DEBUG=False
ALLOWED_HOSTS=*.railway.app,yourdomain.com
SECURE_SSL_REDIRECT=True

# Database (automatically set by Railway PostgreSQL)
# DATABASE_URL=postgresql://user:pass@host:port/dbname

# Redis (automatically set by Railway Redis)
# REDIS_URL=redis://host:port

# Frontend URL
FRONTEND_URL=https://your-frontend-url.com
CORS_ALLOWED_ORIGINS=https://your-frontend-url.com

# API Keys (Optional - for full functionality)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
GROQ_API_KEY=your_groq_key
SERPER_API_KEY=your_serper_key
MODEL=llama-3.3-70b-versatile

# Email Settings (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com

# 2FA & Webhooks
TWOFA_ISSUER_NAME=Your App Name
WEBHOOK_TIMEOUT=10
WEBHOOK_MAX_RETRIES=3

# AI Settings
AI_ASYNC_ENABLED=true
```

### Step 6: Add Celery Worker Service
1. Click "New" → "Empty Service"
2. Connect same GitHub repo
3. Name it "celery-worker"
4. Set start command:
   ```
   celery -A config worker -l info --concurrency=2
   ```
5. Add environment variables (copy from web service):
   - `DJANGO_SETTINGS_MODULE`
   - `SECRET_KEY`
   - `DATABASE_URL` (reference from PostgreSQL)
   - `REDIS_URL` (reference from Redis)
   - All other API keys

### Step 7: Add Celery Beat Service
1. Click "New" → "Empty Service"
2. Connect same GitHub repo
3. Name it "celery-beat"
4. Set start command:
   ```
   celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```
5. Add environment variables (copy from web service)

### Step 8: Run Migrations
After deployment, run migrations:

```bash
railway run python manage.py migrate
```

Or in the Railway dashboard, go to web service and run:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

---

## Important Notes

### 1. Generate SECRET_KEY
Generate a secure secret key:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Database Connection
Railway automatically provides `DATABASE_URL`. Update your production settings if needed to parse it correctly. The app already uses `dj-database-url` which handles this.

### 3. Static Files
Railway will run `collectstatic` during build. Make sure your Dockerfile includes this step.

### 4. Domain Configuration
- Railway provides a default domain: `your-app.railway.app`
- Add custom domain in Railway dashboard under "Settings" → "Domains"
- Update `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` accordingly

### 5. Service Communication
All services in the same Railway project can communicate using private networking. Reference environment variables using Railway's variable referencing.

### 6. Monitoring
- View logs: Railway dashboard → Select service → "Logs"
- Monitor resources: Check "Metrics" tab
- Set up alerts in "Settings"

### 7. Cost Optimization
- Free tier: $5/month credit
- Each service consumes resources
- Consider using Railway's "Sleep on Idle" for non-production environments

---

## Troubleshooting

### Build Fails
- Check Dockerfile is correct
- Ensure all requirements.txt dependencies are valid
- Check Railway build logs

### Application Won't Start
- Verify `PORT` environment variable is used
- Check `ALLOWED_HOSTS` includes Railway domain
- Review application logs

### Database Connection Issues
- Ensure `DATABASE_URL` is set
- Check PostgreSQL service is running
- Verify network connectivity between services

### Celery Not Processing Tasks
- Confirm Redis is running
- Check `REDIS_URL` is correctly set in worker/beat services
- Review celery worker logs

---

## Post-Deployment

1. **Create superuser:**
   ```bash
   railway run python manage.py createsuperuser
   ```

2. **Test API:**
   - Visit: `https://your-app.railway.app/api/docs/`
   - Login and test endpoints

3. **Monitor logs:**
   ```bash
   railway logs
   ```

4. **Scale services (if needed):**
   - Railway dashboard → Service → "Settings" → "Resources"

---

## Useful Railway CLI Commands

Install Railway CLI:
```bash
npm i -g @railway/cli
```

Login:
```bash
railway login
```

Link project:
```bash
railway link
```

View logs:
```bash
railway logs
```

Run commands:
```bash
railway run python manage.py migrate
railway run python manage.py createsuperuser
```

Deploy:
```bash
railway up
```

---

## Alternative: Docker Deployment on Railway

If you prefer Docker-based deployment:

1. Railway will automatically detect `Dockerfile`
2. Ensure `railway.toml` is configured
3. Railway will build and deploy using Docker

Your `railway.toml` is already configured for this approach.

---

## Need Help?

- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app/
