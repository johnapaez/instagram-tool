# Implementation Details

## Overview

This document explains the implementation details, design decisions, and technical challenges overcome during development.

## Instagram Login Automation

### Challenge: Windows Subprocess Compatibility

**Problem**: Playwright requires spawning a subprocess to launch the browser. On Windows with Python 3.11+, the default asyncio event loop (`SelectorEventLoop`) doesn't support subprocesses, causing `NotImplementedError`.

**Evolution of Solutions**:

1. **Attempt 1: WindowsSelectorEventLoopPolicy** ❌
   ```python
   asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
   ```
   - Failed: Selector loop doesn't support subprocesses

2. **Attempt 2: WindowsProactorEventLoopPolicy** ❌
   ```python
   asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
   ```
   - Failed: Uvicorn overrides the policy

3. **Attempt 3: Uvicorn with asyncio loop** ❌
   ```bash
   uvicorn app.main:app --loop asyncio
   ```
   - Failed: Still had greenlet threading conflicts

4. **Final Solution: Synchronous Playwright API** ✅
   ```python
   def instagram_login(username, password, headless=False):
       playwright = sync_playwright().start()
       browser = playwright.chromium.launch(headless=headless)
       # ... automation
       browser.close()
       playwright.stop()
   
   # In FastAPI endpoint
   result = await loop.run_in_executor(executor, instagram_login, username, password)
   ```
   - **Success**: Sync API avoids all async/threading issues
   - Runs in ThreadPoolExecutor to keep FastAPI async

### Instagram Form Detection

**Challenge**: Instagram's login form uses various selectors depending on:
- Geographic location
- A/B testing
- Browser fingerprint
- Account status

**Solution**: Multi-selector fallback strategy

```python
possible_username_selectors = [
    'input[name="username"]',           # Standard attribute
    'input[type="text"]',               # Generic text input
    'input[autocomplete="username"]',   # Autocomplete hint
    'input[aria-label*="username" i]',  # Accessibility label
    'input[placeholder*="username" i]'  # Placeholder text
]

for selector in possible_username_selectors:
    if page.locator(selector).is_visible(timeout=5000):
        username_selector = selector
        break
```

**Benefits**:
- Resilient to Instagram UI changes
- Works across different Instagram variants
- Self-documenting (logs which selector worked)

### Login Button Click

**Challenge**: Submit button may not be clickable due to:
- Dynamic class names (Instagram uses obfuscated classes)
- JavaScript-controlled button enabling
- Form validation

**Solution**: Fallback to Enter key press

```python
# Try multiple button selectors
login_button_selector = None
for selector in possible_button_selectors:
    if page.locator(selector).is_visible(timeout=2000):
        login_button_selector = selector
        break

if not login_button_selector:
    # Fallback: Press Enter on password field
    page.locator(password_selector).press('Enter')
else:
    page.click(login_button_selector)
```

**Why Enter key is more reliable**:
- Always works regardless of button state
- Bypasses JavaScript validation issues
- Standard HTML form behavior

### Cookie Management

**Implementation**:
```python
# Save cookies after login
cookies = context.cookies()

# Store in database as JSON
db_session = DBSession(
    session_id=session_id,
    username=username,
    cookies=cookies,  # SQLAlchemy handles JSON serialization
    is_active=True
)
```

**Session restoration** (not yet implemented):
```python
# Load cookies from database
cookies = db_session.cookies

# Restore in new browser context
context.add_cookies(cookies)
page.goto('https://www.instagram.com/')
# User is now logged in
```

## Backend Architecture

### FastAPI Async + Sync Playwright Integration

**Challenge**: FastAPI is async, but sync Playwright works better on Windows.

**Solution**: ThreadPoolExecutor bridge

```python
# Create thread pool
executor = ThreadPoolExecutor(max_workers=3)

# Async endpoint
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    loop = asyncio.get_event_loop()
    
    # Run sync function in executor
    result = await loop.run_in_executor(
        executor,
        instagram_login,  # Sync function
        request.username,
        request.password,
        False
    )
    
    return result
```

**Benefits**:
- FastAPI remains fully async
- Playwright runs in isolated threads
- No blocking of main event loop
- Clean separation of concerns

### Database Design

**Philosophy**: Optimistic storage with lazy updates

```python
# Store follower immediately
new_user = User(
    username=follower['username'],
    is_following_me=True,
    # Other fields populated later
)

# Update on subsequent fetches
if existing_user:
    existing_user.is_following_me = True
    existing_user.updated_at = datetime.utcnow()
```

**Indexing strategy**:
```python
class User(Base):
    username = Column(String, unique=True, index=True)  # Fast lookups
    user_id = Column(String, unique=True)               # Instagram ID
    is_following_me = Column(Boolean, default=False, index=True)
    i_am_following = Column(Boolean, default=False, index=True)
```

**Query optimization**:
```python
# Efficient non-follower query
non_followers = db.query(User).filter(
    User.i_am_following == True,
    User.is_following_me == False
).all()
```

### Session Management

**Current Implementation** (Simple):
```python
# Global dictionary (in-memory)
active_bots = {}

# Store bot instance
active_bots[session_id] = bot

# Retrieve for subsequent requests
bot = active_bots.get(session_id)
```

**Limitations**:
- Lost on server restart
- Not suitable for multiple workers
- No expiration handling

**Production Implementation** (Recommended):
```python
import redis

redis_client = redis.Redis()

# Store session with TTL
redis_client.setex(
    f"session:{session_id}",
    3600,  # 1 hour TTL
    json.dumps(session_data)
)

# Retrieve session
session_data = json.loads(
    redis_client.get(f"session:{session_id}")
)
```

## Frontend Architecture

### Component Structure

**Design Pattern**: Container/Presentational

```typescript
// Container Component (Dashboard.tsx)
const Dashboard = () => {
    const [data, setData] = useState();
    
    useEffect(() => {
        // Fetch data
    }, []);
    
    return <UserList users={data} />;
};

// Presentational Component (UserList.tsx)
const UserList = ({ users }) => {
    return (
        <div>
            {users.map(user => <UserCard user={user} />)}
        </div>
    );
};
```

**Benefits**:
- Separation of concerns
- Reusable presentational components
- Easier testing
- Clear data flow

### State Management

**Current**: React hooks (useState, useEffect)

```typescript
const [nonFollowers, setNonFollowers] = useState<UserInfo[]>([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState('');
```

**For larger scale**: Consider Context API or Zustand

```typescript
// Global state store
const useStore = create((set) => ({
    session: null,
    setSession: (session) => set({ session }),
    nonFollowers: [],
    setNonFollowers: (users) => set({ nonFollowers: users }),
}));
```

### API Client Design

**Organized by domain**:

```typescript
export const authApi = {
    login: async (username, password) => { /* ... */ },
    logout: async (sessionId) => { /* ... */ }
};

export const analysisApi = {
    getFollowers: async (username, sessionId, limit) => { /* ... */ },
    getFollowing: async (username, sessionId, limit) => { /* ... */ },
    getNonFollowers: async (sessionId, filters) => { /* ... */ }
};
```

**Benefits**:
- Clear organization
- Easy to find endpoints
- Type-safe with TypeScript
- Centralized error handling

### Error Handling

**Layered approach**:

```typescript
// API layer
try {
    const response = await api.post('/login', data);
    return response.data;
} catch (err) {
    if (err.response) {
        // Server error response
        throw new Error(err.response.data.detail);
    } else if (err.request) {
        // Network error
        throw new Error('Network error');
    } else {
        // Other error
        throw new Error(err.message);
    }
}

// Component layer
try {
    const result = await authApi.login(username, password);
    if (result.success) {
        onLogin(result);
    } else {
        setError(result.error || 'Login failed');
    }
} catch (err) {
    setError(err.message || 'An error occurred');
}
```

## Safety Features

### Rate Limiting

**Daily limit enforcement**:

```python
today = datetime.utcnow().date()
today_unfollows = db.query(Action).filter(
    Action.action_type == 'unfollow',
    Action.status == 'success',
    Action.created_at >= datetime.combine(today, datetime.min.time())
).count()

if today_unfollows + len(request.usernames) > settings.max_daily_unfollows:
    raise HTTPException(status_code=429, detail="Daily limit exceeded")
```

### Action Delays

**Randomized human-like behavior**:

```python
import random
import time

# Between actions
time.sleep(random.uniform(
    settings.min_action_delay,  # 30 seconds
    settings.max_action_delay   # 60 seconds
))

# Form filling delays
time.sleep(random.uniform(1, 2))
```

**Why randomization matters**:
- Mimics human behavior
- Avoids pattern detection
- Reduces bot detection risk

### Activity Logging

**Every action is logged**:

```python
action = Action(
    action_type='unfollow',
    username=target_username,
    status='success',  # or 'failed'
    details={'reason': 'non-follower'},
    created_at=datetime.utcnow()
)
db.add(action)
db.commit()
```

**Benefits**:
- Full audit trail
- Debugging capability
- User transparency
- Analytics potential

## Testing Strategy

### Current State
- **Manual testing only**
- No automated test suite

### Recommended Testing Approach

**Unit Tests**:
```python
# test_instagram_sync.py
def test_login_form_detection():
    """Test that multiple selectors work for login form"""
    # Mock page with different selectors
    # Assert correct selector is found

def test_cookie_storage():
    """Test cookie serialization/deserialization"""
    # Create cookies
    # Store in DB
    # Retrieve and verify
```

**Integration Tests**:
```python
# test_api_endpoints.py
from fastapi.testclient import TestClient

client = TestClient(app)

def test_login_endpoint():
    response = client.post("/api/auth/login", json={
        "username": "test",
        "password": "test"
    })
    assert response.status_code == 200
```

**E2E Tests**:
```typescript
// test/login.spec.ts
import { test, expect } from '@playwright/test';

test('user can login', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.fill('input[name="username"]', 'test');
    await page.fill('input[name="password"]', 'test');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/dashboard/);
});
```

## Performance Optimizations

### Implemented

1. **Vite for fast builds**
   - Hot Module Replacement (HMR)
   - Optimized production builds
   - Code splitting

2. **Database indexing**
   - Indexed username columns
   - Indexed session_id
   - Boolean indexes for filters

3. **Connection pooling**
   - SQLAlchemy session management
   - Reused database connections

### Planned

1. **Browser instance reuse**
   - Keep browser open between requests
   - Faster subsequent operations

2. **Pagination**
   - Load followers in chunks
   - Reduce memory usage

3. **Caching**
   - Cache follower lists
   - Invalidate on updates
   - Redis for distributed caching

## Debugging Tools

### Backend Logging

**Structured logging with prefixes**:
```python
print(f"[LOGIN] Starting login for user: {username}")
print(f"[PLAYWRIGHT] Navigating to Instagram...")
print(f"[DATABASE] Storing session: {session_id}")
```

**Benefits**:
- Easy log filtering
- Clear context
- Searchable logs

### Screenshot on Error

```python
try:
    page.wait_for_selector('input[name="username"]', timeout=30000)
except Exception:
    screenshot_path = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    page.screenshot(path=screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")
    raise
```

### Browser DevTools

When running in headed mode (headless=False):
- Can inspect elements
- View network requests
- Debug JavaScript
- See real-time automation

## Security Considerations

### Input Validation

**Pydantic models**:
```python
class LoginRequest(BaseModel):
    username: str
    password: str
    
    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()
```

### SQL Injection Prevention

**SQLAlchemy ORM**:
```python
# Safe - parameterized query
user = db.query(User).filter(User.username == username).first()

# Dangerous - never do this
# db.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

### CORS Configuration

**Strict origin checking**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Only localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Environment-Specific Configuration

### Development
```env
DATABASE_URL=sqlite:///./instagram_tool.db
CORS_ORIGINS=http://localhost:5173
MAX_DAILY_UNFOLLOWS=999
MIN_ACTION_DELAY=1
MAX_ACTION_DELAY=2
```

### Production
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
CORS_ORIGINS=https://yourdomain.com
MAX_DAILY_UNFOLLOWS=50
MIN_ACTION_DELAY=30
MAX_ACTION_DELAY=60
```

## Lessons Learned

### 1. Windows Async Complexity
**Learning**: Windows subprocess handling is fundamentally different from Unix/Linux
**Solution**: Use synchronous APIs when possible on Windows

### 2. Instagram Form Variability
**Learning**: Instagram serves different HTML based on many factors
**Solution**: Always have fallback selectors

### 3. Browser Automation Reliability
**Learning**: Timeouts and network issues are common
**Solution**: Generous timeouts, retries, and error screenshots

### 4. Type Safety Benefits
**Learning**: TypeScript catches errors before runtime
**Solution**: Use TypeScript for all frontend code

### 5. Documentation Importance
**Learning**: Complex async/threading issues need clear documentation
**Solution**: Document architectural decisions in detail

## Future Improvements

### Code Quality
- [ ] Add unit tests (pytest for backend)
- [ ] Add E2E tests (Playwright for frontend)
- [ ] Set up pre-commit hooks (black, flake8, eslint)
- [ ] Add type hints to all Python functions
- [ ] Implement error boundaries in React

### Performance
- [ ] Implement Redis for session storage
- [ ] Add database query caching
- [ ] Optimize follower list pagination
- [ ] Implement lazy loading for long lists
- [ ] Add service worker for offline capability

### Features
- [ ] Export follower lists to CSV
- [ ] Import custom unfollow lists
- [ ] Schedule automated unfollows
- [ ] Email notifications for completed operations
- [ ] Analytics dashboard with charts

### DevOps
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Automated deployment
- [ ] Monitoring and alerting
- [ ] Log aggregation
