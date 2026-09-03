# Deployment Guide: Revenue Intelligence Suite (RIS)

This guide walks you through deploying the **Revenue Intelligence Suite (RIS)** to free cloud hosting platforms.

---

## 🏆 Recommended Platform: **Render** (Render.com)

**Render** is the best platform for deploying Python Data Analytics & Plotly/Dash applications. It provides free SSL (HTTPS), automatic Git integration, and native Gunicorn support.

### Step 1: Push Project to GitHub
1. Create a new repository on GitHub (e.g. `Revenue-Intelligence-Suite`).
2. Run the following commands in your terminal:
   ```bash
   git init
   git add .
   git commit -m "Deployment ready Revenue Intelligence Suite"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/Revenue-Intelligence-Suite.git
   git push -u origin main
   ```

### Step 2: Deploy on Render (1-Click Blueprint)
1. Sign up for a free account at [render.com](https://render.com/).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository (`Revenue-Intelligence-Suite`).
4. Fill in the deployment details:
   - **Name**: `revenue-intelligence-suite`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:server --timeout 120 --workers 2`
5. Click **Create Web Service**. Render will automatically build the environment, run the database generator, and give you a live HTTPS link (e.g., `https://revenue-intelligence-suite.onrender.com`).

---

## 🥈 Alternative Platform 1: **Railway** (Railway.app)

Railway provides instant deployment with zero setup.

1. Sign up at [railway.app](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub Repo**.
3. Select your repository.
4. Railway automatically detects `Procfile` and `requirements.txt` and deploys your Dash application instantly.

---

## 🥉 Alternative Platform 2: **PythonAnywhere** (PythonAnywhere.com)

Great for dedicated Python web apps:

1. Sign up for a free account at [pythonanywhere.com](https://www.pythonanywhere.com/).
2. Open a Bash Console and clone your repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Revenue-Intelligence-Suite.git
   ```
3. Create a virtual environment and install requirements:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.11 ris-env
   pip install -r requirements.txt
   ```
4. Under the **Web** tab, set up a new WSGI configuration pointing to `app:server`.

---

## 🛠 Pre-Flight Deployment Checklist (Already Configured in Code)
- [x] **WSGI Entrypoint**: `server = app.server` exposed in `app.py`.
- [x] **Dynamic Port Binding**: `port = int(os.environ.get("PORT", 8050))` configured in `app.py`.
- [x] **Production WSGI Server**: `gunicorn>=21.2.0` added to `requirements.txt`.
- [x] **Procfile & Render Blueprint**: `Procfile` and `render.yaml` created in project root.
- [x] **Automatic Data Bootstrapping**: SQLite database `revenue_intelligence.db` auto-generates raw CSVs and builds the analytical warehouse if not found on startup.
