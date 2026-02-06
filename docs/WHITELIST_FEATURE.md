# Allow-List (Whitelist) Feature

## Overview

The allow-list feature lets you mark specific users who won't appear in your non-followers list, even if they don't follow you back. This is perfect for:

- 👨‍👩‍👧‍👦 **Family and close friends** (who might not use Instagram actively)
- ⭐ **Celebrities and influencers** (who you want to follow but won't follow back)
- 🏢 **Business accounts** (brands, companies, news outlets)
- 🎨 **Content creators** (artists, photographers, etc.)
- 💼 **Professional connections** (who use Instagram differently)

## How It Works

1. When you run a follower analysis, the app identifies users you follow who don't follow you back
2. Users on your allow-list are **automatically excluded** from the non-followers list
3. You won't accidentally unfollow them in batch operations
4. You can add/remove users from the allow-list anytime

## API Endpoints

### Add Users to Allow-List

**POST** `/api/whitelist/add`

```json
{
  "usernames": ["zancorr", "natgeo", "nasa"],
  "reason": "Family and favorite accounts"
}
```

**Response:**
```json
{
  "success": true,
  "added": ["zancorr", "natgeo", "nasa"],
  "already_whitelisted": [],
  "not_found": []
}
```

### Remove Users from Allow-List

**POST** `/api/whitelist/remove`

```json
{
  "usernames": ["someuser"]
}
```

**Response:**
```json
{
  "success": true,
  "removed": ["someuser"],
  "not_whitelisted": [],
  "not_found": []
}
```

### View Allow-List

**GET** `/api/whitelist`

**Response:**
```json
{
  "success": true,
  "count": 3,
  "users": [
    {
      "username": "zancorr",
      "full_name": "John Doe",
      "reason": "Family",
      "is_following_me": false,
      "i_am_following": true,
      "added_at": "2026-02-05T12:00:00"
    }
  ]
}
```

### Stats (includes whitelist count)

**GET** `/api/stats`

```json
{
  "total_users": 500,
  "total_followers": 250,
  "total_following": 300,
  "non_followers": 45,
  "whitelisted_users": 5,
  "today_unfollows": 10,
  "remaining_today": 40,
  "daily_limit": 50
}
```

## Database Migration

If you have an existing database, run the migration script:

```powershell
cd c:\GitHub\johnapaez\instagram-tool\backend
python migrate_add_whitelist.py
```

**Expected Output:**
```
📦 Found database at: instagram_tool.db
🔄 Starting migration...
➕ Adding column 'is_whitelisted'...
✅ Added 'is_whitelisted' column
➕ Adding column 'whitelist_reason'...
✅ Added 'whitelist_reason' column

🎉 Migration completed successfully!
```

## Usage Examples

### Example 1: Whitelist Family Members

```bash
curl -X POST http://localhost:8000/api/whitelist/add \
  -H "Content-Type: application/json" \
  -d '{
    "usernames": ["zancorr", "mom_instagram", "sister_account"],
    "reason": "Family - keep following always"
  }'
```

### Example 2: Whitelist Celebrities

```bash
curl -X POST http://localhost:8000/api/whitelist/add \
  -H "Content-Type: application/json" \
  -d '{
    "usernames": ["cristiano", "beyonce", "therock"],
    "reason": "Celebrities I want to follow"
  }'
```

### Example 3: Remove from Whitelist

```bash
curl -X POST http://localhost:8000/api/whitelist/remove \
  -H "Content-Type: application/json" \
  -d '["someuser"]'
```

### Example 4: Check Who's Whitelisted

```bash
curl http://localhost:8000/api/whitelist
```

## Database Schema

The `users` table now includes:

| Column | Type | Description |
|--------|------|-------------|
| `is_whitelisted` | BOOLEAN | If true, user won't appear in non-followers |
| `whitelist_reason` | TEXT | Optional note (family, celebrity, etc.) |

## Benefits

✅ **Never accidentally unfollow important people**
- Family members who don't use Instagram often
- Your spouse/partner's account
- Close friends who don't follow back

✅ **Keep following accounts you care about**
- News organizations
- Educational accounts
- Inspiration/motivation accounts

✅ **Clean non-followers list**
- Only shows people you might actually want to unfollow
- Reduces clutter in analysis results

✅ **Flexible management**
- Add/remove users anytime
- Optional reason tracking
- View entire allow-list

## Important Notes

1. **Whitelisted users are NEVER included in non-followers analysis**
   - They won't show up in the non-followers list
   - They won't be unfollowed in batch operations
   - They're protected from accidental unfollows

2. **Whitelist persists across analyses**
   - You only need to whitelist someone once
   - Survives database updates and re-analyses
   - Stays even if you unfollow and re-follow them

3. **You can whitelist users not in your database**
   - Add usernames preemptively
   - Protects them if you follow them later

4. **Whitelist is logged**
   - All add/remove actions are recorded
   - Full audit trail in actions table

## Workflow

### Typical Usage Flow

1. **Run follower analysis**
   ```
   POST /api/analysis/complete
   ```

2. **Check non-followers**
   ```
   GET /api/analysis/non-followers
   ```

3. **Spot family/friends in the list**
   ```
   "Oh, I see my husband and my friend Sarah!"
   ```

4. **Add them to allow-list**
   ```
   POST /api/whitelist/add
   {
     "usernames": ["zancorr", "sarah_jones"],
     "reason": "Family and close friends"
   }
   ```

5. **Check non-followers again**
   ```
   GET /api/analysis/non-followers
   (Now they're gone from the list!)
   ```

6. **Safely unfollow others**
   ```
   POST /api/actions/unfollow
   (Whitelisted users are protected)
   ```

## Frontend Integration

The frontend should include:

- ✅ **Whitelist button** on each user in non-followers list
- ✅ **Whitelist management page** to view/edit allow-list
- ✅ **Visual indicator** for whitelisted users
- ✅ **Reason input** when adding to whitelist
- ✅ **Quick add** for multiple users at once

## Security Considerations

- ✅ Whitelist is per-database (local to your installation)
- ✅ No external API calls - all local storage
- ✅ Actions are logged for transparency
- ✅ Can be reviewed and modified anytime

## Troubleshooting

### Issue: User still appears in non-followers after whitelisting

**Solution:** Refresh the non-followers list:
```bash
GET /api/analysis/non-followers
```

### Issue: Migration script fails

**Solution:** Check if database exists and is not locked:
```powershell
# Stop the backend
# Then run migration
python migrate_add_whitelist.py
```

### Issue: Can't add user to whitelist

**Check:**
1. Username spelling is correct
2. Backend is running
3. Database is accessible

## Future Enhancements

Potential future features:
- 📁 **Whitelist categories** (family, friends, celebrities)
- 📊 **Whitelist import/export** (CSV support)
- 🔄 **Auto-whitelist verified accounts** (optional setting)
- 📧 **Whitelist recommendations** (based on interaction history)

---

**Next Steps:**
- Run migration script if you have existing database
- Add family/friends to whitelist
- Enjoy cleaner non-followers analysis!
