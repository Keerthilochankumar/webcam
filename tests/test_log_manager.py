"""
Unit tests for LogManager
"""
import unittest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from managers.log_manager import LogManager
from database.database_manager import DatabaseManager
from models.data_models import LogEntry, IntrusionAttempt, User


class TestLogManager(unittest.TestCase):
    """Test cases for LogManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.log_manager = LogManager(self.db_manager)
        
        # Create a test user
        self.test_user_id = self.db_manager.create_user("testuser", "hashed_password")
    
    def tearDown(self):
        """Clean up test environment"""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_log_camera_access(self):
        """Test logging camera access"""
        result = self.log_manager.log_camera_access(self.test_user_id, "CAMERA_ENABLED")
        self.assertTrue(result)
        
        # Verify log was created
        logs = self.log_manager.get_access_logs(self.test_user_id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "CAMERA_ENABLED")
        self.assertEqual(logs[0].user_id, self.test_user_id)
    
    def test_log_camera_access_with_timestamp(self):
        """Test logging camera access with custom timestamp"""
        custom_timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = self.log_manager.log_camera_access(
            self.test_user_id, 
            "CAMERA_DISABLED", 
            custom_timestamp
        )
        self.assertTrue(result)
        
        logs = self.log_manager.get_access_logs(self.test_user_id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "CAMERA_DISABLED")
    
    def test_get_access_logs(self):
        """Test retrieving access logs"""
        # Log multiple actions
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_ENABLED")
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_DISABLED")
        self.log_manager.log_camera_access(self.test_user_id, "VIEW_LOGS")
        
        # Get all logs for user
        logs = self.log_manager.get_access_logs(self.test_user_id)
        self.assertEqual(len(logs), 3)
        
        # Logs should be in reverse chronological order (most recent first)
        self.assertEqual(logs[0].action, "VIEW_LOGS")
        self.assertEqual(logs[1].action, "CAMERA_DISABLED")
        self.assertEqual(logs[2].action, "CAMERA_ENABLED")
    
    def test_get_access_logs_with_limit(self):
        """Test retrieving access logs with limit"""
        # Log multiple actions
        for i in range(5):
            self.log_manager.log_camera_access(self.test_user_id, f"ACTION_{i}")
        
        # Get limited logs
        logs = self.log_manager.get_access_logs(self.test_user_id, limit=3)
        self.assertEqual(len(logs), 3)
    
    def test_get_access_logs_all_users(self):
        """Test retrieving access logs for all users"""
        # Create another user
        user2_id = self.db_manager.create_user("testuser2", "hashed_password2")
        
        # Log actions for both users
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_ENABLED")
        self.log_manager.log_camera_access(user2_id, "CAMERA_DISABLED")
        
        # Get all logs (no user filter)
        logs = self.log_manager.get_access_logs()
        self.assertEqual(len(logs), 2)
        
        # Get logs for specific user
        user1_logs = self.log_manager.get_access_logs(self.test_user_id)
        self.assertEqual(len(user1_logs), 1)
        self.assertEqual(user1_logs[0].action, "CAMERA_ENABLED")
    
    def test_log_intrusion_attempt(self):
        """Test logging intrusion attempt"""
        media_path = "/path/to/intrusion_video.avi"
        ip_address = "192.168.1.100"
        
        result = self.log_manager.log_intrusion_attempt(media_path, ip_address=ip_address)
        self.assertTrue(result)
        
        # Verify intrusion log was created
        intrusion_logs = self.log_manager.get_intrusion_logs()
        self.assertEqual(len(intrusion_logs), 1)
        self.assertEqual(intrusion_logs[0].media_path, media_path)
        self.assertEqual(intrusion_logs[0].ip_address, ip_address)
    
    def test_log_intrusion_attempt_with_timestamp(self):
        """Test logging intrusion attempt with custom timestamp"""
        media_path = "/path/to/intrusion_photo.jpg"
        custom_timestamp = datetime(2023, 1, 1, 15, 30, 0)
        
        result = self.log_manager.log_intrusion_attempt(
            media_path, 
            timestamp=custom_timestamp
        )
        self.assertTrue(result)
        
        intrusion_logs = self.log_manager.get_intrusion_logs()
        self.assertEqual(len(intrusion_logs), 1)
        self.assertEqual(intrusion_logs[0].media_path, media_path)
    
    def test_get_intrusion_logs(self):
        """Test retrieving intrusion logs"""
        # Log multiple intrusion attempts
        self.log_manager.log_intrusion_attempt("/path/to/video1.avi", ip_address="192.168.1.100")
        self.log_manager.log_intrusion_attempt("/path/to/video2.avi", ip_address="192.168.1.101")
        
        intrusion_logs = self.log_manager.get_intrusion_logs()
        self.assertEqual(len(intrusion_logs), 2)
        
        # Should be in reverse chronological order
        self.assertEqual(intrusion_logs[0].media_path, "/path/to/video2.avi")
        self.assertEqual(intrusion_logs[1].media_path, "/path/to/video1.avi")
    
    def test_log_authentication_attempt_success(self):
        """Test logging successful authentication attempt"""
        result = self.log_manager.log_authentication_attempt("testuser", success=True)
        self.assertTrue(result)
        
        logs = self.log_manager.get_access_logs(self.test_user_id)
        self.assertEqual(len(logs), 1)
        self.assertTrue(logs[0].action.startswith("AUTH_SUCCESS_"))
    
    def test_log_authentication_attempt_failure(self):
        """Test logging failed authentication attempt"""
        result = self.log_manager.log_authentication_attempt("nonexistent", success=False)
        self.assertTrue(result)
        
        # Failed attempts are logged with user_id -1
        logs = self.log_manager.get_access_logs(-1)
        self.assertEqual(len(logs), 1)
        self.assertTrue(logs[0].action.startswith("AUTH_FAILED_"))
    
    def test_log_system_event(self):
        """Test logging system events"""
        result = self.log_manager.log_system_event(
            self.test_user_id, 
            "SYSTEM_STARTUP", 
            "Admin privileges granted"
        )
        self.assertTrue(result)
        
        logs = self.log_manager.get_access_logs(self.test_user_id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "SYSTEM_STARTUP_Admin privileges granted")
    
    def test_log_system_event_no_details(self):
        """Test logging system events without details"""
        result = self.log_manager.log_system_event(self.test_user_id, "CAMERA_STATUS_CHECK")
        self.assertTrue(result)
        
        logs = self.log_manager.get_access_logs(self.test_user_id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "CAMERA_STATUS_CHECK")
    
    def test_get_logs_by_date_range(self):
        """Test retrieving logs by date range"""
        # Create logs with different timestamps
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        # Log actions at different times
        self.log_manager.log_camera_access(self.test_user_id, "OLD_ACTION", yesterday)
        self.log_manager.log_camera_access(self.test_user_id, "CURRENT_ACTION", now)
        self.log_manager.log_camera_access(self.test_user_id, "FUTURE_ACTION", tomorrow)
        
        # Get logs for today only
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        logs = self.log_manager.get_logs_by_date_range(start_of_today, end_of_today, self.test_user_id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "CURRENT_ACTION")
    
    def test_get_logs_by_action(self):
        """Test retrieving logs by action pattern"""
        # Log various actions
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_ENABLED")
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_DISABLED")
        self.log_manager.log_camera_access(self.test_user_id, "VIEW_LOGS")
        self.log_manager.log_camera_access(self.test_user_id, "AUTH_SUCCESS_testuser")
        
        # Search for camera-related actions
        camera_logs = self.log_manager.get_logs_by_action("CAMERA", self.test_user_id)
        self.assertEqual(len(camera_logs), 2)
        
        # Search for auth-related actions
        auth_logs = self.log_manager.get_logs_by_action("AUTH", self.test_user_id)
        self.assertEqual(len(auth_logs), 1)
    
    def test_format_log_entry(self):
        """Test formatting log entry for display"""
        # Create a log entry
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_ENABLED")
        logs = self.log_manager.get_access_logs(self.test_user_id)
        
        formatted = self.log_manager.format_log_entry(logs[0])
        self.assertIn("CAMERA_ENABLED", formatted)
        self.assertIn(str(self.test_user_id), formatted)
        self.assertIn(logs[0].timestamp.strftime("%Y-%m-%d"), formatted)
    
    def test_format_logs_for_display(self):
        """Test formatting multiple logs for display"""
        # Create multiple log entries
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_ENABLED")
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_DISABLED")
        
        logs = self.log_manager.get_access_logs(self.test_user_id)
        formatted_logs = self.log_manager.format_logs_for_display(logs)
        
        self.assertEqual(len(formatted_logs), 2)
        self.assertIn("CAMERA_DISABLED", formatted_logs[0])  # Most recent first
        self.assertIn("CAMERA_ENABLED", formatted_logs[1])
    
    def test_get_log_statistics(self):
        """Test getting log statistics"""
        # Create various log entries
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_ENABLED")
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_DISABLED")
        self.log_manager.log_camera_access(self.test_user_id, "VIEW_LOGS")
        self.log_manager.log_intrusion_attempt("/path/to/video.avi")
        
        stats = self.log_manager.get_log_statistics(self.test_user_id)
        
        self.assertEqual(stats['total_access_logs'], 3)
        self.assertEqual(stats['total_intrusion_attempts'], 1)
        self.assertIn('CAMERA', stats['action_breakdown'])
        self.assertIn('VIEW', stats['action_breakdown'])
        self.assertIsNotNone(stats['latest_activity'])
        self.assertEqual(stats['user_filter'], self.test_user_id)
    
    def test_get_log_statistics_all_users(self):
        """Test getting log statistics for all users"""
        # Create log entries for multiple users
        user2_id = self.db_manager.create_user("testuser2", "hashed_password2")
        
        self.log_manager.log_camera_access(self.test_user_id, "CAMERA_ENABLED")
        self.log_manager.log_camera_access(user2_id, "CAMERA_DISABLED")
        
        stats = self.log_manager.get_log_statistics()  # No user filter
        
        self.assertEqual(stats['total_access_logs'], 2)
        self.assertIsNone(stats['user_filter'])
    
    @patch.object(DatabaseManager, 'log_access')
    def test_log_camera_access_database_error(self, mock_log_access):
        """Test handling database errors during logging"""
        mock_log_access.side_effect = Exception("Database error")
        
        result = self.log_manager.log_camera_access(self.test_user_id, "CAMERA_ENABLED")
        self.assertFalse(result)
    
    @patch.object(DatabaseManager, 'get_access_logs')
    def test_get_access_logs_database_error(self, mock_get_logs):
        """Test handling database errors during log retrieval"""
        mock_get_logs.side_effect = Exception("Database error")
        
        logs = self.log_manager.get_access_logs(self.test_user_id)
        self.assertEqual(len(logs), 0)


if __name__ == '__main__':
    unittest.main()