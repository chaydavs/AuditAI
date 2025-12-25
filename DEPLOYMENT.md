# VT Academic Optimizer - Deployment Guide

## Quick Start (Recommended Stack)

| Component | Service | Cost |
|-----------|---------|------|
| Frontend | Vercel | Free |
| Backend | Railway | $5/mo |
| Domain | Namecheap | ~$10/year |

**Total: ~$70/year**

---

## Step 1: Buy a Domain

### Option A: Namecheap (Cheapest)
1. Go to [namecheap.com](https://namecheap.com)
2. Search for your domain (e.g., `vtoptimizer.com`)
3. Purchase (~$10/year for .com)

### Option B: Cloudflare (Best DNS)
1. Go to [cloudflare.com](https://cloudflare.com)
2. Use Cloudflare Registrar
3. Better security + faster DNS

---

## Step 2: Deploy Backend to Railway

### 2.1 Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub

### 2.2 Deploy from GitHub
```bash
# First, push your code to GitHub
cd /path/to/HokieAd
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/hokiead.git
git push -u origin main
```

### 2.3 Create Railway Project
1. Click "New Project" → "Deploy from GitHub repo"
2. Select your repository
3. Choose the `backend` folder as root directory

### 2.4 Set Environment Variables in Railway
Go to your project → Variables → Add these:

```
JWT_SECRET=your-super-secret-jwt-key-make-it-long-and-random
GEMINI_API_KEY=your-gemini-api-key
RESEND_API_KEY=your-resend-api-key
EMAIL_FROM=onboarding@resend.dev
FRONTEND_URL=https://your-domain.com
```

### 2.5 Get Your Backend URL
Railway will give you a URL like: `https://hokiead-backend-production.up.railway.app`

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub

### 3.2 Import Project
1. Click "Add New" → "Project"
2. Import your GitHub repository
3. Set Root Directory to `frontend`

### 3.3 Set Environment Variables in Vercel
In Project Settings → Environment Variables:

```
VITE_API_URL=https://your-railway-backend-url.up.railway.app
```

### 3.4 Deploy
Click "Deploy" - Vercel will build and deploy automatically

---

## Step 4: Connect Your Domain

### For Vercel (Frontend)
1. Go to Project Settings → Domains
2. Add your domain: `vtoptimizer.com`
3. Vercel will show DNS records to add

### For Railway (Backend API)
1. Go to Settings → Networking → Custom Domain
2. Add: `api.vtoptimizer.com`
3. Railway will show DNS records

### Add DNS Records (in Namecheap/Cloudflare)
```
# Frontend (Vercel)
Type: CNAME
Name: @
Value: cname.vercel-dns.com

# Backend API (Railway)
Type: CNAME
Name: api
Value: your-app.up.railway.app
```

---

## Step 5: Update CORS (Backend)

Update `backend/main.py` to allow your production domain:

```python
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://vtoptimizer.com",
    "https://www.vtoptimizer.com",
]
```

---

## Step 6: SSL/HTTPS

Both Vercel and Railway provide **free SSL certificates** automatically!

---

## Alternative: All-in-One with Render

If you prefer one platform for everything:

1. Go to [render.com](https://render.com)
2. Create a "Web Service" for backend
3. Create a "Static Site" for frontend
4. Render handles SSL, custom domains, etc.

---

## Alternative: VPS (Most Control)

For full control, use DigitalOcean/Linode ($5-10/mo):

```bash
# On your VPS
sudo apt update
sudo apt install nginx python3-pip nodejs npm certbot

# Clone your repo
git clone https://github.com/YOUR_USERNAME/hokiead.git
cd hokiead

# Backend
cd backend
pip install -r requirements.txt
# Use systemd or pm2 to run uvicorn

# Frontend
cd ../frontend
npm install
npm run build
# Copy dist/ to nginx html folder

# SSL
sudo certbot --nginx -d vtoptimizer.com -d api.vtoptimizer.com
```

---

## Production Checklist

- [ ] Change JWT_SECRET to a strong random string
- [ ] Set up proper CORS origins
- [ ] Configure email (Resend with verified domain)
- [ ] Enable rate limiting
- [ ] Set up database backups (if using PostgreSQL)
- [ ] Monitor with Railway/Vercel dashboards
- [ ] Test all features on production URL

---

## Database Considerations

Currently using **SQLite** (fine for small-medium traffic).

For higher scale, switch to **PostgreSQL**:
1. Railway offers PostgreSQL add-on ($5/mo)
2. Update database connection in `main.py`

---

## Cost Breakdown

| Item | Monthly | Yearly |
|------|---------|--------|
| Domain | - | $10 |
| Railway (Backend) | $5 | $60 |
| Vercel (Frontend) | Free | Free |
| **Total** | **$5** | **$70** |

With free tiers only: **~$10/year** (just domain)
