"""
Database manager for Camera Privacy Manager
Handles SQLite database operations and schema management
"""
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from pathlib import Path

from models.data_models import User, LogEntry, IntrusionAttempt
from config import DATABASE_FILE


class DatabaseManager:
    """Manages database operations for the Camera Privacy Manager"""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager with optional custom database path"""
        self.db_path = db_path or str(DATABASE_FILE)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                self._create_tables(conn)
                self.logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create database tables"""
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Access logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Intrusion attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intrusion_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                media_path TEXT NOT NULL,
                ip_address TEXT
            )
        """)
        
        conn.commit()
    
    def create_user(self, username: str, password_hash: str) -> int:
        """Create a new user and return user ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                conn.commit()
                user_id = cursor.lastrowid
                self.logger.info(f"User created successfully: {username}")
                return user_id
        except sqlite3.IntegrityError:
            self.logger.error(f"User already exists: {username}")
            raise ValueError(f"User {username} already exists")
        except sqlite3.Error as e:
            self.logger.error(f"Failed to create user: {e}")
            raise
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve user by username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
                    (username,)
                )
                row = cursor.fetchone()
                if row:
                    return User(
                        id=row[0],
                        username=row[1],
                        password_hash=row[2],
                        created_at=datetime.fromisoformat(row[3])
                    )
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve user: {e}")
            raise
    
    def log_access(self, user_id: int, action: str) -> int:
        """Log camera access action"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO access_logs (user_id, action) VALUES (?, ?)",
                    (user_id, action)
                )
                conn.commit()
                log_id = cursor.lastrowid
                self.logger.info(f"Access logged: {action} for user {user_id}")
                return log_id
        except sqlite3.Error as e:
            self.logger.error(f"Failed to log access: {e}")
            raise
    
    def get_access_logs(self, user_id: int = None, limit: int = 100) -> List[LogEntry]:
        """Retrieve access logs, optionally filtered by user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if user_id:
                    cursor.execute(
                        "SELECT id, user_id, action, timestamp FROM access_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                        (user_id, limit)
                    )
                else:
                    cursor.execute(
                        "SELECT id, user_id, action, timestamp FROM access_logs ORDER BY timestamp DESC LIMIT ?",
                        (limit,)
                    )
                
                logs = []
                for row in cursor.fetchall():
                    logs.append(LogEntry(
                        id=row[0],
                        user_id=row[1],
                        action=row[2],
                        timestamp=datetime.fromisoformat(row[3])
                    ))
                return logs
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve access logs: {e}")
            raise
    
    def log_intrusion_attempt(self, media_path: str, ip_address: str = None) -> int:
        """Log intrusion attempt"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO intrusion_attempts (media_path, ip_address) VALUES (?, ?)",
                    (media_path, ip_address)
                )
                conn.commit()
                intrusion_id = cursor.lastrowid
                self.logger.warning(f"Intrusion attempt logged: {media_path}")
                return intrusion_id
        except sqlite3.Error as e:
            self.logger.error(f"Failed to log intrusion attempt: {e}")
            raise
    
    def get_intrusion_attempts(self, limit: int = 50) -> List[IntrusionAttempt]:
        """Retrieve intrusion attempts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, timestamp, media_path, ip_address FROM intrusion_attempts ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                
                attempts = []
                for row in cursor.fetchall():
                    attempts.append(IntrusionAttempt(
                        id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        media_path=row[2],
                        ip_address=row[3]
                    ))
                return attempts
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve intrusion attempts: {e}")
            raise
    
    def close(self):
        """Close database connection (for cleanup)"""
        # SQLite connections are automatically closed when using context manager
        pass
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get user count: {e}")
            raise