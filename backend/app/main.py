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
from .instagram_sync import instagram_login, instagram_get_followers, instagram_get_following, instagram_unfollow_batch
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


class WhitelistRequest(BaseModel):
    usernames: List[str]
    reason: Optional[str] = None


class WhitelistResponse(BaseModel):
    success: bool
    added: List[str] = []
    already_whitelisted: List[str] = []
    not_found: List[str] = []


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
    limit: int = 999999,  # Very high limit = fetch all
    db: Session = Depends(get_db)
):
    """Get ALL followers list using synchronous Playwright.
    
    Will scroll through entire followers list to get complete data.
    """
    print(f"[FOLLOWERS] ========================================")
    print(f"[FOLLOWERS] Fetching ALL followers for: {username}")
    print(f"[FOLLOWERS] (Will scroll until complete - may take time)")
    print(f"[FOLLOWERS] ========================================")
    
    try:
        # Check if session exists and is active
        db_session = db.query(DBSession).filter(
            DBSession.session_id == session_id,
            DBSession.is_active == True
        ).first()
        
        if not db_session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        print(f"[FOLLOWERS] Session valid, fetching followers...")
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            instagram_get_followers,
            username,
            db_session.cookies,
            limit,
            False  # headless=False to see browser
        )
        
        if not result['success']:
            print(f"[FOLLOWERS] FAILED: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to fetch followers'))
        
        followers = result['followers']
        print(f"[FOLLOWERS] Successfully fetched {len(followers)} followers")
        
        # IMPORTANT: Reset all is_following_me flags to False before updating
        # This ensures stale data doesn't persist
        print(f"[FOLLOWERS] Resetting all is_following_me flags...")
        db.query(User).update({User.is_following_me: False})
        db.commit()
        
        # Store in database
        follower_usernames = set()
        for follower in followers:
            follower_usernames.add(follower['username'])
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
        
        print(f"[FOLLOWERS] Stored {len(follower_usernames)} unique followers")
        
        # Log action
        action = Action(
            action_type='fetch_followers',
            username=username,
            status='success',
            details={'count': len(followers)}
        )
        db.add(action)
        db.commit()
        
        print(f"[FOLLOWERS] SUCCESS! Stored in database.")
        return {
            "success": True,
            "count": len(followers),
            "followers": followers
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[FOLLOWERS] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/following/{username}")
async def get_following(
    username: str,
    session_id: str,
    limit: int = 999999,  # Very high limit = fetch all
    db: Session = Depends(get_db)
):
    """Get ALL following list using synchronous Playwright.
    
    Will scroll through entire following list to get complete data.
    """
    print(f"[FOLLOWING] ========================================")
    print(f"[FOLLOWING] Fetching ALL following for: {username}")
    print(f"[FOLLOWING] (Will scroll until complete - may take time)")
    print(f"[FOLLOWING] ========================================")
    
    try:
        # Check if session exists and is active
        db_session = db.query(DBSession).filter(
            DBSession.session_id == session_id,
            DBSession.is_active == True
        ).first()
        
        if not db_session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        print(f"[FOLLOWING] Session valid, fetching following...")
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            instagram_get_following,
            username,
            db_session.cookies,
            limit,
            False  # headless=False to see browser
        )
        
        if not result['success']:
            print(f"[FOLLOWING] FAILED: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to fetch following'))
        
        following = result['following']
        print(f"[FOLLOWING] Successfully fetched {len(following)} following")
        
        # IMPORTANT: Reset all i_am_following flags to False before updating
        # This ensures stale data doesn't persist
        print(f"[FOLLOWING] Resetting all i_am_following flags...")
        db.query(User).update({User.i_am_following: False})
        db.commit()
        
        # Store in database
        following_usernames = set()
        for followed_user in following:
            following_usernames.add(followed_user['username'])
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
        
        print(f"[FOLLOWING] Stored {len(following_usernames)} unique following users")
        
        # Log action
        action = Action(
            action_type='fetch_following',
            username=username,
            status='success',
            details={'count': len(following)}
        )
        db.add(action)
        db.commit()
        
        print(f"[FOLLOWING] SUCCESS! Stored in database.")
        return {
            "success": True,
            "count": len(following),
            "following": following
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[FOLLOWING] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analysis/complete")
async def complete_analysis(
    username: str,
    session_id: str,
    limit: int = 999999,  # Very high limit = fetch all users
    db: Session = Depends(get_db)
):
    """Perform complete analysis - fetch ALL followers and following, then identify non-followers.
    
    NOTE: This will scroll through ENTIRE lists to get complete data.
    May take several minutes for accounts with thousands of followers/following.
    """
    print(f"[COMPLETE ANALYSIS] ========================================")
    print(f"[COMPLETE ANALYSIS] Starting COMPLETE analysis for: {username}")
    print(f"[COMPLETE ANALYSIS] Will fetch ALL followers and following (may take time)")
    print(f"[COMPLETE ANALYSIS] ========================================")
    
    try:
        # Check session
        db_session = db.query(DBSession).filter(
            DBSession.session_id == session_id,
            DBSession.is_active == True
        ).first()
        
        if not db_session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        # Reset ALL flags first to ensure clean slate
        print(f"[COMPLETE ANALYSIS] Resetting all user flags...")
        db.query(User).update({
            User.is_following_me: False,
            User.i_am_following: False
        })
        db.commit()
        
        loop = asyncio.get_event_loop()
        
        # 1. Fetch followers
        print(f"[COMPLETE ANALYSIS] Step 1: Fetching followers...")
        followers_result = await loop.run_in_executor(
            executor,
            instagram_get_followers,
            username,
            db_session.cookies,
            limit,
            False
        )
        
        if not followers_result['success']:
            raise HTTPException(status_code=500, detail=f"Failed to fetch followers: {followers_result.get('error')}")
        
        followers = followers_result['followers']
        print(f"[COMPLETE ANALYSIS] Fetched {len(followers)} followers")
        
        # 2. Fetch following
        print(f"[COMPLETE ANALYSIS] Step 2: Fetching following...")
        following_result = await loop.run_in_executor(
            executor,
            instagram_get_following,
            username,
            db_session.cookies,
            limit,
            False
        )
        
        if not following_result['success']:
            raise HTTPException(status_code=500, detail=f"Failed to fetch following: {following_result.get('error')}")
        
        following = following_result['following']
        print(f"[COMPLETE ANALYSIS] Fetched {len(following)} following")
        
        # 3. Store followers in database
        print(f"[COMPLETE ANALYSIS] Step 3: Storing followers...")
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
                    user_id=follower['username'],
                    full_name=follower.get('full_name', ''),
                    is_verified=follower.get('is_verified', False),
                    is_following_me=True
                )
                db.add(new_user)
        
        # 4. Store following in database
        print(f"[COMPLETE ANALYSIS] Step 4: Storing following...")
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
        
        # Log actions
        db.add(Action(
            action_type='fetch_followers',
            username=username,
            status='success',
            details={'count': len(followers)}
        ))
        db.add(Action(
            action_type='fetch_following',
            username=username,
            status='success',
            details={'count': len(following)}
        ))
        
        db.commit()
        
        # Calculate and display statistics
        followers_set = set(f['username'] for f in followers)
        following_set = set(f['username'] for f in following)
        mutual = followers_set & following_set
        not_following_back = following_set - followers_set
        
        print(f"[COMPLETE ANALYSIS] ========================================")
        print(f"[COMPLETE ANALYSIS] Analysis complete!")
        print(f"[COMPLETE ANALYSIS] ========================================")
        print(f"[COMPLETE ANALYSIS] Followers: {len(followers)}")
        print(f"[COMPLETE ANALYSIS] Following: {len(following)}")
        print(f"[COMPLETE ANALYSIS] Mutual (follow each other): {len(mutual)}")
        print(f"[COMPLETE ANALYSIS] Not following back: {len(not_following_back)}")
        print(f"[COMPLETE ANALYSIS] ========================================")
        
        # Verify data was saved correctly
        db_followers = db.query(User).filter(User.is_following_me == True).count()
        db_following = db.query(User).filter(User.i_am_following == True).count()
        db_non_followers = db.query(User).filter(
            User.i_am_following == True,
            User.is_following_me == False
        ).count()
        
        print(f"[COMPLETE ANALYSIS] Database verification:")
        print(f"[COMPLETE ANALYSIS]   - Followers in DB: {db_followers}")
        print(f"[COMPLETE ANALYSIS]   - Following in DB: {db_following}")
        print(f"[COMPLETE ANALYSIS]   - Non-followers in DB: {db_non_followers}")
        print(f"[COMPLETE ANALYSIS] ========================================")
        
        return {
            "success": True,
            "followers_count": len(followers),
            "following_count": len(following),
            "message": "Analysis complete. Use /api/analysis/non-followers to get results."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[COMPLETE ANALYSIS] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/non-followers", response_model=AnalysisResponse)
async def get_non_followers(
    session_id: str,
    min_followers: int = 10000,
    exclude_verified: bool = True,
    db: Session = Depends(get_db)
):
    """Get list of users who don't follow back."""
    print(f"[NON-FOLLOWERS] ========================================")
    print(f"[NON-FOLLOWERS] Analyzing non-followers")
    print(f"[NON-FOLLOWERS] Filters: verified={exclude_verified}, min_followers={min_followers}")
    print(f"[NON-FOLLOWERS] ========================================")
    
    try:
        # Get totals first for debugging
        total_followers = db.query(User).filter(User.is_following_me == True).count()
        total_following = db.query(User).filter(User.i_am_following == True).count()
        
        print(f"[NON-FOLLOWERS] Total in database:")
        print(f"[NON-FOLLOWERS]   - Users following me: {total_followers}")
        print(f"[NON-FOLLOWERS]   - Users I'm following: {total_following}")
        
        # Get all users I'm following but who don't follow me
        # EXCLUDE whitelisted users
        query = db.query(User).filter(
            User.i_am_following == True,
            User.is_following_me == False,
            User.is_whitelisted == False  # Don't show whitelisted users
        )
        
        # Apply filters
        if exclude_verified:
            query = query.filter(User.is_verified == False)
        
        if min_followers > 0:
            query = query.filter(User.follower_count < min_followers)
        
        non_followers = query.all()
        
        print(f"[NON-FOLLOWERS] Found {len(non_followers)} non-followers after filtering")
        
        # Debug: show first few non-followers
        if len(non_followers) > 0:
            print(f"[NON-FOLLOWERS] First few results:")
            for user in non_followers[:5]:
                print(f"[NON-FOLLOWERS]   - @{user.username}: following_me={user.is_following_me}, i_follow={user.i_am_following}")
        
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
        print(f"[NON-FOLLOWERS] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/actions/unfollow", response_model=UnfollowResponse)
async def unfollow_users(
    request: UnfollowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Unfollow users using synchronous Playwright."""
    print(f"[UNFOLLOW] ========================================")
    print(f"[UNFOLLOW] Unfollow request for {len(request.usernames)} users")
    print(f"[UNFOLLOW] ========================================")
    
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
            print(f"[UNFOLLOW] Daily limit exceeded: {today_unfollows}/{settings.max_daily_unfollows}")
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit exceeded. Already unfollowed {today_unfollows} users today. Limit is {settings.max_daily_unfollows}."
            )
        
        print(f"[UNFOLLOW] Daily limit check passed: {today_unfollows}/{settings.max_daily_unfollows}")
        print(f"[UNFOLLOW] Running batch unfollow in thread pool...")
        
        # Run batch unfollow in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            instagram_unfollow_batch,
            request.usernames,
            db_session.cookies,
            settings.min_action_delay,
            settings.max_action_delay,
            False  # headless=False to see browser
        )
        
        if not result['success']:
            print(f"[UNFOLLOW] Batch unfollow completed with errors")
        
        batch_results = result['results']
        print(f"[UNFOLLOW] Processing {len(batch_results)} results...")
        
        # Log actions and update database
        errors = []
        for unfollow_result in batch_results:
            status = 'success' if unfollow_result['success'] else 'failed'
            action = Action(
                action_type='unfollow',
                username=unfollow_result['username'],
                status=status,
                details=unfollow_result
            )
            db.add(action)
            
            if unfollow_result['success']:
                # Update user in database
                user = db.query(User).filter(User.username == unfollow_result['username']).first()
                if user:
                    user.i_am_following = False
                    user.updated_at = datetime.utcnow()
                print(f"[UNFOLLOW] ✓ {unfollow_result['username']}")
            else:
                error_msg = f"{unfollow_result['username']}: {unfollow_result.get('error', 'Unknown error')}"
                errors.append(error_msg)
                print(f"[UNFOLLOW] ✗ {error_msg}")
        
        db.commit()
        
        print(f"[UNFOLLOW] ========================================")
        print(f"[UNFOLLOW] Complete! Success: {result['summary']['successful']}, Failed: {result['summary']['failed']}")
        print(f"[UNFOLLOW] ========================================")
        
        return UnfollowResponse(
            success=len(errors) == 0,
            results=batch_results,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[UNFOLLOW] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/api/whitelist/add", response_model=WhitelistResponse)
async def add_to_whitelist(
    request: WhitelistRequest,
    db: Session = Depends(get_db)
):
    """Add users to the allow-list (whitelist) - they won't appear in non-followers."""
    print(f"[WHITELIST] ========================================")
    print(f"[WHITELIST] Adding {len(request.usernames)} users to whitelist")
    print(f"[WHITELIST] Reason: {request.reason or 'No reason provided'}")
    print(f"[WHITELIST] ========================================")
    
    added = []
    already_whitelisted = []
    not_found = []
    
    try:
        for username in request.usernames:
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                # User doesn't exist in database - create them as whitelisted
                print(f"[WHITELIST] User @{username} not in database, creating...")
                new_user = User(
                    username=username,
                    user_id=username,
                    is_whitelisted=True,
                    whitelist_reason=request.reason
                )
                db.add(new_user)
                added.append(username)
            elif user.is_whitelisted:
                print(f"[WHITELIST] User @{username} already whitelisted")
                already_whitelisted.append(username)
            else:
                print(f"[WHITELIST] Adding @{username} to whitelist")
                user.is_whitelisted = True
                user.whitelist_reason = request.reason
                user.updated_at = datetime.utcnow()
                added.append(username)
        
        # Log action
        action = Action(
            action_type='whitelist_add',
            username=', '.join(request.usernames),
            status='success',
            details={
                'count': len(added),
                'reason': request.reason,
                'usernames': added
            }
        )
        db.add(action)
        db.commit()
        
        print(f"[WHITELIST] SUCCESS! Added: {len(added)}, Already whitelisted: {len(already_whitelisted)}")
        
        return WhitelistResponse(
            success=True,
            added=added,
            already_whitelisted=already_whitelisted,
            not_found=not_found
        )
        
    except Exception as e:
        print(f"[WHITELIST] EXCEPTION: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/whitelist/remove")
async def remove_from_whitelist(
    usernames: List[str],
    db: Session = Depends(get_db)
):
    """Remove users from the allow-list (whitelist)."""
    print(f"[WHITELIST] ========================================")
    print(f"[WHITELIST] Removing {len(usernames)} users from whitelist")
    print(f"[WHITELIST] ========================================")
    
    removed = []
    not_whitelisted = []
    not_found = []
    
    try:
        for username in usernames:
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                print(f"[WHITELIST] User @{username} not found in database")
                not_found.append(username)
            elif not user.is_whitelisted:
                print(f"[WHITELIST] User @{username} not whitelisted")
                not_whitelisted.append(username)
            else:
                print(f"[WHITELIST] Removing @{username} from whitelist")
                user.is_whitelisted = False
                user.whitelist_reason = None
                user.updated_at = datetime.utcnow()
                removed.append(username)
        
        # Log action
        action = Action(
            action_type='whitelist_remove',
            username=', '.join(usernames),
            status='success',
            details={
                'count': len(removed),
                'usernames': removed
            }
        )
        db.add(action)
        db.commit()
        
        print(f"[WHITELIST] SUCCESS! Removed: {len(removed)}")
        
        return {
            "success": True,
            "removed": removed,
            "not_whitelisted": not_whitelisted,
            "not_found": not_found
        }
        
    except Exception as e:
        print(f"[WHITELIST] EXCEPTION: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/whitelist")
async def get_whitelist(db: Session = Depends(get_db)):
    """Get all whitelisted users."""
    try:
        whitelisted_users = db.query(User).filter(User.is_whitelisted == True).all()
        
        return {
            "success": True,
            "count": len(whitelisted_users),
            "users": [
                {
                    "username": user.username,
                    "full_name": user.full_name or "",
                    "reason": user.whitelist_reason,
                    "is_following_me": user.is_following_me,
                    "i_am_following": user.i_am_following,
                    "added_at": user.updated_at.isoformat() if user.updated_at else None
                }
                for user in whitelisted_users
            ]
        }
        
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
        
        whitelisted_count = db.query(User).filter(User.is_whitelisted == True).count()
        
        return {
            "total_users": total_users,
            "total_followers": total_followers,
            "total_following": total_following,
            "non_followers": non_followers,
            "whitelisted_users": whitelisted_count,
            "today_unfollows": today_unfollows,
            "remaining_today": max(0, settings.max_daily_unfollows - today_unfollows),
            "daily_limit": settings.max_daily_unfollows
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
