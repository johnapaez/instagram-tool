# Project Structure

This document provides an overview of the project's file structure and organization.

## Root Directory

```
instagram-tool/
├── backend/                    # Python FastAPI backend
├── frontend/                   # React TypeScript frontend
├── .gitignore                 # Git ignore rules
├── LICENSE                    # MIT License
├── README.md                  # Main documentation
├── QUICKSTART.md              # Quick start guide
├── SAFETY.md                  # Safety guidelines
├── CONTRIBUTING.md            # Contribution guidelines
├── PROJECT_STRUCTURE.md       # This file
├── setup.ps1                  # Automated setup script
├── start-backend.ps1          # Backend start script
└── start-frontend.ps1         # Frontend start script
```

## Backend Structure

```
backend/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI application & endpoints
│   ├── instagram.py          # Instagram automation logic (Playwright)
│   ├── models.py             # SQLAlchemy database models
│   ├── database.py           # Database configuration
│   └── config.py             # Application configuration
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in git)
└── .env.example              # Example environment file
```

### Backend Components

**`main.py`** - FastAPI Application
- Authentication endpoints (`/api/auth/login`, `/api/auth/logout`)
- Analysis endpoints (`/api/analysis/followers`, `/api/analysis/following`, `/api/analysis/non-followers`)
- Action endpoints (`/api/actions/unfollow`)
- Logging endpoints (`/api/logs`)
- Statistics endpoints (`/api/stats`)

**`instagram.py`** - Instagram Bot
- `InstagramBot` class with Playwright automation
- Login functionality
- Follower/following fetching
- User information retrieval
- Unfollow operations with rate limiting

**`models.py`** - Database Models
- `User` - Instagram user information
- `Action` - Action log entries
- `Session` - Instagram session data
- `UnfollowQueue` - Unfollow queue management

**`database.py`** - Database Setup
- SQLAlchemy engine configuration
- Session management
- Database initialization

**`config.py`** - Configuration
- Settings management with Pydantic
- Environment variable loading
- CORS configuration

## Frontend Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Button.tsx        # Reusable button component
│   │   ├── Card.tsx          # Card components
│   │   ├── Input.tsx         # Input component
│   │   ├── LoginForm.tsx     # Login form component
│   │   ├── Dashboard.tsx     # Main dashboard
│   │   ├── UserList.tsx      # User list with selection
│   │   └── ActivityLog.tsx   # Activity log display
│   ├── services/
│   │   └── api.ts            # API service layer
│   ├── types/
│   │   └── index.ts          # TypeScript type definitions
│   ├── lib/
│   │   └── utils.ts          # Utility functions
│   ├── App.tsx               # Main app component
│   ├── main.tsx              # Application entry point
│   └── index.css             # Global styles with Tailwind
├── public/                   # Static assets
├── index.html                # HTML template
├── package.json              # Node.js dependencies
├── tsconfig.json             # TypeScript configuration
├── tsconfig.node.json        # TypeScript config for Vite
├── vite.config.ts            # Vite configuration
├── tailwind.config.js        # Tailwind CSS configuration
├── postcss.config.js         # PostCSS configuration
└── .eslintrc.cjs             # ESLint configuration
```

### Frontend Components

**`LoginForm.tsx`**
- Instagram login interface
- Credential handling
- Error display
- Session creation

**`Dashboard.tsx`**
- Main application interface
- Statistics display
- Analysis configuration
- Activity monitoring

**`UserList.tsx`**
- Non-follower display
- Batch selection
- Unfollow action
- Progress tracking

**`ActivityLog.tsx`**
- Action history
- Status indicators
- Real-time updates

**`api.ts`** - API Services
- `authApi` - Authentication
- `analysisApi` - Follower analysis
- `actionApi` - Unfollow actions
- `logsApi` - Activity logs
- `statsApi` - Statistics

## Data Flow

### Authentication Flow

```
User Input → LoginForm → authApi.login() 
  → Backend /api/auth/login → InstagramBot.login() 
  → Instagram → Session Created → Response → Dashboard
```

### Analysis Flow

```
Dashboard → Analyze Button → analysisApi.getFollowers/getFollowing() 
  → Backend → InstagramBot.get_followers/get_following() 
  → Instagram → Data Fetched → Database → Response → Dashboard
```

### Unfollow Flow

```
UserList → Select Users → Unfollow Button → actionApi.unfollowUsers() 
  → Backend → InstagramBot.unfollow_batch() 
  → Instagram (with delays) → Database Logs → Response → UI Update
```

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Instagram username
- `user_id` - Instagram user ID
- `full_name` - Full name
- `profile_pic_url` - Profile picture URL
- `is_verified` - Verified status
- `follower_count` - Follower count
- `following_count` - Following count
- `is_following_me` - Whether they follow you
- `i_am_following` - Whether you follow them
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Actions Table
- `id` - Primary key
- `action_type` - Type of action
- `username` - Target username
- `user_id` - Target user ID
- `status` - Action status
- `details` - JSON details
- `created_at` - Action timestamp

### Sessions Table
- `id` - Primary key
- `session_id` - Unique session ID
- `username` - Instagram username
- `cookies` - Session cookies (JSON)
- `is_active` - Active status
- `last_used` - Last usage timestamp
- `created_at` - Creation timestamp

### UnfollowQueue Table
- `id` - Primary key
- `username` - Username to unfollow
- `user_id` - User ID
- `full_name` - Full name
- `is_verified` - Verified status
- `follower_count` - Follower count
- `status` - Queue status
- `priority` - Priority level
- `added_at` - Added timestamp
- `processed_at` - Processing timestamp

## Configuration Files

### Backend (.env)
```
DATABASE_URL - SQLite database URL
SECRET_KEY - Application secret key
CORS_ORIGINS - Allowed CORS origins
MAX_DAILY_UNFOLLOWS - Daily unfollow limit
MIN_ACTION_DELAY - Minimum delay between actions
MAX_ACTION_DELAY - Maximum delay between actions
```

### Frontend (vite.config.ts)
- Development server configuration
- Proxy configuration for API calls
- Path aliases

## Key Dependencies

### Backend
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Playwright** - Browser automation
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **Lucide React** - Icons

## Development Workflow

1. **Start Backend**: `.\start-backend.ps1`
2. **Start Frontend**: `.\start-frontend.ps1`
3. **Make Changes**: Edit files in `backend/app/` or `frontend/src/`
4. **Auto Reload**: Both servers auto-reload on file changes
5. **Test**: Access at `http://localhost:5173`
6. **Check Logs**: View backend logs in terminal, frontend in browser console

## Build & Deployment

### Backend
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```powershell
cd frontend
npm run build
# Output in dist/ folder
```

## Security Considerations

- ✅ Credentials never stored in code
- ✅ Environment variables for sensitive data
- ✅ Local-only data storage
- ✅ Session-based authentication
- ✅ CORS protection
- ✅ Input validation with Pydantic
- ✅ TypeScript type safety

## Performance Optimizations

- **Frontend**: React component memoization, lazy loading
- **Backend**: Async/await with Playwright, database indexing
- **Database**: Indexed queries on username, session_id
- **Browser**: Headless mode for faster automation

## Monitoring & Logging

- **Backend Logs**: Uvicorn console output
- **Database Logs**: `actions` table
- **Frontend Logs**: Browser console
- **Activity Log**: Real-time UI component

---

For questions about the project structure, see [CONTRIBUTING.md](CONTRIBUTING.md).
