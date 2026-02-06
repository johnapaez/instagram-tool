# Logs Directory

This directory contains runtime logs from Playwright automation operations.

## Structure

```
logs/
├── playwright_YYYYMMDD_HHMMSS.log  # Session logs (one per run)
├── debug/                          # Debug artifacts
│   ├── *_error_*.png              # Error screenshots
│   └── *.png                      # Debug screenshots
└── .gitignore                     # Excludes logs from git
```

## Log Files

### Playwright Session Logs

Each time you run a follower analysis or unfollow operation, a new log file is created:
- **Filename format**: `playwright_20260205_163045.log`
- **Contains**: All Playwright operations, scroll attempts, user counts, errors
- **Useful for**: Debugging issues, verifying operations, audit trail

**Example log content:**
```
[PLAYWRIGHT] Starting followers fetch for deciphur...
[PLAYWRIGHT] Loading 15 session cookies...
[PLAYWRIGHT] Navigating to profile: deciphur
[PLAYWRIGHT] Clicked followers link, waiting for dialog...
[PLAYWRIGHT] Dialog opened, starting to collect ALL followers...
[PLAYWRIGHT] +12 new followers (total: 12, scroll: 1)
[PLAYWRIGHT] Scroll: 0px to 481px (height: 881px, method: find by links)
[PLAYWRIGHT] +17 new followers (total: 29, scroll: 2)
...
[PLAYWRIGHT] Finished collecting followers: 150 total
```

### Debug Screenshots

Error screenshots are automatically saved to `debug/` when operations fail:
- `followers_error_*.png` - Follower fetch errors
- `following_error_*.png` - Following fetch errors  
- `unfollow_error_*.png` - Unfollow operation errors
- `login_error_*.png` - Login errors

## Log Retention

Logs are NOT automatically cleaned up. To prevent disk space issues:

**Manual cleanup:**
```powershell
# Delete logs older than 7 days
Get-ChildItem "c:\GitHub\johnapaez\instagram-tool\backend\logs\*.log" | 
  Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | 
  Remove-Item

# Delete debug screenshots older than 7 days
Get-ChildItem "c:\GitHub\johnapaez\instagram-tool\backend\logs\debug\*.png" | 
  Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | 
  Remove-Item
```

**Or delete all logs:**
```powershell
Remove-Item "c:\GitHub\johnapaez\instagram-tool\backend\logs\*.log"
Remove-Item "c:\GitHub\johnapaez\instagram-tool\backend\logs\debug\*.png"
```

## Troubleshooting

### No logs being created

Check:
1. Directory exists: `backend/logs/`
2. Backend has write permissions
3. Playwright operations are actually running

### Logs too large

Session logs can grow large if you have many followers/following:
- ~100 KB for typical runs
- ~1 MB for accounts with 1000+ followers

Delete old logs periodically or increase disk space.

### Finding specific operations

Logs include timestamps and operation types. Search for:
- `Starting followers fetch` - Follower operations
- `Starting following fetch` - Following operations
- `Starting batch unfollow` - Unfollow operations
- `Exception` - Errors

## Privacy Note

Logs may contain:
- ✅ Usernames
- ✅ Operation timestamps
- ✅ Error messages
- ❌ NO passwords or sensitive credentials

Logs are excluded from git via `.gitignore` and stored locally only.
