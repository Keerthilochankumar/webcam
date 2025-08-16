"""
Core data models for Camera Privacy Manager
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User data model for authentication and identification"""
    id: int
    username: str
    password_hash: str
    created_at: datetime


@dataclass
class LogEntry:
    """Log entry data model for camera access tracking"""
    id: int
    user_id: int
    action: str
    timestamp: datetime


@dataclass
class IntrusionAttempt:
    """Intrusion attempt data model for security events"""
    id: int
    timestamp: datetime
    media_path: str
    ip_address: Optional[str] = None