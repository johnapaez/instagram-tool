# Architecture Documentation

## System Overview

The Instagram Follower Manager is a full-stack web application that uses browser automation to interact with Instagram for follower management.

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│                    (http://localhost:5173)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  - React 18 + TypeScript                                     │
│  - Tailwind CSS + Custom Components                          │
│  - Axios for API communication                               │
│  - State management with React hooks                         │
└────────────────────────┬────────────────────────────────────┘
                         │ Proxy: /api → :8000
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  - Python 3.11 + FastAPI                                     │
│  - SQLAlchemy ORM + SQLite                                   │
│  - Pydantic for validation                                   │
│  - ThreadPoolExecutor for Playwright                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ├──────────────┐
                         ▼              ▼
              ┌──────────────┐  ┌──────────────────┐
              │   SQLite DB  │  │  Playwright      │
              │              │  │  (Sync API)      │
              │  - Users     │  │                  │
              │  - Sessions  │  │  Chromium        │
              │  - Actions   │  │  Browser         │
              │  - Logs      │  │                  │
              └──────────────┘  └────────┬─────────┘
                                         │
                                         ▼
                                ┌─────────────────┐
                                │   Instagram     │
                                │   Website       │
                                └─────────────────┘
```

## Technology Stack

### Frontend
- **Framework**: React 18.2.0
- **Language**: TypeScript 5.3.3
- **Build Tool**: Vite 5.0.12
- **Styling**: Tailwind CSS 3.4.1
- **HTTP Client**: Axios 1.6.5
- **Icons**: Lucide React 0.309.0
- **Dev Server**: Vite dev server with HMR

### Backend
- **Framework**: FastAPI 0.115.6
- **Language**: Python 3.11.9
- **Server**: Uvicorn 0.34.0 with asyncio event loop
- **Database**: SQLite 3 with SQLAlchemy 2.0.36
- **Validation**: Pydantic 2.10.5
- **Automation**: Playwright 1.49.1 (sync API)
- **Async Support**: nest-asyncio 1.6.0

### Browser Automation
- **Engine**: Playwright Chromium
- **Mode**: Synchronous API (for Windows compatibility)
- **Execution**: ThreadPoolExecutor (3 workers)
- **Features**: Headless/headed modes, cookie management, screenshot capability

## Component Architecture

### Frontend Components

```
src/
├── components/
│   ├── Button.tsx              # Reusable button with variants
│   ├── Card.tsx                # Card container components
│   ├── Input.tsx               # Form input component
│   ├── LoginForm.tsx           # Authentication form
│   ├── Dashboard.tsx           # Main application dashboard
│   ├── UserList.tsx            # User selection and batch operations
│   └── ActivityLog.tsx         # Action history display
├── services/
│   └── api.ts                  # API client with typed endpoints
├── types/
│   └── index.ts                # TypeScript type definitions
├── lib/
│   └── utils.ts                # Utility functions
├── App.tsx                     # Root component with routing
└── main.tsx                    # Application entry point
```

### Backend Structure

```
app/
├── main.py                     # FastAPI application & endpoints
├── instagram_sync.py           # Playwright sync automation
├── instagram.py                # Legacy async automation (unused)
├── models.py                   # SQLAlchemy database models
├── database.py                 # Database connection & session
└── config.py                   # Configuration management
```

## Data Flow

### 1. Authentication Flow

```
User enters credentials
    ↓
Frontend: LoginForm.tsx
    ↓ POST /api/auth/login
Backend: login() endpoint
    ↓
ThreadPoolExecutor.run_in_executor()
    ↓
instagram_sync.instagram_login()
    ↓ Playwright automation
Browser: Navigate → Fill form → Submit
    ↓
Instagram: Authenticate
    ↓ Cookies
Backend: Store session in DB
    ↓ session_id
Frontend: Store in localStorage
    ↓
Dashboard: Display user interface
```

### 2. API Request Flow

```
Frontend Component
    ↓ Axios request
Vite Proxy (/api → :8000)
    ↓
FastAPI Endpoint
    ↓
Dependency Injection (get_db)
    ↓
Database Query (SQLAlchemy)
    ↓
Response Model (Pydantic)
    ↓ JSON
Frontend Component
    ↓
React State Update
    ↓
UI Re-render
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    user_id TEXT UNIQUE,
    full_name TEXT,
    profile_pic_url TEXT,
    is_verified BOOLEAN DEFAULT 0,
    follower_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    is_following_me BOOLEAN DEFAULT 0,
    i_am_following BOOLEAN DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    cookies JSON NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    last_used TIMESTAMP,
    created_at TIMESTAMP
);
```

### Actions Table
```sql
CREATE TABLE actions (
    id INTEGER PRIMARY KEY,
    action_type TEXT NOT NULL,
    username TEXT NOT NULL,
    user_id TEXT,
    status TEXT NOT NULL,
    details JSON,
    created_at TIMESTAMP
);
```

### UnfollowQueue Table
```sql
CREATE TABLE unfollow_queue (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    user_id TEXT,
    full_name TEXT,
    is_verified BOOLEAN DEFAULT 0,
    follower_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    added_at TIMESTAMP,
    processed_at TIMESTAMP
);
```

## Windows Compatibility Solutions

### Problem 1: Asyncio Subprocess Support
**Issue**: Python's default asyncio event loop on Windows doesn't support subprocesses, which Playwright requires.

**Solution**: Use `WindowsProactorEventLoopPolicy`:
```python
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

**Why it works**: ProactorEventLoop uses I/O Completion Ports which support subprocesses on Windows.

### Problem 2: Uvicorn Event Loop Conflicts
**Issue**: Uvicorn creates its own event loop, overriding the policy set in code.

**Solution**: Run uvicorn with `--loop asyncio` flag:
```bash
uvicorn app.main:app --loop asyncio
```

### Problem 3: Playwright Async API Issues
**Issue**: Even with ProactorEventLoop, Playwright async API had greenlet threading issues.

**Final Solution**: Use Playwright's **synchronous API** in a ThreadPoolExecutor:

```python
# Synchronous function
def instagram_login(username, password, headless=False):
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    # ... automation logic
    browser.close()
    playwright.stop()

# Async endpoint
@app.post("/api/auth/login")
async def login(request):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        instagram_login,
        username,
        password,
        False
    )
    return result
```

**Why it works**:
- Sync Playwright avoids async/greenlet conflicts
- ThreadPoolExecutor isolates browser automation
- Event loop remains responsive for FastAPI

## Security Considerations

### 1. Credential Handling
- **Never stored**: Passwords are only passed to Instagram, never saved
- **Cookie storage**: Only session cookies are stored in SQLite
- **Local only**: All data stored on user's machine
- **No transmission**: Credentials never sent to any server except Instagram

### 2. Session Management
- **UUID-based**: Session IDs use UUID4 for uniqueness
- **Cookie-based**: Uses Instagram's own session cookies
- **Expiration**: Sessions can be manually invalidated
- **Active tracking**: `is_active` flag for session control

### 3. Rate Limiting
- **Daily limits**: Configurable max actions per 24 hours (default: 50)
- **Action delays**: 30-60 second randomized delays between actions
- **Request limits**: Respects Instagram's 200 requests/hour limit
- **Exponential backoff**: Planned for retry logic

### 4. Data Protection
- **No external APIs**: No data sent to third parties
- **Local storage**: SQLite database on user's machine
- **Environment variables**: Sensitive config in .env file
- **Git ignored**: Credentials, databases, and sessions excluded

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login to Instagram
- `POST /api/auth/logout` - Logout and invalidate session

### Analysis (Temporarily Disabled)
- `GET /api/analysis/followers/{username}` - Fetch followers
- `GET /api/analysis/following/{username}` - Fetch following
- `GET /api/analysis/non-followers` - Get non-followers list

### Actions (Temporarily Disabled)
- `POST /api/actions/unfollow` - Unfollow batch of users

### Logging & Stats
- `GET /api/logs` - Get action history
- `GET /api/stats` - Get usage statistics

## Configuration

### Backend (.env)
```env
DATABASE_URL=sqlite:///./instagram_tool.db
SECRET_KEY=random-secret-string
CORS_ORIGINS=http://localhost:5173
MAX_DAILY_UNFOLLOWS=50
MIN_ACTION_DELAY=30
MAX_ACTION_DELAY=60
```

### Frontend (vite.config.ts)
```typescript
{
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
}
```

## Performance Considerations

### 1. Browser Automation
- **Headless mode**: Faster for production (currently disabled for debugging)
- **Single browser**: Reuse browser instances when possible
- **Screenshot caching**: Only capture on errors
- **Page timeouts**: Configured timeouts prevent hanging

### 2. Database
- **Indexed columns**: username, session_id, user_id
- **Connection pooling**: SQLAlchemy session management
- **Query optimization**: Filter before loading full objects
- **Batch operations**: Bulk inserts for follower lists

### 3. Frontend
- **Code splitting**: Vite handles automatic chunking
- **Lazy loading**: Components loaded on demand
- **State management**: Minimal re-renders with React hooks
- **API caching**: Response caching for repeated requests

## Scalability Notes

**Current Limitations**:
- Single-user application (no multi-user support)
- SQLite (not suitable for concurrent writes)
- In-memory session storage (lost on restart)
- No horizontal scaling

**Production Enhancements Needed**:
- PostgreSQL or MySQL for multi-user support
- Redis for session management
- Message queue for background tasks (Celery/RQ)
- Load balancer for multiple backend instances
- CDN for frontend static assets

## Monitoring & Debugging

### Logging
- **Backend**: Print statements with `[PLAYWRIGHT]` prefix
- **Frontend**: Browser console.log
- **Database**: Action logs table
- **Screenshots**: Saved on automation errors

### Error Handling
- **Try-catch blocks**: Comprehensive exception handling
- **HTTP status codes**: Proper REST error responses
- **User feedback**: Error messages in UI
- **Debug mode**: Detailed tracebacks in development

## Future Architecture Enhancements

1. **Microservices**: Separate automation service
2. **Message Queue**: Background job processing
3. **WebSocket**: Real-time progress updates
4. **Docker**: Containerization for easy deployment
5. **CI/CD**: Automated testing and deployment
6. **Monitoring**: Application performance monitoring (APM)
7. **Caching**: Redis for frequently accessed data
