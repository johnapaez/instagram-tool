"""Database models."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from datetime import datetime
from .database import Base


class User(Base):
    """Instagram user model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    user_id = Column(String, unique=True)
    full_name = Column(String, nullable=True)
    profile_pic_url = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    is_following_me = Column(Boolean, default=False)
    i_am_following = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Action(Base):
    """User action log."""
    
    __tablename__ = "actions"
    
    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String)  # 'unfollow', 'fetch_followers', etc.
    username = Column(String)
    user_id = Column(String, nullable=True)
    status = Column(String)  # 'success', 'failed', 'skipped'
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    """Instagram session data."""
    
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    username = Column(String)
    cookies = Column(JSON)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class UnfollowQueue(Base):
    """Queue of users to unfollow."""
    
    __tablename__ = "unfollow_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    user_id = Column(String)
    full_name = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    follower_count = Column(Integer, default=0)
    status = Column(String, default='pending')  # 'pending', 'processing', 'completed', 'failed'
    priority = Column(Integer, default=0)
    added_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
