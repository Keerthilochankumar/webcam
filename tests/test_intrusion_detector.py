"""
Unit tests for IntrusionDetector
"""
import unittest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from managers.intrusion_detector import IntrusionDetector
from managers.camera_manager import CameraManager
from managers.log_manager import LogManager
from database.database_manager import DatabaseManager


class TestIntrusionDetector(unittest.TestCase):
    """Test cases for IntrusionDetector"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create temporary media directory
        self.temp_media_dir = tempfile.mkdtemp()
        
        # Create managers with mocks
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.log_manager = LogManager(self.db_manager)
        self.camera_manager = MagicMock(spec=CameraManager)
        
        # Create intrusion detector
        self.intrusion_detector = IntrusionDetector(
            camera_manager=self.camera_manager,
            log_manager=self.log_manager
        )
        
        # Create test user
        self.test_user_id = self.db_manager.create_user("testuser", "hashed_password")
    
    def tearDown(self):
        """Clean up test environment"""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
        
        # Clean up temporary media directory
        import shutil
        shutil.rmtree(self.temp_media_dir, ignore_errors=True)
    
    @patch('managers.intrusion_detector.MEDIA_DIR')
    def test_handle_failed_authentication_success(self, mock_media_dir):
        """Test successful handling of failed authentication"""
        mock_media_dir.mkdir = MagicMock()
        
        # Mock successful media capture
        test_media_path = "/path/to/intrusion_video.avi"
        self.camera_manager.capture_intrusion_media.return_value = test_media_path
        
        # Mock IP address detection
        with patch.object(self.intrusion_detector, '_get_local_ip_address', return_value="192.168.1.100"):
            result = self.intrusion_detector.handle_failed_authentication("testuser")
        
        self.assertEqual(result, test_media_path)
        self.camera_manager.capture_intrusion_media.assert_called_once()
        
        # Verify logs were created
        intrusion_logs = self.log_manager.get_intrusion_logs()
        self.assertEqual(len(intrusion_logs), 1)
        self.assertEqual(intrusion_logs[0].media_path, test_media_path)
    
    def test_handle_failed_authentication_capture_fails(self):
        """Test handling failed authentication when media capture fails"""
        # Mock failed media capture
        self.camera_manager.capture_intrusion_media.return_value = None
        
        result = self.intrusion_detector.handle_failed_authentication("testuser")
        
        self.assertIsNone(result)
        self.camera_manager.capture_intrusion_media.assert_called_once()
        
        # Should still log the failed authentication
        # Check for failed auth logs (they use user_id -1)
        failed_logs = self.log_manager.get_access_logs(-1)
        self.assertTrue(any("AUTH_FAILED_testuser" in log.action for log in failed_logs))
    
    def test_handle_failed_authentication_in_progress(self):
        """Test handling failed authentication when intrusion is already in progress"""
        # Set intrusion in progress
        self.intrusion_detector.intrusion_in_progress = True
        
        result = self.intrusion_detector.handle_failed_authentication("testuser")
        
        self.assertIsNone(result)
        self.camera_manager.capture_intrusion_media.assert_not_called()
    
    @patch('managers.intrusion_detector.MEDIA_DIR')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_capture_and_store_evidence_success(self, mock_stat, mock_exists, mock_media_dir):
        """Test successful evidence capture and storage"""
        mock_media_dir.mkdir = MagicMock()
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 1024  # Non-zero file size
        
        test_media_path = "/path/to/intrusion_video.avi"
        self.camera_manager.capture_intrusion_media.return_value = test_media_path
        
        result = self.intrusion_detector.capture_and_store_evidence()
        
        self.assertEqual(result, test_media_path)
        self.camera_manager.capture_intrusion_media.assert_called_once()
    
    @patch('managers.intrusion_detector.MEDIA_DIR')
    @patch('pathlib.Path.exists')
    def test_capture_and_store_evidence_video_fails_photo_succeeds(self, mock_exists, mock_media_dir):
        """Test evidence capture when video fails but photo succeeds"""
        mock_media_dir.mkdir = MagicMock()
        mock_exists.return_value = True
        
        test_photo_path = "/path/to/intrusion_photo.jpg"
        
        # Mock video capture failure, photo capture success
        self.camera_manager.capture_intrusion_media.side_effect = [None, test_photo_path]
        
        result = self.intrusion_detector.capture_and_store_evidence()
        
        self.assertEqual(result, test_photo_path)
        # Should be called twice: once for video (duration > 0), once for photo (duration = 0)
        self.assertEqual(self.camera_manager.capture_intrusion_media.call_count, 2)
    
    @patch('managers.intrusion_detector.MEDIA_DIR')
    def test_capture_and_store_evidence_both_fail(self, mock_media_dir):
        """Test evidence capture when both video and photo fail"""
        mock_media_dir.mkdir = MagicMock()
        
        # Mock both video and photo capture failure
        self.camera_manager.capture_intrusion_media.return_value = None
        
        result = self.intrusion_detector.capture_and_store_evidence()
        
        self.assertIsNone(result)
        self.assertEqual(self.camera_manager.capture_intrusion_media.call_count, 2)
    
    def test_trigger_email_alert(self):
        """Test triggering email alert"""
        media_path = "/path/to/intrusion_video.avi"
        username = "testuser"
        timestamp = datetime.now()
        
        result = self.intrusion_detector.trigger_email_alert(media_path, username, timestamp)
        
        # Currently returns True as placeholder (EmailService not implemented yet)
        self.assertTrue(result)
    
    def test_detect_multiple_failed_attempts_detected(self):
        """Test detection of multiple failed attempts"""
        username = "testuser"
        
        # Create multiple failed authentication logs within time window
        current_time = datetime.now()
        for i in range(4):  # More than max_attempts (3)
            timestamp = current_time - timedelta(minutes=i)
            self.log_manager.log_authentication_attempt(username, success=False, timestamp=timestamp)
        
        result = self.intrusion_detector.detect_multiple_failed_attempts(username, time_window_minutes=15, max_attempts=3)
        
        self.assertTrue(result)
    
    def test_detect_multiple_failed_attempts_not_detected(self):
        """Test when multiple failed attempts are not detected"""
        username = "testuser"
        
        # Create only 2 failed attempts (less than max_attempts)
        current_time = datetime.now()
        for i in range(2):
            timestamp = current_time - timedelta(minutes=i)
            self.log_manager.log_authentication_attempt(username, success=False, timestamp=timestamp)
        
        result = self.intrusion_detector.detect_multiple_failed_attempts(username, time_window_minutes=15, max_attempts=3)
        
        self.assertFalse(result)
    
    def test_detect_multiple_failed_attempts_outside_window(self):
        """Test when failed attempts are outside time window"""
        username = "testuser"
        
        # Create failed attempts outside the time window
        old_time = datetime.now() - timedelta(hours=1)  # 1 hour ago
        for i in range(4):
            timestamp = old_time - timedelta(minutes=i)
            self.log_manager.log_authentication_attempt(username, success=False, timestamp=timestamp)
        
        result = self.intrusion_detector.detect_multiple_failed_attempts(username, time_window_minutes=15, max_attempts=3)
        
        self.assertFalse(result)
    
    def test_handle_suspicious_activity(self):
        """Test handling suspicious activity"""
        activity_type = "UNAUTHORIZED_CAMERA_ACCESS"
        details = "Camera accessed without proper authentication"
        
        result = self.intrusion_detector.handle_suspicious_activity(activity_type, details)
        
        self.assertTrue(result)
        
        # Verify system event was logged
        logs = self.log_manager.get_access_logs(-1)  # System events use user_id -1
        suspicious_logs = [log for log in logs if "SUSPICIOUS_ACTIVITY" in log.action]
        self.assertEqual(len(suspicious_logs), 1)
    
    @patch('managers.intrusion_detector.MEDIA_DIR')
    def test_handle_suspicious_activity_with_evidence_capture(self, mock_media_dir):
        """Test handling suspicious activity that triggers evidence capture"""
        mock_media_dir.exists.return_value = True
        
        activity_type = "UNAUTHORIZED_CAMERA_ACCESS"
        test_media_path = "/path/to/evidence.avi"
        self.camera_manager.capture_intrusion_media.return_value = test_media_path
        
        with patch.object(self.intrusion_detector, 'capture_and_store_evidence', return_value=test_media_path):
            with patch.object(self.intrusion_detector, 'trigger_email_alert', return_value=True):
                result = self.intrusion_detector.handle_suspicious_activity(activity_type)
        
        self.assertTrue(result)
    
    @patch('managers.intrusion_detector.MEDIA_DIR')
    def test_cleanup_old_evidence(self, mock_media_dir):
        """Test cleanup of old evidence files"""
        # Mock media directory with files
        old_file = MagicMock()
        old_file.is_file.return_value = True
        old_file.stat.return_value.st_mtime = (datetime.now() - timedelta(days=35)).timestamp()
        old_file.unlink = MagicMock()
        
        recent_file = MagicMock()
        recent_file.is_file.return_value = True
        recent_file.stat.return_value.st_mtime = (datetime.now() - timedelta(days=5)).timestamp()
        
        mock_media_dir.exists.return_value = True
        mock_media_dir.iterdir.return_value = [old_file, recent_file]
        
        result = self.intrusion_detector.cleanup_old_evidence(days_to_keep=30)
        
        self.assertEqual(result, 1)  # Only old file should be deleted
        old_file.unlink.assert_called_once()
    
    @patch('managers.intrusion_detector.MEDIA_DIR')
    def test_cleanup_old_evidence_no_directory(self, mock_media_dir):
        """Test cleanup when media directory doesn't exist"""
        mock_media_dir.exists.return_value = False
        
        result = self.intrusion_detector.cleanup_old_evidence()
        
        self.assertEqual(result, 0)
    
    def test_get_intrusion_statistics(self):
        """Test getting intrusion statistics"""
        # Create some intrusion logs
        self.log_manager.log_intrusion_attempt("/path/to/video1.avi", ip_address="192.168.1.100")
        self.log_manager.log_intrusion_attempt("/path/to/video2.avi", ip_address="192.168.1.101")
        
        with patch('managers.intrusion_detector.MEDIA_DIR') as mock_media_dir:
            # Mock media directory with files
            file1 = MagicMock()
            file1.is_file.return_value = True
            file1.stat.return_value.st_size = 1024
            
            file2 = MagicMock()
            file2.is_file.return_value = True
            file2.stat.return_value.st_size = 2048
            
            mock_media_dir.exists.return_value = True
            mock_media_dir.iterdir.return_value = [file1, file2]
            
            stats = self.intrusion_detector.get_intrusion_statistics()
        
        self.assertEqual(stats['total_intrusion_attempts'], 2)
        self.assertEqual(stats['evidence_files_count'], 2)
        self.assertEqual(stats['total_evidence_size_bytes'], 3072)
        self.assertIsNotNone(stats['latest_intrusion'])
    
    @patch('socket.socket')
    def test_get_local_ip_address_success(self, mock_socket):
        """Test successful local IP address detection"""
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("192.168.1.100", 12345)
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        ip_address = self.intrusion_detector._get_local_ip_address()
        
        self.assertEqual(ip_address, "192.168.1.100")
    
    @patch('socket.socket')
    @patch('socket.gethostbyname')
    @patch('socket.gethostname')
    def test_get_local_ip_address_fallback(self, mock_hostname, mock_hostbyname, mock_socket):
        """Test IP address detection with fallback methods"""
        # Mock primary method failure
        mock_socket.side_effect = Exception("Network error")
        
        # Mock fallback success
        mock_hostname.return_value = "localhost"
        mock_hostbyname.return_value = "127.0.0.1"
        
        ip_address = self.intrusion_detector._get_local_ip_address()
        
        self.assertEqual(ip_address, "127.0.0.1")
    
    @patch('socket.socket')
    @patch('socket.gethostbyname')
    def test_get_local_ip_address_all_fail(self, mock_hostbyname, mock_socket):
        """Test IP address detection when all methods fail"""
        # Mock all methods failing
        mock_socket.side_effect = Exception("Network error")
        mock_hostbyname.side_effect = Exception("DNS error")
        
        ip_address = self.intrusion_detector._get_local_ip_address()
        
        self.assertEqual(ip_address, "127.0.0.1")  # Final fallback
    
    def test_is_intrusion_in_progress(self):
        """Test checking if intrusion is in progress"""
        # Initially not in progress
        self.assertFalse(self.intrusion_detector.is_intrusion_in_progress())
        
        # Set in progress
        self.intrusion_detector.intrusion_in_progress = True
        self.assertTrue(self.intrusion_detector.is_intrusion_in_progress())
        
        # Reset
        self.intrusion_detector.intrusion_in_progress = False
        self.assertFalse(self.intrusion_detector.is_intrusion_in_progress())


if __name__ == '__main__':
    unittest.main()