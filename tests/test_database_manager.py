"""
Unit tests for DatabaseManager
"""
import unittest
import tempfile
import os
from datetime import datetime

from database.database_manager import DatabaseManager
from models.data_models import User, LogEntry, IntrusionAttempt


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_create_user(self):
        """Test user creation"""
        user_id = self.db_manager.create_user("testuser", "hashed_password")
        self.assertIsInstance(user_id, int)
        self.assertGreater(user_id, 0)
    
    def test_create_duplicate_user(self):
        """Test creating duplicate user raises error"""
        self.db_manager.create_user("testuser", "hashed_password")
        with self.assertRaises(ValueError):
            self.db_manager.create_user("testuser", "another_password")
    
    def test_get_user_by_username(self):
        """Test retrieving user by username"""
        # Create user
        user_id = self.db_manager.create_user("testuser", "hashed_password")
        
        # Retrieve user
        user = self.db_manager.get_user_by_username("testuser")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, user_id)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.password_hash, "hashed_password")
        self.assertIsInstance(user.created_at, datetime)
    
    def test_get_nonexistent_user(self):
        """Test retrieving non-existent user returns None"""
        user = self.db_manager.get_user_by_username("nonexistent")
        self.assertIsNone(user)
    
    def test_log_access(self):
        """Test logging camera access"""
        # Create user first
        user_id = self.db_manager.create_user("testuser", "hashed_password")
        
        # Log access
        log_id = self.db_manager.log_access(user_id, "CAMERA_ENABLED")
        self.assertIsInstance(log_id, int)
        self.assertGreater(log_id, 0)
    
    def test_get_access_logs(self):
        """Test retrieving access logs"""
        # Create user and log access
        user_id = self.db_manager.create_user("testuser", "hashed_password")
        self.db_manager.log_access(user_id, "CAMERA_ENABLED")
        self.db_manager.log_access(user_id, "CAMERA_DISABLED")
        
        # Retrieve logs
        logs = self.db_manager.get_access_logs(user_id)
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0].action, "CAMERA_DISABLED")  # Most recent first
        self.assertEqual(logs[1].action, "CAMERA_ENABLED")
        self.assertEqual(logs[0].user_id, user_id)
    
    def test_log_intrusion_attempt(self):
        """Test logging intrusion attempt"""
        intrusion_id = self.db_manager.log_intrusion_attempt("/path/to/media.mp4", "192.168.1.100")
        self.assertIsInstance(intrusion_id, int)
        self.assertGreater(intrusion_id, 0)
    
    def test_get_intrusion_attempts(self):
        """Test retrieving intrusion attempts"""
        # Log intrusion attempts
        self.db_manager.log_intrusion_attempt("/path/to/media1.mp4", "192.168.1.100")
        self.db_manager.log_intrusion_attempt("/path/to/media2.mp4", "192.168.1.101")
        
        # Retrieve attempts
        attempts = self.db_manager.get_intrusion_attempts()
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0].media_path, "/path/to/media2.mp4")  # Most recent first
        self.assertEqual(attempts[1].media_path, "/path/to/media1.mp4")
        self.assertEqual(attempts[0].ip_address, "192.168.1.101")
    
    def test_get_user_count(self):
        """Test getting user count"""
        # Initially no users
        self.assertEqual(self.db_manager.get_user_count(), 0)
        
        # Create users
        self.db_manager.create_user("user1", "hash1")
        self.assertEqual(self.db_manager.get_user_count(), 1)
        
        self.db_manager.create_user("user2", "hash2")
        self.assertEqual(self.db_manager.get_user_count(), 2)


if __name__ == '__main__':
    unittest.main()