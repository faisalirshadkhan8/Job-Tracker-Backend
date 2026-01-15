# 🐳 Docker + PostgreSQL Setup Guide for Beginners

A step-by-step guide to set up PostgreSQL database using Docker for the Job Application Tracker.

---

## 📋 Table of Contents

1. [What is Docker?](#what-is-docker)
2. [Install Docker](#install-docker)
3. [Understanding docker-compose.yml](#understanding-docker-composeyml)
4. [Start PostgreSQL Container](#start-postgresql-container)
5. [Connect Django to PostgreSQL](#connect-django-to-postgresql)
6. [Common Docker Commands](#common-docker-commands)
7. [Troubleshooting](#troubleshooting)

---

## 🤔 What is Docker?

Think of Docker as a **shipping container for software**. Just like shipping containers can hold anything and work on any ship, Docker containers can hold any software and run on any computer.

**Why use Docker for PostgreSQL?**
- ✅ No complex installation - just one command
- ✅ Same setup works on Windows, Mac, Linux
- ✅ Easy to delete and start fresh
- ✅ Matches production environment exactly
- ✅ Your computer stays clean - everything is contained

---

## 📥 Install Docker

### Step 1: Download Docker Desktop

1. Go to: https://www.docker.com/products/docker-desktop/
2. Click **"Download for Windows"**
3. Run the installer (`Docker Desktop Installer.exe`)

### Step 2: Install Docker Desktop

1. Follow the installation wizard
2. When asked, ensure **"Use WSL 2 instead of Hyper-V"** is checked (recommended)
3. Click **Install**
4. Restart your computer when prompted

### Step 3: Start Docker Desktop

1. Open **Docker Desktop** from Start Menu
2. Wait for it to start (you'll see "Docker Desktop is running" in system tray)
3. You might need to accept the terms of service

### Step 4: Verify Installation

Open PowerShell and run:

```powershell
docker --version
```

You should see something like:
```
Docker version 24.0.7, build afdd53b
```

Also verify Docker Compose:
```powershell
docker-compose --version
```

---

## 📄 Understanding docker-compose.yml

Here's our `docker-compose.yml` file explained:

```yaml
# Docker Compose for Job Application Tracker

services:
  db:                                    # Service name (we call it "db")
    image: postgres:16-alpine            # Use PostgreSQL 16 (alpine = smaller image)
    container_name: jobtracker_db        # Name of the container
    restart: unless-stopped              # Auto-restart if it crashes
    environment:                         # Database configuration
      POSTGRES_DB: jobtracker            # Database name
      POSTGRES_USER: jobtracker_user     # Username
      POSTGRES_PASSWORD: jobtracker_pass123  # Password
    ports:
      - "5432:5432"                       # Map port 5432 (host:container)
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Persist data

volumes:
  postgres_data:                         # Named volume for data persistence
```

### Key Points:
- **Image**: `postgres:16-alpine` - Official PostgreSQL image
- **Ports**: `5432:5432` - PostgreSQL default port
- **Volumes**: Data persists even if container is deleted

---

## 🚀 Start PostgreSQL Container

### Step 1: Open PowerShell in Project Directory

```powershell
cd D:\Interview\mysite
```

### Step 2: Start the Container

```powershell
docker-compose up -d
```

**What this does:**
- `up` = Create and start the container
- `-d` = Run in background (detached mode)

**Expected output:**
```
[+] Running 2/2
 ✔ Network mysite_default      Created
 ✔ Container jobtracker_db     Started
```

### Step 3: Verify Container is Running

```powershell
docker ps
```

**Expected output:**
```
CONTAINER ID   IMAGE                COMMAND                  STATUS         PORTS                    NAMES
abc123...      postgres:16-alpine   "docker-entrypoint..."   Up 2 minutes   0.0.0.0:5432->5432/tcp   jobtracker_db
```

### Step 4: Check Container Logs (Optional)

```powershell
docker logs jobtracker_db
```

You should see:
```
PostgreSQL init process complete; ready for start up.
database system is ready to accept connections
```

---

## 🔌 Connect Django to PostgreSQL

### Step 1: Check .env File

Make sure your `.env` file has these values:

```env
# PostgreSQL Database (Docker)
DB_NAME=jobtracker
DB_USER=jobtracker_user
DB_PASSWORD=jobtracker_pass123
DB_HOST=localhost
DB_PORT=5432
```

### Step 2: Verify Django Settings

Your `config/settings/development.py` should have:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'jobtracker'),
        'USER': os.environ.get('DB_USER', 'jobtracker_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'jobtracker_pass123'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### Step 3: Run Migrations

```powershell
# Activate virtual environment first
D:\Interview\venv\Scripts\Activate.ps1

# Navigate to project
cd D:\Interview\mysite

# Create migrations
python manage.py makemigrations users companies applications interviews

# Apply migrations
python manage.py migrate
```

### Step 4: Create Superuser

```powershell
python manage.py createsuperuser
```

### Step 5: Run the Server

```powershell
python manage.py runserver
```

Visit: http://127.0.0.1:8000/admin/

---

## 🛠️ Common Docker Commands

### Container Management

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start containers in background |
| `docker-compose down` | Stop and remove containers |
| `docker-compose stop` | Stop containers (keep data) |
| `docker-compose start` | Start stopped containers |
| `docker-compose restart` | Restart containers |

### View Information

| Command | Description |
|---------|-------------|
| `docker ps` | List running containers |
| `docker ps -a` | List all containers (including stopped) |
| `docker logs jobtracker_db` | View container logs |
| `docker logs -f jobtracker_db` | Follow logs in real-time |

### Database Access

| Command | Description |
|---------|-------------|
| `docker exec -it jobtracker_db psql -U jobtracker_user -d jobtracker` | Open PostgreSQL shell |

### Cleanup

| Command | Description |
|---------|-------------|
| `docker-compose down` | Stop containers |
| `docker-compose down -v` | Stop + delete all data |
| `docker system prune` | Remove unused resources |

---

## 🐛 Troubleshooting

### Issue 1: "Cannot connect to the Docker daemon"

**Cause:** Docker Desktop is not running.

**Fix:** 
1. Open Docker Desktop from Start Menu
2. Wait for it to fully start (green icon in system tray)

---

### Issue 2: "Port 5432 is already in use"

**Cause:** Another PostgreSQL instance is using the port.

**Fix Option 1:** Stop the other PostgreSQL:
```powershell
# Find what's using the port
netstat -ano | findstr :5432

# Stop the process (replace PID with actual number)
taskkill /PID <PID> /F
```

**Fix Option 2:** Use a different port in `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Use 5433 instead
```
Then update `.env`:
```env
DB_PORT=5433
```

---

### Issue 3: "Connection refused" when running migrations

**Cause:** Container is not ready yet.

**Fix:** 
1. Wait 10-15 seconds after starting container
2. Check if container is running: `docker ps`
3. Check logs: `docker logs jobtracker_db`

---

### Issue 4: "FATAL: password authentication failed"

**Cause:** Credentials mismatch between Django and Docker.

**Fix:** 
1. Make sure `.env` matches `docker-compose.yml` exactly
2. If you changed credentials, recreate the container:
```powershell
docker-compose down -v  # Warning: deletes all data!
docker-compose up -d
```

---

### Issue 5: "psycopg2 not installed"

**Cause:** PostgreSQL driver not installed.

**Fix:**
```powershell
pip install psycopg2-binary
```

---

## 📊 Visual Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR COMPUTER                           │
│                                                             │
│  ┌──────────────────┐      ┌──────────────────────────┐    │
│  │   Django App     │      │    Docker Container      │    │
│  │                  │      │  ┌──────────────────┐   │    │
│  │  localhost:8000  │──────│─▶│   PostgreSQL     │   │    │
│  │                  │      │  │  localhost:5432  │   │    │
│  │  Your Python     │      │  │                  │   │    │
│  │  Code Runs Here  │      │  │  Database Lives  │   │    │
│  │                  │      │  │  Here            │   │    │
│  └──────────────────┘      │  └──────────────────┘   │    │
│                            │                          │    │
│                            │  Volume: postgres_data   │    │
│                            │  (Data persists here)    │    │
│                            └──────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Quick Start Checklist

- [ ] Docker Desktop installed
- [ ] Docker Desktop is running
- [ ] `docker-compose.yml` exists in project folder
- [ ] `.env` file has correct database credentials
- [ ] Run `docker-compose up -d`
- [ ] Verify with `docker ps`
- [ ] Run `python manage.py migrate`
- [ ] Run `python manage.py createsuperuser`
- [ ] Run `python manage.py runserver`
- [ ] Visit http://127.0.0.1:8000/admin/

---

## 🎉 You're Done!

Your PostgreSQL database is now running in Docker. Every time you want to work on the project:

1. **Start Docker Desktop** (if not running)
2. **Start the database:** `docker-compose up -d`
3. **Activate venv:** `D:\Interview\venv\Scripts\Activate.ps1`
4. **Run server:** `python manage.py runserver`

When done for the day:
- `docker-compose stop` (keeps data)
- Or just close Docker Desktop
