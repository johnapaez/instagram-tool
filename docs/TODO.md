# To-Do List

## Critical - Core Features

### 1. Implement Follower Analysis (HIGH PRIORITY)
**Status**: Not Started  
**Estimate**: 3-4 hours

**Tasks**:
- [ ] Create `instagram_get_followers()` sync function in `instagram_sync.py`
  - Navigate to user profile
  - Click followers link
  - Scroll and collect follower data
  - Handle pagination and Instagram rate limits
  - Return list of follower objects

- [ ] Create `instagram_get_following()` sync function in `instagram_sync.py`
  - Navigate to user profile
  - Click following link
  - Scroll and collect following data
  - Handle pagination
  - Return list of following objects

- [ ] Update `/api/analysis/followers/{username}` endpoint
  - Remove temporary 501 error
  - Integrate with sync Playwright function
  - Run in ThreadPoolExecutor
  - Store results in database
  - Return follower list

- [ ] Update `/api/analysis/following/{username}` endpoint
  - Remove temporary 501 error
  - Integrate with sync Playwright function
  - Run in ThreadPoolExecutor
  - Store results in database
  - Return following list

- [ ] Enable `/api/analysis/non-followers` endpoint
  - Currently works with DB, just needs data
  - Test filtering logic
  - Ensure verified/follower count filtering works

**Technical Notes**:
- Use same pattern as `instagram_login()` function
- Run in ThreadPoolExecutor like login
- Add debug logging with `[PLAYWRIGHT]` prefix
- Take screenshots on errors
- Handle Instagram's lazy-loading scrolling
- Respect rate limits (small delays between scrolls)

**Example Implementation**:
```python
def instagram_get_followers(username: str, session_cookies: list, limit: int = 500):
    """Fetch followers list using sync Playwright."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    
    # Load session cookies
    context.add_cookies(session_cookies)
    
    page = context.new_page()
    page.goto(f'https://www.instagram.com/{username}/')
    
    # Click followers link
    followers_link = page.locator(f'a[href="/{username}/followers/"]')
    followers_link.click()
    time.sleep(2)
    
    # Get dialog and scroll
    dialog = page.locator('div[role="dialog"]')
    followers = []
    seen_usernames = set()
    
    for _ in range(limit // 12):  # ~12 users per scroll
        # Extract usernames from dialog
        user_links = dialog.locator('a[href^="/"]').all()
        for link in user_links:
            href = link.get_attribute('href')
            username_from_href = href.strip('/').split('/')[0]
            if username_from_href and username_from_href not in seen_usernames:
                seen_usernames.add(username_from_href)
                followers.append({'username': username_from_href})
        
        # Scroll down
        dialog.evaluate('el => el.scrollTop = el.scrollHeight')
        time.sleep(random.uniform(1.5, 2.5))
        
        if len(followers) >= limit:
            break
    
    browser.close()
    playwright.stop()
    
    return followers[:limit]
```

### 2. Implement Unfollow Functionality (HIGH PRIORITY)
**Status**: Not Started  
**Estimate**: 2-3 hours

**Tasks**:
- [ ] Create `instagram_unfollow_user()` sync function
  - Navigate to user profile
  - Click "Following" button
  - Click "Unfollow" in confirmation dialog
  - Verify unfollow success
  - Return result

- [ ] Create `instagram_unfollow_batch()` sync function
  - Loop through list of usernames
  - Call unfollow for each
  - Add randomized delays between unfollows
  - Track successes and failures
  - Return batch results

- [ ] Update `/api/actions/unfollow` endpoint
  - Remove temporary 501 error
  - Integrate with sync Playwright function
  - Run in ThreadPoolExecutor
  - Check daily limits
  - Log all actions
  - Update database user records

- [ ] Test unfollow with single user
- [ ] Test batch unfollow with 5-10 users
- [ ] Verify delays are working correctly

**Example Implementation**:
```python
def instagram_unfollow_user(username: str, session_cookies: list):
    """Unfollow a single user."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    context.add_cookies(session_cookies)
    
    page = context.new_page()
    page.goto(f'https://www.instagram.com/{username}/')
    
    # Click Following button
    following_button = page.locator('button:has-text("Following")')
    following_button.click()
    time.sleep(1)
    
    # Click Unfollow in dialog
    unfollow_button = page.locator('button:has-text("Unfollow")')
    unfollow_button.click()
    time.sleep(2)
    
    browser.close()
    playwright.stop()
    
    return {'success': True, 'username': username}

def instagram_unfollow_batch(usernames: list, session_cookies: list, 
                             min_delay: int = 30, max_delay: int = 60):
    """Unfollow multiple users with delays."""
    results = []
    
    for i, username in enumerate(usernames):
        result = instagram_unfollow_user(username, session_cookies)
        results.append(result)
        
        # Delay between unfollows (except last one)
        if i < len(usernames) - 1:
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)
    
    return results
```

## Important - UX Improvements

### 3. Session Persistence (MEDIUM PRIORITY)
**Status**: Not Started  
**Estimate**: 1-2 hours

**Tasks**:
- [ ] Store browser cookies properly for session reuse
- [ ] Implement session restoration (load cookies on subsequent requests)
- [ ] Add session expiration detection
- [ ] Handle "re-login required" gracefully
- [ ] Test session persistence across server restarts

**Current Issue**:
- Login works but creates new browser session each time
- Need to reuse cookies for follower/unfollow operations

### 4. Better Error Messages (MEDIUM PRIORITY)
**Status**: Not Started  
**Estimate**: 1 hour

**Tasks**:
- [ ] Create error message mapping for common Instagram errors
- [ ] Display user-friendly error messages in UI
- [ ] Add troubleshooting hints for common issues
- [ ] Show "what went wrong" and "what to try" messages

**Example Errors**:
- "Login failed" → "Could not log in. Please check your credentials or complete 2FA if prompted."
- "Rate limit" → "Instagram rate limit reached. Please wait 1 hour before trying again."
- "Timeout" → "Instagram is loading slowly. Please try again or check your internet connection."

### 5. Progress Indicators (MEDIUM PRIORITY)
**Status**: Not Started  
**Estimate**: 2 hours

**Tasks**:
- [ ] Add loading spinner for analyze operation
- [ ] Show progress bar for unfollow batch
  - "Unfollowing 1 of 20..."
  - Percentage complete
  - Estimated time remaining
- [ ] Real-time status updates
  - Consider WebSocket for live updates
  - Or polling with `/api/progress/{task_id}` endpoint

## Nice to Have - Enhanced Features

### 6. Advanced Filtering (LOW PRIORITY)
**Status**: Not Started  
**Estimate**: 2 hours

**Tasks**:
- [ ] Filter by account age (needs profile scraping)
- [ ] Filter by bio keywords
- [ ] Filter by profile picture (has picture vs no picture)
- [ ] Filter by post count
- [ ] Filter by engagement rate
- [ ] Save filter presets

### 7. Export/Import (LOW PRIORITY)
**Status**: Not Started  
**Estimate**: 2 hours

**Tasks**:
- [ ] Export follower list to CSV
- [ ] Export non-follower list to CSV
- [ ] Import custom unfollow list from CSV
- [ ] Export activity log to CSV
- [ ] Add "Download Report" button

### 8. Scheduling (LOW PRIORITY)
**Status**: Not Started  
**Estimate**: 4 hours

**Tasks**:
- [ ] Add background task queue (Celery or similar)
- [ ] Create scheduled job table in database
- [ ] UI for scheduling unfollow operations
- [ ] Cron-like syntax for recurring jobs
- [ ] Email notifications when complete

### 9. Analytics Dashboard (LOW PRIORITY)
**Status**: Not Started  
**Estimate**: 3 hours

**Tasks**:
- [ ] Charts for follower growth over time
- [ ] Unfollow activity timeline
- [ ] Follower/following ratio trends
- [ ] Most active days/times
- [ ] Use Chart.js or Recharts

## Bug Fixes

### 10. Handle 2FA/SMS Verification
**Status**: Not Started  
**Estimate**: 2 hours

**Tasks**:
- [ ] Detect when Instagram asks for 2FA code
- [ ] Pause automation
- [ ] Show message to user: "Please complete 2FA in the browser"
- [ ] Wait for user to complete 2FA manually
- [ ] Continue after verification
- [ ] Add timeout (5 minutes)

### 11. Handle "Suspicious Login" Blocks
**Status**: Not Started  
**Estimate**: 1 hour

**Tasks**:
- [ ] Detect when Instagram blocks login
- [ ] Show clear message to user
- [ ] Provide instructions for verification
- [ ] Allow retry after verification

### 12. Better Cookie Consent Handling
**Status**: Partial  
**Estimate**: 30 minutes

**Tasks**:
- [x] Basic cookie consent handling exists
- [ ] Handle all cookie dialog variants
- [ ] Test with different geo-locations
- [ ] Handle GDPR cookie prompts

## Testing & Quality

### 13. Unit Tests (MEDIUM PRIORITY)
**Status**: Not Started  
**Estimate**: 4 hours

**Tasks**:
- [ ] Backend tests with pytest
  - Test database models
  - Test API endpoints (mocked)
  - Test utility functions
- [ ] Frontend tests with Jest
  - Test components
  - Test API client
  - Test utility functions
- [ ] Set up test CI/CD pipeline

### 14. E2E Tests (LOW PRIORITY)
**Status**: Not Started  
**Estimate**: 3 hours

**Tasks**:
- [ ] Playwright E2E tests
  - Test login flow
  - Test analyze flow
  - Test unfollow flow
- [ ] Run in CI/CD

### 15. Code Quality Tools (MEDIUM PRIORITY)
**Status**: Not Started  
**Estimate**: 2 hours

**Tasks**:
- [ ] Add pre-commit hooks
  - black (Python formatter)
  - flake8 (Python linter)
  - eslint (TypeScript linter)
  - prettier (TypeScript formatter)
- [ ] Add type hints to all Python functions
- [ ] Fix all TypeScript `any` types
- [ ] Add JSDoc comments

## Documentation

### 16. API Documentation (LOW PRIORITY)
**Status**: Partial (FastAPI auto-docs)  
**Estimate**: 1 hour

**Tasks**:
- [x] FastAPI generates OpenAPI docs
- [ ] Add detailed endpoint descriptions
- [ ] Add request/response examples
- [ ] Document error codes
- [ ] Add authentication guide

### 17. User Guide (LOW PRIORITY)
**Status**: Basic README exists  
**Estimate**: 2 hours

**Tasks**:
- [ ] Create step-by-step tutorial with screenshots
- [ ] Video walkthrough
- [ ] FAQ section
- [ ] Troubleshooting guide
- [ ] Best practices guide

### 18. Developer Guide (COMPLETED)
**Status**: Done ✅  
**Estimate**: N/A

**Tasks**:
- [x] Architecture documentation
- [x] Implementation details
- [x] This TODO list

## DevOps & Deployment

### 19. Docker Support (LOW PRIORITY)
**Status**: Not Started  
**Estimate**: 3 hours

**Tasks**:
- [ ] Create Dockerfile for backend
- [ ] Create Dockerfile for frontend
- [ ] Create docker-compose.yml
- [ ] Document Docker deployment
- [ ] Test on Linux/Mac

### 20. CI/CD Pipeline (LOW PRIORITY)
**Status**: Not Started  
**Estimate**: 3 hours

**Tasks**:
- [ ] GitHub Actions workflow
- [ ] Run tests on push
- [ ] Build frontend
- [ ] Deploy to staging
- [ ] Deploy to production (on tag)

### 21. Production Deployment Guide (LOW PRIORITY)
**Status**: Not Started  
**Estimate**: 2 hours

**Tasks**:
- [ ] Nginx configuration
- [ ] SSL certificate setup
- [ ] Environment variables guide
- [ ] Database migration guide
- [ ] Monitoring setup
- [ ] Backup strategy

## Performance

### 22. Browser Instance Pooling (LOW PRIORITY)
**Status**: Not Started  
**Estimate**: 2 hours

**Tasks**:
- [ ] Create browser pool manager
- [ ] Reuse browser instances
- [ ] Handle browser crashes
- [ ] Limit max instances
- [ ] Close idle browsers

### 23. Database Optimization (LOW PRIORITY)
**Status**: Partial (indexes exist)  
**Estimate**: 2 hours

**Tasks**:
- [x] Indexes on key columns
- [ ] Query optimization
- [ ] Add database query logging
- [ ] Implement connection pooling config
- [ ] Database performance monitoring

### 24. Frontend Optimization (LOW PRIORITY)
**Status**: Basic Vite optimization  
**Estimate**: 2 hours

**Tasks**:
- [x] Code splitting (Vite does this)
- [ ] Lazy load components
- [ ] Image optimization
- [ ] Bundle size analysis
- [ ] Performance monitoring

## Security

### 25. Enhanced Security (MEDIUM PRIORITY)
**Status**: Basic security in place  
**Estimate**: 3 hours

**Tasks**:
- [ ] Add rate limiting to API endpoints
- [ ] Implement CSRF protection
- [ ] Add request signing/verification
- [ ] Secure cookie storage (encryption)
- [ ] Add security headers
- [ ] Regular security audit
- [ ] Dependency vulnerability scanning

### 26. Multi-User Support (LOW PRIORITY - Optional)
**Status**: Not Started  
**Estimate**: 8+ hours

**Tasks**:
- [ ] Add user authentication system
- [ ] Separate Instagram sessions per user
- [ ] User management
- [ ] PostgreSQL migration
- [ ] User isolation
- [ ] Admin dashboard

## Priority Matrix

### Do First (Critical + High Value)
1. ✅ Instagram Login (COMPLETED)
2. **Follower Analysis** (Most important)
3. **Unfollow Functionality** (Core feature)
4. Session Persistence (Needed for above)

### Do Next (Important + Medium Value)
5. Better Error Messages
6. Progress Indicators
7. Unit Tests
8. Code Quality Tools
9. Enhanced Security

### Do Later (Nice to Have)
10. Advanced Filtering
11. Export/Import
12. Scheduling
13. Analytics Dashboard
14. E2E Tests
15. Docker Support
16. CI/CD Pipeline

### Consider (Low Priority)
17. API Documentation improvements
18. User Guide
19. Production Deployment
20. Performance optimizations
21. Multi-user support

## Estimated Timeline

**Week 1** (Current Status ✅):
- ✅ Project setup
- ✅ Instagram login automation
- ✅ Basic UI
- ✅ Database schema

**Week 2** (Next Steps):
- Follower analysis implementation (3-4 hours)
- Unfollow functionality (2-3 hours)
- Session persistence (1-2 hours)
- Better error messages (1 hour)
- **Total: ~10 hours**

**Week 3** (Enhancements):
- Progress indicators (2 hours)
- Advanced filtering (2 hours)
- Export/Import (2 hours)
- Unit tests (4 hours)
- **Total: ~10 hours**

**Week 4** (Polish):
- Code quality tools (2 hours)
- Enhanced security (3 hours)
- Documentation (3 hours)
- Bug fixes (2 hours)
- **Total: ~10 hours**

## Notes

- All estimates are for one developer
- High-priority items should be done before low-priority items
- Some features can be done in parallel
- Testing should be done alongside feature development
- Security should be reviewed before production deployment

## How to Use This TODO

1. Pick items from "Do First" section
2. Create a branch for each major feature
3. Check off sub-tasks as you complete them
4. Update status when starting/completing items
5. Add new items as needed
6. Review and reprioritize quarterly
