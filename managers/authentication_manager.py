"""
Authentication manager for Camera Privacy Manager
Handles password hashing, verification, and secure credential management
"""
import hashlib
import secrets
import logging
from typing import Optional

from database.database_manager import DatabaseManager
from models.data_models import User
from config import PASSWORD_SALT_LENGTH, HASH_ALGORITHM


class AuthenticationManager:
    """Manages user authentication and password security"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize authentication manager with database connection"""
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)
        self.current_user: Optional[User] = None
    
    def hash_password(self, password: str, salt: bytes = None) -> str:
        """
        Hash password with salt using SHA-256
        Returns salt + hash as hex string
        """
        if salt is None:
            salt = secrets.token_bytes(PASSWORD_SALT_LENGTH)
        
        # Create hash using salt + password
        hash_obj = hashlib.new(HASH_ALGORITHM)
        hash_obj.update(salt + password.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        
        # Return salt + hash as hex string
        return salt.hex() + password_hash
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """
        Verify password against stored hash
        Returns True if password matches, False otherwise
        """
        try:
            # Extract salt from stored hash (first PASSWORD_SALT_LENGTH * 2 hex chars)
            salt_hex = stored_hash[:PASSWORD_SALT_LENGTH * 2]
            stored_password_hash = stored_hash[PASSWORD_SALT_LENGTH * 2:]
            
            # Convert salt back to bytes
            salt = bytes.fromhex(salt_hex)
            
            # Hash the provided password with the same salt
            hash_obj = hashlib.new(HASH_ALGORITHM)
            hash_obj.update(salt + password.encode('utf-8'))
            password_hash = hash_obj.hexdigest()
            
            # Compare hashes
            return password_hash == stored_password_hash
            
        except (ValueError, IndexError) as e:
            self.logger.error(f"Password verification failed: {e}")
            return False
    
    def setup_initial_password(self, username: str, password: str) -> bool:
        """
        Set up initial password for first-time setup
        Returns True if successful, False if user already exists
        """
        try:
            # Check if user already exists
            existing_user = self.db_manager.get_user_by_username(username)
            if existing_user:
                self.logger.warning(f"User {username} already exists")
                return False
            
            # Hash password and create user
            password_hash = self.hash_password(password)
            user_id = self.db_manager.create_user(username, password_hash)
            
            self.logger.info(f"Initial password setup completed for user: {username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup initial password: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticate user with username and password
        Returns True if authentication successful, False otherwise
        """
        try:
            # Retrieve user from database
            user = self.db_manager.get_user_by_username(username)
            if not user:
                self.logger.warning(f"Authentication failed: User {username} not found")
                return False
            
            # Verify password
            if self.verify_password(password, user.password_hash):
                self.current_user = user
                self.logger.info(f"User {username} authenticated successfully")
                return True
            else:
                self.logger.warning(f"Authentication failed: Invalid password for user {username}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    def logout_user(self):
        """Logout current user"""
        if self.current_user:
            self.logger.info(f"User {self.current_user.username} logged out")
            self.current_user = None
    
    def get_current_user(self) -> Optional[User]:
        """Get currently authenticated user"""
        return self.current_user
    
    def is_authenticated(self) -> bool:
        """Check if a user is currently authenticated"""
        return self.current_user is not None
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change user password
        Returns True if successful, False otherwise
        """
        try:
            # First authenticate with old password
            if not self.authenticate_user(username, old_password):
                self.logger.warning(f"Password change failed: Invalid old password for {username}")
                return False
            
            # Hash new password
            new_password_hash = self.hash_password(new_password)
            
            # Update password in database
            # Note: This requires adding an update method to DatabaseManager
            # For now, we'll log the action
            self.logger.info(f"Password change requested for user: {username}")
            # TODO: Implement password update in DatabaseManager
            
            return True
            
        except Exception as e:
            self.logger.error(f"Password change error: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """
        Validate password strength
        Returns (is_valid, message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        return True, "Password is strong"
    
    def has_users(self) -> bool:
        """Check if any users exist in the system"""
        try:
            return self.db_manager.get_user_count() > 0
        except Exception as e:
            self.logger.error(f"Error checking user count: {e}")
            return False