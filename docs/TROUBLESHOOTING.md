# Troubleshooting Guide

Common issues and their solutions.

## Installation Issues

### Python 3.13 Subprocess Errors

**Symptom**: `NotImplementedError` when starting the application

```
NotImplementedError
  File "asyncio\base_events.py", line 503, in _make_subprocess_transport
    raise NotImplementedError
```

**Solution**: Use Python 3.11 instead

```powershell
# Check your Python version
python --version

# If 3.13, install Python 3.11
# Download from https://www.python.org/downloads/

# Recreate virtual environment with 3.11
cd backend
Remove-Item -Recurse -Force venv
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

### Playwright Browser Not Installed

**Symptom**: Browser fails to launch, missing binary error

**Solution**:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
playwright install chromium
```

### Node Modules Installation Fails

**Symptom**: `npm install` errors in frontend

**Solution**:
```powershell
cd frontend

# Clear cache and reinstall
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install
```

## Login Issues

### "Login failed" with No Details

**Possible Causes**:
1. Incorrect credentials
2. Instagram requires 2FA
3. Instagram blocked the login attempt
4. Network timeout

**Solutions**:

1. **Verify Credentials**:
   - Try logging into Instagram normally in your browser
   - Ensure username (not email) is used
   - Check for typos in password

2. **Complete 2FA**:
   - The browser window will pause if 2FA is required
   - Complete 2FA in the opened browser
   - Tool will continue after verification

3. **Instagram Security Check**:
   - Instagram may show "Suspicious Login Attempt"
   - Verify your identity through email/SMS
   - Try again after verification

4. **Network Issues**:
   - Check internet connection
   - Try with VPN disabled
   - Instagram may be down (check downdetector.com)

### Login Form Not Found

**Symptom**: `Could not find username input field`

**Debug Steps**:
1. Check `backend/` folder for screenshot files: `login_debug_*.png`
2. Look at what page Instagram is showing
3. Possible issues:
   - Instagram changed their HTML
   - Cookie consent blocking form
   - Geographic restrictions
   - Instagram maintenance

**Solution**:
- Update selectors in `instagram_sync.py`
- Add new selector to `possible_username_selectors` list

### Browser Opens But Nothing Happens

**Cause**: Timeout waiting for Instagram to load

**Solution**:
```python
# In instagram_sync.py, increase timeouts:
page.goto('https://www.instagram.com/accounts/login/', 
          wait_until='domcontentloaded', 
          timeout=120000)  # Increase from 60000 to 120000

page.wait_for_selector('input[name="username"]', 
                      timeout=60000)  # Increase from 30000 to 60000
```

## Runtime Errors

### "FeatureNotImplementedYet" Error

**Symptom**: Clicking "Analyze Followers" shows error

**Cause**: Feature temporarily disabled during Windows compatibility work

**Status**: Needs implementation (see `docs/TODO.md`)

**Workaround**: Login functionality is working. Follower analysis coming soon.

### Backend Won't Start

**Symptom**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# If still failing, reinstall everything
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

### Frontend Won't Start

**Symptom**: `Cannot find module` or compilation errors

**Solution**:
```powershell
cd frontend

# Reinstall dependencies
Remove-Item -Recurse -Force node_modules
npm install

# Clear Vite cache
Remove-Item -Recurse -Force node_modules/.vite

# Try starting again
npm run dev
```

### Database Locked Error

**Symptom**: `database is locked` error

**Cause**: Multiple processes accessing SQLite simultaneously

**Solution**:
```powershell
# Stop all Python processes
Get-Process python | Stop-Process -Force

# Delete lock file if exists
Remove-Item backend/instagram_tool.db-journal

# Restart backend
.\start-backend.ps1
```

## Browser Automation Issues

### Greenlet Threading Error

**Symptom**:
```
greenlet.error: Cannot switch to a different thread
```

**Cause**: Using async Playwright instead of sync

**Solution**: Already fixed in current code. If you see this:
- Ensure you're using `instagram_sync.py` with sync Playwright
- Check that functions run in ThreadPoolExecutor
- Update to latest code

### Browser Crashes During Automation

**Symptom**: Browser closes unexpectedly

**Common Causes**:
1. Out of memory
2. Instagram detected automation
3. Network interruption

**Solutions**:
```python
# Add error recovery
try:
    result = instagram_login(username, password)
except Exception as e:
    # Retry once
    time.sleep(5)
    result = instagram_login(username, password)
```

### Screenshot Files Keep Accumulating

**Issue**: Debug screenshots filling up disk

**Solution**:
```powershell
# Clean up old screenshots
Remove-Item backend/login_debug_*.png

# Or add to .gitignore (already done)
```

## Performance Issues

### Slow Page Loading

**Cause**: Instagram's pages are heavy

**Solutions**:
1. Increase timeouts
2. Use faster internet connection
3. Close other browser tabs/applications

### Backend Response Slow

**Cause**: Playwright automation is synchronous and blocking

**Expected**: Login takes 10-30 seconds (normal)

**If slower**:
- Check internet speed
- Instagram may be slow
- Your machine may be under load

### Frontend Laggy

**Cause**: Development mode isn't optimized

**Solution**:
```powershell
cd frontend

# Build for production (faster)
npm run build

# Serve production build
npm run preview
```

## Network Issues

### CORS Errors in Browser Console

**Symptom**: `Access-Control-Allow-Origin` error

**Solution**:
```python
# Verify CORS settings in backend/.env
CORS_ORIGINS=http://localhost:5173

# Restart backend after changing .env
```

### API Not Reachable

**Symptom**: `Network Error` or `ERR_CONNECTION_REFUSED`

**Check**:
1. Is backend running? (`http://localhost:8000`)
2. Is frontend running? (`http://localhost:5173`)
3. Firewall blocking ports?

**Solution**:
```powershell
# Check if ports are in use
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# Kill process if needed
Stop-Process -Id <PID> -Force

# Restart services
.\start-backend.ps1
.\start-frontend.ps1
```

## Data Issues

### Sessions Not Persisting

**Expected Behavior**: Currently, sessions don't fully persist across browser restarts

**Workaround**: Re-login when needed

**Future Fix**: See `docs/TODO.md` #3 - Session Persistence

### Users Not in Database

**Cause**: Follower analysis not yet implemented

**Status**: Coming soon (see `docs/TODO.md` #1)

### Activity Log Empty

**Expected**: Only shows login actions currently

**Future**: Will show all follower/unfollow actions when implemented

## Windows-Specific Issues

### PowerShell Execution Policy Error

**Symptom**: 
```
.\setup.ps1 : File cannot be loaded because running scripts is disabled
```

**Solution**:
```powershell
# Run as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try again
.\setup.ps1
```

### Path Too Long Error

**Symptom**: `The specified path, file name, or both are too long`

**Solution**:
```powershell
# Enable long paths in Windows
# Run as Administrator:
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or move project closer to root
# Example: C:\projects\instagram-tool
```

### Virtual Environment Activation Fails

**Symptom**: `Activate.ps1 cannot be loaded`

**Solution**:
```powershell
# Use alternative activation
cd backend
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt

# Use full path to python
venv\Scripts\python.exe -m uvicorn app.main:app
```

## Getting Help

### Steps Before Asking for Help

1. **Check the logs**:
   - Backend terminal output
   - Frontend browser console (F12)
   - Screenshot files in `backend/` folder

2. **Try these debugging steps**:
   - Restart both backend and frontend
   - Clear browser cache
   - Delete and recreate virtual environment
   - Re-run `setup.ps1`

3. **Gather information**:
   - Python version: `python --version`
   - Node version: `node --version`
   - Operating system version
   - Exact error message
   - Screenshot of error

### Where to Get Help

1. **Documentation**:
   - `README.md` - Overview
   - `QUICKSTART.md` - Setup guide
   - `docs/ARCHITECTURE.md` - Technical details
   - `docs/IMPLEMENTATION.md` - Code explanations
   - `docs/TODO.md` - Known limitations

2. **GitHub Issues**:
   - Check existing issues first
   - Open new issue with details above
   - Include logs and screenshots

3. **Common Error Patterns**:
   - Search this file for your error message
   - Google the error with "Playwright" or "FastAPI"
   - Check Playwright documentation

## Advanced Debugging

### Enable Detailed Logging

```python
# In instagram_sync.py, add more print statements
print(f"[DEBUG] Current URL: {page.url}")
print(f"[DEBUG] Page title: {page.title()}")
print(f"[DEBUG] Visible elements: {page.locator('*').count()}")
```

### Use Playwright Inspector

```python
# In instagram_sync.py
browser = playwright.chromium.launch(
    headless=False,
    slow_mo=1000  # Slow down by 1 second per action
)

# Or use inspector
PWDEBUG=1 python your_script.py
```

### Capture HAR File

```python
# Record network traffic
context = browser.new_context(
    record_har_path="network.har"
)
# ... do actions ...
context.close()  # HAR file saved

# Analyze with Chrome DevTools
```

### Database Debugging

```python
# In backend terminal
python

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM sessions"))
    for row in result:
        print(row)
```

## Prevention Tips

### Before Running

1. ✅ Check Python version (3.11 recommended)
2. ✅ Check Node version (18+ required)
3. ✅ Virtual environment activated
4. ✅ All dependencies installed
5. ✅ Playwright browser installed
6. ✅ Instagram credentials ready

### While Running

1. ✅ Watch backend terminal for errors
2. ✅ Watch browser automation
3. ✅ Check browser console (F12)
4. ✅ Don't close browser manually during automation
5. ✅ Don't modify database while app is running

### After Issues

1. ✅ Read error messages carefully
2. ✅ Check screenshot files
3. ✅ Review recent changes
4. ✅ Try clean restart
5. ✅ Document steps to reproduce
