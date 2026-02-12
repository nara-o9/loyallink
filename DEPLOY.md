# Flask Deployment Guide - Render (No Docker)

## 🚀 Quick Start

Your Flask app is configured for **free deployment on Render** with **no Docker needed**.

---

## ✅ Local Testing (Before Deployment)

### 1. Activate Virtual Environment
```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run Locally
```powershell
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## 🌐 Deploy to Render (Free)

### Step 1: Push to GitHub
```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/loyalilnk-login.git
git push -u origin main
```

### Step 2: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up (free)
3. Connect your GitHub account

### Step 3: Deploy Service
1. Click **"New +"** → **"Web Service"**
2. Select your `loyalilnk-login` repository
3. Render will auto-detect `render.yaml` configuration
4. Configure environment variables:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Generate a random string (e.g., `openssl rand -hex 32`) |
| `DATABASE_URL` | Keep empty for SQLite, or connect PostgreSQL DB |

5. Click **"Deploy"** ✨

### Step 4: Connect PostgreSQL (Optional)
1. In Render, create a **PostgreSQL** database
2. Copy the connection string
3. Set `DATABASE_URL` = `postgresql://...`

---

## 🔧 Configuration Files

### `requirements.txt`
- Contains all Python dependencies
- `gunicorn` for production server
- `psycopg2-binary` for PostgreSQL support (optional)

### `render.yaml`
- Tells Render how to build and run your app
- No Docker - uses Python 3 native environment
- Auto-scales with Render's infrastructure

### `wsgi.py`
- Entry point for Gunicorn
- Initializes database tables on startup
- Ensures app is production-ready

---

## 📊 What's Different (No Docker)

| Feature | Docker | Native Python |
|---------|--------|----------------|
| Complexity | High | **Low** ✓ |
| Startup Time | Slow | **Fast** ✓ |
| File Size | Large | **Small** ✓ |
| Maintenance | Complex | **Simple** ✓ |
| Free Tier Support | Limited | **Full** ✓ |

---

## ✨ Your App is Ready!

✅ No Docker configuration needed  
✅ Direct Python 3 execution  
✅ Gunicorn for production-grade serving  
✅ Auto-deployment on Git push  

Simply push to GitHub and Render handles the rest.

---

## 🐛 Troubleshooting

**App won't start on Render?**
- Check `SECRET_KEY` is set in environment variables
- Verify `DATABASE_URL` format if using PostgreSQL
- Check Render logs for detailed errors

**Database connection issues?**
- For PostgreSQL: ensure `DATABASE_URL` is correct
- For SQLite: use default (works on free tier)
- Run migration if needed: `python -c "from app import db, app; app.app_context().push(); db.create_all()"`

**Local vs Production differences?**
- Locally: Uses SQLite (stationery.db)
- Production: Uses PostgreSQL (if configured)
- Debug mode disabled on Render (safer)

---

## 💡 Tips

- Keep `SECRET_KEY` secure (use strong random string)
- PostgreSQL is more reliable for production
- Monitor app logs in Render dashboard
- Render spins down free apps after 15 min inactivity (normal)
