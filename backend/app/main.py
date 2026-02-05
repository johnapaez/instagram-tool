"""FastAPI main application."""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime, timedelta
import asyncio
import uuid
import sys

# Fix for Windows - use WindowsProactorEventLoopPolicy for subprocess support
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from .config import settings
from .database import get_db, init_db
from .models import User, Action, Session as DBSession, UnfollowQueue
from .instagram_sync import instagram_login
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(
    title="Instagram Follower Management API",
    description="API for managing Instagram followers",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot instance (in production, use a proper session manager)
active_bots = {}

# Thread pool for synchronous Playwright operations
executor = ThreadPoolExecutor(max_workers=3)


# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    username: Optional[str] = None
    error: Optional[str] = None


class UserInfo(BaseModel):
    username: str
    full_name: Optional[str] = None
    is_verified: bool = False
    follower_count: int = 0
    is_following_me: bool = False
    i_am_following: bool = False


class AnalysisResponse(BaseModel):
    total_followers: int
    total_following: int
    non_followers: List[UserInfo]
    non_followers_count: int


class UnfollowRequest(BaseModel):
    usernames: List[str]
    session_id: str


class UnfollowResponse(BaseModel):
    success: bool
    results: List[dict]
    errors: List[str] = []


class ActionLog(BaseModel):
    id: int
    action_type: str
    username: str
    status: str
    created_at: datetime
    details: Optional[dict] = None

    class Config:
        from_attributes = True


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    for bot in active_bots.values():
        try:
            await bot.close()
        except:
            pass


# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Instagram Follower Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login to Instagram using synchronous Playwright."""
    print(f"[LOGIN] ========================================")
    print(f"[LOGIN] Received login request for user: {request.username}")
    print(f"[LOGIN] Using synchronous Playwright API (Windows compatible)")
    print(f"[LOGIN] ========================================")
    
    try:
        print(f"[LOGIN] Running Playwright login in thread pool...")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            instagram_login,
            request.username,
            request.password,
            False  # headless=False to see browser
        )
        
        print(f"[LOGIN] Login completed: success={result['success']}")
        
        if result['success']:
            # Create session
            session_id = str(uuid.uuid4())
            
            db_session = DBSession(
                session_id=session_id,
                username=request.username,
                cookies=result['cookies'],
                is_active=True
            )
            db.add(db_session)
            
            # Log action
            action = Action(
                action_type='login',
                username=request.username,
                status='success',
                details={'session_id': session_id}
            )
            db.add(action)
            db.commit()
            
            print(f"[LOGIN] SUCCESS! Session created: {session_id}")
            return LoginResponse(
                success=True,
                session_id=session_id,
                username=request.username
            )
        else:
            error_msg = result.get('error', 'Login failed - no error details provided')
            print(f"[LOGIN] FAILED: {error_msg}")
            return LoginResponse(
                success=False,
                error=error_msg
            )
            
    except Exception as e:
        error_detail = str(e)
        print(f"[LOGIN] ========================================")
        print(f"[LOGIN] EXCEPTION OCCURRED!")
        print(f"[LOGIN] Error type: {type(e).__name__}")
        print(f"[LOGIN] Error message: {error_detail}")
        print(f"[LOGIN] ========================================")
        import traceback
        traceback.print_exc()
        
        return LoginResponse(
            success=False,
            error=f"Server error: {error_detail}"
        )


@app.post("/api/auth/logout")
async def logout(session_id: str, db: Session = Depends(get_db)):
    """Logout and close session."""
    try:
        # Close bot if exists
        if session_id in active_bots:
            bot = active_bots[session_id]
            await bot.close()
            del active_bots[session_id]
        
        # Deactivate session in database
        db_session = db.query(DBSession).filter(DBSession.session_id == session_id).first()
        if db_session:
            db_session.is_active = False
            db.commit()
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/followers/{username}")
async def get_followers(
    username: str,
    session_id: str,
    limit: int = 500,
    db: Session = Depends(get_db)
):
    """Get followers list - TEMPORARILY DISABLED."""
    raise HTTPException(
        status_code=501,
        detail="Follower analysis feature is being updated for Windows compatibility. Login is working! Full features coming soon."
    )
    
    # Original code commented out for now
    """
    try:
        # Check if session exists and is active
        db_session = db.query(DBSession).filter(
            DBSession.session_id == session_id,
            DBSession.is_active == True
        ).first()
        
        if not db_session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        # Get or create bot
        if session_id not in active_bots:
            # TODO: Implement with sync Playwright
            pass
        else:
            bot = active_bots[session_id]
        
        # Fetch followers
        followers = await bot.get_followers(username, limit)
        
        # Store in database
        for follower in followers:
            existing_user = db.query(User).filter(User.username == follower['username']).first()
            if existing_user:
                existing_user.full_name = follower.get('full_name', '')
                existing_user.is_verified = follower.get('is_verified', False)
                existing_user.is_following_me = True
                existing_user.updated_at = datetime.utcnow()
            else:
                new_user = User(
                    username=follower['username'],
                    user_id=follower['username'],  # We'll use username as ID for now
                    full_name=follower.get('full_name', ''),
                    is_verified=follower.get('is_verified', False),
                    is_following_me=True
                )
                db.add(new_user)
        
        # Log action
        action = Action(
            action_type='fetch_followers',
            username=username,
            status='success',
            details={'count': len(followers)}
        )
        db.add(action)
        db.commit()
        
        return {
            "success": True,
            "count": len(followers),
            "followers": followers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    """


@app.get("/api/analysis/following/{username}")
async def get_following(
    username: str,
    session_id: str,
    limit: int = 500,
    db: Session = Depends(get_db)
):
    """Get following list - TEMPORARILY DISABLED."""
    raise HTTPException(
        status_code=501,
        detail="Following analysis feature is being updated for Windows compatibility. Login is working! Full features coming soon."
    )
    
    """
    try:
        db_session = db.query(DBSession).filter(
            DBSession.session_id == session_id,
            DBSession.is_active == True
        ).first()
        
        if not db_session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        if session_id not in active_bots:
            bot = InstagramBot()
            await bot.start(headless=True)
            await bot.load_session(db_session.cookies)
            active_bots[session_id] = bot
        else:
            bot = active_bots[session_id]
        
        following = await bot.get_following(username, limit)
        
        # Store in database
        for followed_user in following:
            existing_user = db.query(User).filter(User.username == followed_user['username']).first()
            if existing_user:
                existing_user.full_name = followed_user.get('full_name', '')
                existing_user.is_verified = followed_user.get('is_verified', False)
                existing_user.i_am_following = True
                existing_user.updated_at = datetime.utcnow()
            else:
                new_user = User(
                    username=followed_user['username'],
                    user_id=followed_user['username'],
                    full_name=followed_user.get('full_name', ''),
                    is_verified=followed_user.get('is_verified', False),
                    i_am_following=True
                )
                db.add(new_user)
        
        action = Action(
            action_type='fetch_following',
            username=username,
            status='success',
            details={'count': len(following)}
        )
        db.add(action)
        db.commit()
        
        return {
            "success": True,
            "count": len(following),
            "following": following
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    """


@app.get("/api/analysis/non-followers", response_model=AnalysisResponse)
async def get_non_followers(
    session_id: str,
    min_followers: int = 10000,
    exclude_verified: bool = True,
    db: Session = Depends(get_db)
):
    """Get list of users who don't follow back."""
    try:
        # Get all users I'm following but who don't follow me
        query = db.query(User).filter(
            User.i_am_following == True,
            User.is_following_me == False
        )
        
        # Apply filters
        if exclude_verified:
            query = query.filter(User.is_verified == False)
        
        if min_followers > 0:
            query = query.filter(User.follower_count < min_followers)
        
        non_followers = query.all()
        
        # Get totals
        total_followers = db.query(User).filter(User.is_following_me == True).count()
        total_following = db.query(User).filter(User.i_am_following == True).count()
        
        return AnalysisResponse(
            total_followers=total_followers,
            total_following=total_following,
            non_followers=[
                UserInfo(
                    username=user.username,
                    full_name=user.full_name or "",
                    is_verified=user.is_verified,
                    follower_count=user.follower_count,
                    is_following_me=user.is_following_me,
                    i_am_following=user.i_am_following
                )
                for user in non_followers
            ],
            non_followers_count=len(non_followers)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/actions/unfollow", response_model=UnfollowResponse)
async def unfollow_users(
    request: UnfollowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Unfollow users - TEMPORARILY DISABLED."""
    raise HTTPException(
        status_code=501,
        detail="Unfollow feature is being updated for Windows compatibility. Login is working! Full features coming soon."
    )
    
    """
    try:
        # Check session
        db_session = db.query(DBSession).filter(
            DBSession.session_id == request.session_id,
            DBSession.is_active == True
        ).first()
        
        if not db_session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        # Check daily limit
        today = datetime.utcnow().date()
        today_unfollows = db.query(Action).filter(
            Action.action_type == 'unfollow',
            Action.status == 'success',
            Action.created_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        if today_unfollows + len(request.usernames) > settings.max_daily_unfollows:
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit exceeded. Already unfollowed {today_unfollows} users today. Limit is {settings.max_daily_unfollows}."
            )
        
        # Get bot
        if request.session_id not in active_bots:
            bot = InstagramBot()
            await bot.start(headless=True)
            await bot.load_session(db_session.cookies)
            active_bots[request.session_id] = bot
        else:
            bot = active_bots[request.session_id]
        
        # Unfollow users
        results = await bot.unfollow_batch(
            request.usernames,
            settings.min_action_delay,
            settings.max_action_delay
        )
        
        # Log actions
        errors = []
        for result in results:
            status = 'success' if result['success'] else 'failed'
            action = Action(
                action_type='unfollow',
                username=result['username'],
                status=status,
                details=result
            )
            db.add(action)
            
            if result['success']:
                # Update user in database
                user = db.query(User).filter(User.username == result['username']).first()
                if user:
                    user.i_am_following = False
                    user.updated_at = datetime.utcnow()
            else:
                errors.append(f"{result['username']}: {result.get('error', 'Unknown error')}")
        
        db.commit()
        
        return UnfollowResponse(
            success=len(errors) == 0,
            results=results,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    """


@app.get("/api/logs", response_model=List[ActionLog])
async def get_logs(
    limit: int = 100,
    action_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get action logs."""
    try:
        query = db.query(Action).order_by(Action.created_at.desc())
        
        if action_type:
            query = query.filter(Action.action_type == action_type)
        
        logs = query.limit(limit).all()
        
        return logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get usage statistics."""
    try:
        today = datetime.utcnow().date()
        
        total_users = db.query(User).count()
        total_followers = db.query(User).filter(User.is_following_me == True).count()
        total_following = db.query(User).filter(User.i_am_following == True).count()
        non_followers = db.query(User).filter(
            User.i_am_following == True,
            User.is_following_me == False
        ).count()
        
        today_unfollows = db.query(Action).filter(
            Action.action_type == 'unfollow',
            Action.status == 'success',
            Action.created_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        return {
            "total_users": total_users,
            "total_followers": total_followers,
            "total_following": total_following,
            "non_followers": non_followers,
            "today_unfollows": today_unfollows,
            "remaining_today": max(0, settings.max_daily_unfollows - today_unfollows),
            "daily_limit": settings.max_daily_unfollows
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
