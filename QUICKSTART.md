# Quick Start Guide

Get up and running with the Instagram Follower Manager in 5 minutes!

## Prerequisites

Ensure you have:
- ✅ Python 3.11 or higher
- ✅ Node.js 18 or higher
- ✅ PowerShell (comes with Windows)

## One-Command Setup

Open PowerShell in the project directory and run:

```powershell
.\setup.ps1
```

This will:
1. Check your Python and Node.js versions
2. Create a Python virtual environment
3. Install all backend dependencies
4. Install Playwright browser automation
5. Install all frontend dependencies

## Starting the Application

### Option 1: Using Start Scripts (Recommended)

Open two PowerShell windows:

**Terminal 1 - Backend:**
```powershell
.\start-backend.ps1
```

**Terminal 2 - Frontend:**
```powershell
.\start-frontend.ps1
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

## Access the Application

Open your browser to:
**http://localhost:5173**

## First-Time Usage

1. **Login**: Enter your Instagram username and password
2. **Analyze**: Click "Analyze Followers" to fetch your follower lists
3. **Review**: Browse the list of people who don't follow you back
4. **Configure**: Adjust filters (minimum followers, exclude verified)
5. **Unfollow**: Select users and click "Unfollow Selected"

## Safety Settings

The app has built-in safety features:
- ⏱️ 30-60 second delays between unfollows
- 📊 50 unfollows per day limit (configurable)
- 🛡️ Automatic exclusion of verified accounts (optional)
- 🎯 Automatic exclusion of major influencers (optional)

## Configuration

Edit `backend\.env` to customize:

```env
MAX_DAILY_UNFOLLOWS=50      # Maximum unfollows per day
MIN_ACTION_DELAY=30         # Minimum seconds between actions
MAX_ACTION_DELAY=60         # Maximum seconds between actions
```

## Troubleshooting

### Backend won't start
- Ensure Python 3.11+ is installed: `python --version`
- Activate the virtual environment: `.\venv\Scripts\Activate.ps1`
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend won't start
- Ensure Node.js 18+ is installed: `node --version`
- Delete `node_modules` and reinstall: `npm install`

### Login fails
- Check your Instagram credentials
- Complete 2FA if prompted
- Instagram may require email/SMS verification

### Browser automation fails
- Reinstall Playwright: `playwright install chromium`
- Ensure no other Instagram sessions are open

## Important Notes

⚠️ **Use at Your Own Risk**
- This tool uses browser automation which may violate Instagram's Terms of Service
- There's a risk of temporary account restrictions
- Always use conservative settings and limits
- Start with small batches (10-20 users) to test

## API Documentation

FastAPI auto-generates interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Need Help?

Check the full [README.md](README.md) for detailed documentation.
