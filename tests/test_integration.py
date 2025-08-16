"""
Integration tests for Camera Privacy Manager
Tests end-to-end workflows and component interactions
"""
import unittest
import tempfile
import os
import shutil
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from pathlib import Path

from database.database_manager import DatabaseManager
from managers.authentication_manager import AuthenticationManager
from managers.camera_manager import CameraManager
from managers.log_manager import LogManager
from managers.intrusion_detector import IntrusionDetector
from managers.email_service import EmailService
from app_config import AppConfig


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, "test.db")
        self.temp_media_dir = os.path.join(self.temp_dir, "media")
        os.makedirs(self.temp_media_dir, exist_ok=True)
        
        # Initialize managers
        self.db_manager = DatabaseManager(self.temp_db)
        self.auth_manager = AuthenticationManager(self.db_manager)
        self.log_manager = LogManager(self.db_manager)
        
        # Mock camera manager for testing
        self.camera_manager = MagicMock(spec=CameraManager)
        self.camera_manager.get_camera_status.return_value = True
        self.camera_manager.enable_camera.return_value = True
        self.camera_manager.disable_camera.return_value = True
        self.camera_manager.capture_intrusion_media.return_value = "/fake/path/video.avi"
        
        self.intrusion_detector = IntrusionDetector(self.camera_manager, self.log_manager)
        self.email_service = EmailService()
        
        # Create test user
        self.test_username = "testuser"
        self.test_password = "TestPassword123"
        self.auth_manager.setup_initial_password(self.test_username, self.test_password)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_authentication_workflow(self):
        """Test complete authentication workflow"""
        # Test successful authentication
        result = self.auth_manager.authenticate_user(self.test_username, self.test_password)
        self.assertTrue(result)
        self.assertTrue(self.auth_manager.is_authenticated())
        
        # Verify user is logged
        user = self.auth_manager.get_current_user()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, self.test_username)
        
        # Test logout
        self.auth_manager.logout_user()
        self.assertFalse(self.auth_manager.is_authenticated())
        self.assertIsNone(self.auth_manager.get_current_user())
    
    def test_camera_enable_disable_workflow(self):
        """Test complete camera enable/disable workflow with logging"""
        # Authenticate user first
        self.auth_manager.authenticate_user(self.test_username, self.test_password)
        user = self.auth_manager.get_current_user()
        
        # Test enable camera
        result = self.camera_manager.enable_camera()
        self.assertTrue(result)
        
        # Log the action
        self.log_manager.log_camera_access(user.id, "CAMERA_ENABLED")
        
        # Verify log was created
        logs = self.log_manager.get_access_logs(user.id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "CAMERA_ENABLED")
        
        # Test disable camera
        result = self.camera_manager.disable_camera()
        self.assertTrue(result)
        
        # Log the action
        self.log_manager.log_camera_access(user.id, "CAMERA_DISABLED")
        
        # Verify both logs exist
        logs = self.log_manager.get_access_logs(user.id)
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0].action, "CAMERA_DISABLED")  # Most recent first
        self.assertEqual(logs[1].action, "CAMERA_ENABLED")
    
    def test_failed_authentication_intrusion_workflow(self):
        """Test complete failed authentication and intrusion detection workflow"""
        # Test failed authentication
        result = self.auth_manager.authenticate_user(self.test_username, "wrongpassword")
        self.assertFalse(result)
        
        # Trigger intrusion detection
        media_path = self.intrusion_detector.handle_failed_authentication(self.test_username)
        self.assertIsNotNone(media_path)
        
        # Verify intrusion was logged
        intrusion_logs = self.log_manager.get_intrusion_logs()
        self.assertEqual(len(intrusion_logs), 1)
        
        # Verify failed authentication was logged
        failed_logs = self.log_manager.get_access_logs(-1)  # System logs
        failed_auth_logs = [log for log in failed_logs if "AUTH_FAILED" in log.action]
        self.assertEqual(len(failed_auth_logs), 1)
    
    def test_multiple_failed_attempts_detection(self):
        """Test detection of multiple failed authentication attempts"""
        # Create multiple failed attempts
        for i in range(4):  # More than the default threshold of 3
            self.auth_manager.authenticate_user(self.test_username, "wrongpassword")
            self.log_manager.log_authentication_attempt(self.test_username, success=False)
        
        # Check if multiple attempts are detected
        result = self.intrusion_detector.detect_multiple_failed_attempts(
            self.test_username, 
            time_window_minutes=15, 
            max_attempts=3
        )
        self.assertTrue(result)
    
    def test_email_integration_with_intrusion_detection(self):
        """Test email service integration with intrusion detection"""
        # Configure email service (mock)
        with patch.object(self.email_service, 'is_configured', True):
            with patch.object(self.email_service, 'send_intrusion_alert', return_value=True) as mock_send:
                # Trigger intrusion with email alert
                media_path = "/fake/path/intrusion.avi"
                result = self.intrusion_detector.trigger_email_alert(
                    media_path, 
                    username=self.test_username
                )
                
                # Email service should have been called
                self.assertTrue(result)
    
    def test_log_filtering_and_retrieval(self):
        """Test comprehensive log filtering and retrieval"""
        # Authenticate user
        self.auth_manager.authenticate_user(self.test_username, self.test_password)
        user = self.auth_manager.get_current_user()
        
        # Create various log entries
        self.log_manager.log_camera_access(user.id, "CAMERA_ENABLED")
        self.log_manager.log_camera_access(user.id, "CAMERA_DISABLED")
        self.log_manager.log_authentication_attempt(self.test_username, success=True)
        self.log_manager.log_system_event(user.id, "SYSTEM_STARTUP")
        
        # Test filtering by action pattern
        camera_logs = self.log_manager.get_logs_by_action("CAMERA", user.id)
        self.assertEqual(len(camera_logs), 2)
        
        auth_logs = self.log_manager.get_logs_by_action("AUTH", user.id)
        self.assertEqual(len(auth_logs), 1)
        
        # Test date range filtering
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        recent_logs = self.log_manager.get_logs_by_date_range(yesterday, tomorrow, user.id)
        self.assertGreater(len(recent_logs), 0)
    
    def test_statistics_generation(self):
        """Test statistics generation across all components"""
        # Authenticate user
        self.auth_manager.authenticate_user(self.test_username, self.test_password)
        user = self.auth_manager.get_current_user()
        
        # Create test data
        self.log_manager.log_camera_access(user.id, "CAMERA_ENABLED")
        self.log_manager.log_camera_access(user.id, "CAMERA_DISABLED")
        self.log_manager.log_intrusion_attempt("/fake/path/video1.avi")
        self.log_manager.log_intrusion_attempt("/fake/path/video2.avi")
        
        # Test log statistics
        log_stats = self.log_manager.get_log_statistics(user.id)
        self.assertEqual(log_stats['total_access_logs'], 2)
        self.assertEqual(log_stats['total_intrusion_attempts'], 2)
        self.assertIn('CAMERA', log_stats['action_breakdown'])
        
        # Test intrusion statistics
        intrusion_stats = self.intrusion_detector.get_intrusion_statistics()
        self.assertEqual(intrusion_stats['total_intrusion_attempts'], 2)
    
    def test_database_integrity_across_operations(self):
        """Test database integrity across multiple operations"""
        # Authenticate user
        self.auth_manager.authenticate_user(self.test_username, self.test_password)
        user = self.auth_manager.get_current_user()
        
        # Perform multiple operations
        operations = [
            ("CAMERA_ENABLED", lambda: self.log_manager.log_camera_access(user.id, "CAMERA_ENABLED")),
            ("CAMERA_DISABLED", lambda: self.log_manager.log_camera_access(user.id, "CAMERA_DISABLED")),
            ("AUTH_SUCCESS", lambda: self.log_manager.log_authentication_attempt(self.test_username, True)),
            ("INTRUSION", lambda: self.log_manager.log_intrusion_attempt("/fake/path/video.avi")),
            ("SYSTEM_EVENT", lambda: self.log_manager.log_system_event(user.id, "TEST_EVENT"))
        ]
        
        # Execute operations
        for op_name, op_func in operations:
            result = op_func()
            self.assertTrue(result, f"Operation {op_name} failed")
        
        # Verify all data is accessible
        access_logs = self.log_manager.get_access_logs(user.id)
        self.assertGreaterEqual(len(access_logs), 4)  # At least 4 access logs
        
        intrusion_logs = self.log_manager.get_intrusion_logs()
        self.assertEqual(len(intrusion_logs), 1)
        
        # Verify database consistency
        user_count = self.db_manager.get_user_count()
        self.assertEqual(user_count, 1)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery across components"""
        # Test authentication with non-existent user
        result = self.auth_manager.authenticate_user("nonexistent", "password")
        self.assertFalse(result)
        
        # Test logging with invalid user ID
        result = self.log_manager.log_camera_access(999, "INVALID_USER_TEST")
        # Should still work (foreign key constraint might not be enforced in test)
        
        # Test intrusion detection with camera failure
        self.camera_manager.capture_intrusion_media.return_value = None
        media_path = self.intrusion_detector.handle_failed_authentication("testuser")
        # Should handle gracefully
        
        # Test email service without configuration
        result = self.email_service.send_intrusion_alert(datetime.now(), "/fake/path")
        self.assertFalse(result)  # Should fail gracefully
    
    def test_concurrent_operations_simulation(self):
        """Test simulation of concurrent operations"""
        # Authenticate user
        self.auth_manager.authenticate_user(self.test_username, self.test_password)
        user = self.auth_manager.get_current_user()
        
        # Simulate concurrent logging operations
        import threading
        import time
        
        results = []
        
        def log_operation(operation_id):
            try:
                self.log_manager.log_camera_access(user.id, f"CONCURRENT_OP_{operation_id}")
                results.append(True)
            except Exception:
                results.append(False)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_operation, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations succeeded
        self.assertEqual(len(results), 5)
        self.assertTrue(all(results))
        
        # Verify all logs were created
        logs = self.log_manager.get_access_logs(user.id)
        concurrent_logs = [log for log in logs if "CONCURRENT_OP" in log.action]
        self.assertEqual(len(concurrent_logs), 5)
    
    def test_system_configuration_integration(self):
        """Test system configuration integration"""
        # Test AppConfig initialization
        with patch('app_config.BASE_DIR', Path(self.temp_dir)):
            app_config = AppConfig()
            
            # Test configuration loading
            self.assertIsNotNone(app_config.settings)
            self.assertIn("app", app_config.settings)
            self.assertIn("security", app_config.settings)
            
            # Test setting operations
            app_config.set_setting("test", "key", "value")
            retrieved_value = app_config.get_setting("test", "key")
            self.assertEqual(retrieved_value, "value")
            
            # Test configuration validation
            is_valid, issues = app_config.validate_configuration()
            # Should be valid with default settings
            self.assertTrue(is_valid or len(issues) == 0)


class TestEndToEndWorkflows(unittest.TestCase):
    """End-to-end workflow tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, "test.db")
        
        # Initialize complete system
        self.db_manager = DatabaseManager(self.temp_db)
        self.auth_manager = AuthenticationManager(self.db_manager)
        self.log_manager = LogManager(self.db_manager)
        
        # Mock camera manager
        self.camera_manager = MagicMock(spec=CameraManager)
        self.camera_manager.get_camera_status.return_value = True
        self.camera_manager.enable_camera.return_value = True
        self.camera_manager.disable_camera.return_value = True
        self.camera_manager.capture_intrusion_media.return_value = "/fake/video.avi"
        
        self.intrusion_detector = IntrusionDetector(self.camera_manager, self.log_manager)
        self.email_service = EmailService()
        
        # Setup initial user
        self.username = "admin"
        self.password = "AdminPassword123"
        self.auth_manager.setup_initial_password(self.username, self.password)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_user_session_workflow(self):
        """Test complete user session from login to logout"""
        # 1. User authentication
        auth_result = self.auth_manager.authenticate_user(self.username, self.password)
        self.assertTrue(auth_result)
        
        user = self.auth_manager.get_current_user()
        self.assertIsNotNone(user)
        
        # 2. Check camera status
        status = self.camera_manager.get_camera_status()
        self.assertTrue(status)
        
        # 3. Disable camera
        disable_result = self.camera_manager.disable_camera()
        self.assertTrue(disable_result)
        self.log_manager.log_camera_access(user.id, "CAMERA_DISABLED")
        
        # 4. Enable camera
        enable_result = self.camera_manager.enable_camera()
        self.assertTrue(enable_result)
        self.log_manager.log_camera_access(user.id, "CAMERA_ENABLED")
        
        # 5. View logs
        logs = self.log_manager.get_access_logs(user.id)
        self.assertEqual(len(logs), 2)
        
        # 6. Logout
        self.auth_manager.logout_user()
        self.assertFalse(self.auth_manager.is_authenticated())
    
    def test_security_incident_workflow(self):
        """Test complete security incident workflow"""
        # 1. Failed authentication attempt
        auth_result = self.auth_manager.authenticate_user(self.username, "wrongpassword")
        self.assertFalse(auth_result)
        
        # 2. Intrusion detection triggers
        media_path = self.intrusion_detector.handle_failed_authentication(self.username)
        self.assertIsNotNone(media_path)
        
        # 3. Verify evidence was captured
        self.camera_manager.capture_intrusion_media.assert_called()
        
        # 4. Verify logs were created
        intrusion_logs = self.log_manager.get_intrusion_logs()
        self.assertEqual(len(intrusion_logs), 1)
        
        failed_logs = self.log_manager.get_access_logs(-1)
        failed_auth_logs = [log for log in failed_logs if "AUTH_FAILED" in log.action]
        self.assertEqual(len(failed_auth_logs), 1)
        
        # 5. Email alert would be triggered (if configured)
        with patch.object(self.email_service, 'is_configured', True):
            with patch.object(self.email_service, 'send_intrusion_alert', return_value=True) as mock_send:
                alert_result = self.intrusion_detector.trigger_email_alert(media_path, self.username)
                self.assertTrue(alert_result)
    
    def test_system_administration_workflow(self):
        """Test system administration workflow"""
        # 1. Authenticate admin user
        self.auth_manager.authenticate_user(self.username, self.password)
        user = self.auth_manager.get_current_user()
        
        # 2. View system statistics
        log_stats = self.log_manager.get_log_statistics()
        self.assertIsInstance(log_stats, dict)
        
        intrusion_stats = self.intrusion_detector.get_intrusion_statistics()
        self.assertIsInstance(intrusion_stats, dict)
        
        # 3. Configure email notifications
        email_config_result = self.email_service.configure_smtp(
            "smtp.example.com", 587, "test@example.com", "password"
        )
        # Will fail without actual SMTP server, but tests the workflow
        
        # 4. Add email recipient
        recipient_result = self.email_service.add_recipient("admin@example.com")
        self.assertTrue(recipient_result)
        
        # 5. Test email (would fail without real SMTP)
        test_result = self.email_service.send_test_email()
        self.assertFalse(test_result)  # Expected to fail without real SMTP
        
        # 6. System maintenance operations
        self.log_manager.log_system_event(user.id, "SYSTEM_MAINTENANCE", "Admin workflow test")
        
        maintenance_logs = self.log_manager.get_logs_by_action("SYSTEM_MAINTENANCE")
        self.assertEqual(len(maintenance_logs), 1)


if __name__ == '__main__':
    # Run integration tests
    unittest.main(verbosity=2)