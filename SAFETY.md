# Safety Guidelines

## ⚠️ Important Disclaimer

This tool uses browser automation to interact with Instagram. While it implements various safety measures, you should be aware of the following:

### Risks

1. **Account Restrictions**: Instagram may temporarily or permanently restrict your account
2. **Rate Limiting**: Instagram has strict rate limits that can trigger account blocks
3. **Terms of Service**: Using automation violates Instagram's Terms of Service
4. **Detection**: Instagram actively works to detect and prevent automation

### Our Recommendation

**Use this tool at your own risk and discretion.** We recommend:
- Starting with very small batches (5-10 users)
- Using the tool infrequently (not daily)
- Keeping delays high (60+ seconds)
- Not exceeding 20-30 unfollows per day
- Having a backup of your following list

## Built-in Safety Features

The tool includes several safety mechanisms:

### 1. Rate Limiting

- **Default Delay**: 30-60 seconds between each unfollow
- **Randomization**: Delays are randomized to appear more human-like
- **Daily Limit**: Maximum 50 unfollows per day (configurable)

### 2. Smart Filtering

- **Verified Accounts**: Automatically excluded by default
- **Follower Threshold**: Keep accounts with large followings
- **Manual Review**: Batch review before unfollowing

### 3. Session Management

- **Secure Storage**: Credentials stored locally only
- **Cookie-based**: Reuses sessions to minimize logins
- **Automatic Cleanup**: Sessions expire and clean up

### 4. Activity Logging

- **Full Audit Trail**: Every action is logged
- **Status Tracking**: Success/failure monitoring
- **Timestamp Records**: Track when actions occurred

### 5. Emergency Controls

- **Stop Anytime**: Cancel operations mid-process
- **Logout**: Clear all sessions immediately
- **Database**: All data stored locally

## Best Practices

### Before You Start

1. **Export Your Following List**: Have a backup before making changes
2. **Test with Small Batches**: Start with 5-10 users to test
3. **Review Filters**: Ensure you're excluding accounts you want to keep
4. **Check Daily Limit**: Verify remaining daily quota

### During Operation

1. **Monitor Progress**: Watch the activity log for errors
2. **Don't Rush**: Higher delays = safer operation
3. **Stay Within Limits**: Respect the daily limit
4. **Take Breaks**: Don't use the tool every day

### After Operation

1. **Review Logs**: Check for any failures or errors
2. **Verify Changes**: Confirm unfollows on Instagram
3. **Wait Before Next Run**: Give Instagram time to "forget"

## Recommended Settings

### Conservative (Safest)

```env
MAX_DAILY_UNFOLLOWS=20
MIN_ACTION_DELAY=60
MAX_ACTION_DELAY=120
```

**Usage**: Once every 3-4 days, 10-20 users at a time

### Moderate (Balanced)

```env
MAX_DAILY_UNFOLLOWS=50
MIN_ACTION_DELAY=30
MAX_ACTION_DELAY=60
```

**Usage**: Once every 1-2 days, 20-30 users at a time

### Aggressive (Higher Risk)

```env
MAX_DAILY_UNFOLLOWS=100
MIN_ACTION_DELAY=20
MAX_ACTION_DELAY=40
```

**Usage**: Daily, up to 50 users at a time

⚠️ **Not Recommended**: Aggressive settings significantly increase detection risk

## What to Do If You Get Restricted

If Instagram restricts your account:

1. **Stop Using the Tool**: Immediately cease all automation
2. **Wait**: Account restrictions are usually temporary (24-48 hours)
3. **Verify Identity**: Instagram may ask for email/SMS verification
4. **Appeal**: Use Instagram's appeal process if restriction persists
5. **Go Manual**: Consider manual unfollowing for a while

## Detection Indicators

Watch for these signs that Instagram may be detecting automation:

- Login challenges (captcha, email verification)
- "Try Again Later" messages
- Actions blocked or restricted
- Unusual session timeouts
- Followers/following counts not updating

If you see these, **stop using the tool immediately** and wait 48-72 hours.

## Privacy & Security

### What We Store

- Instagram cookies (locally, encrypted)
- Follower/following lists (locally, in SQLite)
- Action logs (locally, in SQLite)

### What We DON'T Store

- Your Instagram password (never stored anywhere)
- Your data on any remote server
- Any personally identifiable information outside your machine

### Security Best Practices

1. **Use a Strong Password**: For your Instagram account
2. **Enable 2FA**: Two-factor authentication on Instagram
3. **Don't Share Sessions**: Each person should use their own instance
4. **Keep Software Updated**: Update dependencies regularly
5. **Run Locally**: Don't deploy this to public servers

## Legal Considerations

- This tool is for **personal use** only
- Do **not** use for commercial purposes
- Do **not** sell or redistribute
- You are **responsible** for compliance with Instagram's ToS
- We provide **no warranty** or guarantee

## Questions?

Before using this tool, ask yourself:

1. ✅ Have I backed up my following list?
2. ✅ Have I read and understood the risks?
3. ✅ Am I okay with potential account restrictions?
4. ✅ Have I configured conservative settings?
5. ✅ Will I start with a small test batch?

If you answered "No" to any of these, **please reconsider** using this tool.

---

**Remember**: The safest way to manage followers is manually through the Instagram app. This tool is a convenience with inherent risks.
