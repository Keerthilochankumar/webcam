"""
Unit tests for CameraManager
"""
import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from managers.camera_manager import CameraManager


class TestCameraManager(unittest.TestCase):
    """Test cases for CameraManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.camera_manager = CameraManager()
    
    def test_init(self):
        """Test CameraManager initialization"""
        self.assertTrue(self.camera_manager.camera_enabled)
        self.assertEqual(self.camera_manager._camera_device_id, 0)
    
    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    def test_check_admin_privileges(self, mock_is_admin):
        """Test checking administrator privileges"""
        # Test when running as admin
        mock_is_admin.return_value = True
        self.assertTrue(self.camera_manager.check_admin_privileges())
        
        # Test when not running as admin
        mock_is_admin.return_value = False
        self.assertFalse(self.camera_manager.check_admin_privileges())
        
        # Test when exception occurs
        mock_is_admin.side_effect = Exception("Access denied")
        self.assertFalse(self.camera_manager.check_admin_privileges())
    
    @patch('cv2.VideoCapture')
    def test_get_camera_status_available(self, mock_video_capture):
        """Test getting camera status when camera is available"""
        # Mock camera being available and working
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, "mock_frame")
        mock_video_capture.return_value = mock_cap
        
        status = self.camera_manager.get_camera_status()
        self.assertTrue(status)
        mock_cap.release.assert_called_once()
    
    @patch('cv2.VideoCapture')
    def test_get_camera_status_unavailable(self, mock_video_capture):
        """Test getting camera status when camera is unavailable"""
        # Mock camera not being available
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        status = self.camera_manager.get_camera_status()
        self.assertFalse(status)
    
    @patch('cv2.VideoCapture')
    def test_get_camera_status_disabled(self, mock_video_capture):
        """Test getting camera status when internally disabled"""
        # Mock camera being available but internally disabled
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, "mock_frame")
        mock_video_capture.return_value = mock_cap
        
        # Disable camera internally
        self.camera_manager.camera_enabled = False
        
        status = self.camera_manager.get_camera_status()
        self.assertFalse(status)
    
    @patch.object(CameraManager, 'unblock_camera_system_wide')
    @patch.object(CameraManager, 'get_camera_status')
    def test_enable_camera_success(self, mock_get_status, mock_unblock):
        """Test successful camera enabling"""
        mock_unblock.return_value = True
        mock_get_status.return_value = True
        
        result = self.camera_manager.enable_camera()
        self.assertTrue(result)
        self.assertTrue(self.camera_manager.camera_enabled)
        mock_unblock.assert_called_once()
    
    @patch.object(CameraManager, 'unblock_camera_system_wide')
    def test_enable_camera_unblock_fails(self, mock_unblock):
        """Test camera enabling when system unblock fails"""
        mock_unblock.return_value = False
        
        result = self.camera_manager.enable_camera()
        self.assertFalse(result)
    
    @patch.object(CameraManager, 'block_camera_system_wide')
    def test_disable_camera_success(self, mock_block):
        """Test successful camera disabling"""
        mock_block.return_value = True
        
        result = self.camera_manager.disable_camera()
        self.assertTrue(result)
        self.assertFalse(self.camera_manager.camera_enabled)
        mock_block.assert_called_once()
    
    @patch.object(CameraManager, 'block_camera_system_wide')
    def test_disable_camera_block_fails(self, mock_block):
        """Test camera disabling when system block fails"""
        mock_block.return_value = False
        
        result = self.camera_manager.disable_camera()
        self.assertFalse(result)
        self.assertFalse(self.camera_manager.camera_enabled)  # Internal state still changes
    
    @patch.object(CameraManager, 'check_admin_privileges')
    @patch('winreg.OpenKey')
    @patch('winreg.SetValueEx')
    @patch('winreg.CloseKey')
    def test_block_camera_system_wide_registry(self, mock_close, mock_set_value, mock_open_key, mock_admin):
        """Test system-wide camera blocking via registry"""
        mock_admin.return_value = True
        mock_key = MagicMock()
        mock_open_key.return_value = mock_key
        
        result = self.camera_manager.block_camera_system_wide()
        self.assertTrue(result)
        mock_set_value.assert_called_once()
        mock_close.assert_called_once_with(mock_key)
    
    @patch.object(CameraManager, 'check_admin_privileges')
    def test_block_camera_system_wide_no_admin(self, mock_admin):
        """Test system-wide camera blocking without admin privileges"""
        mock_admin.return_value = False
        
        result = self.camera_manager.block_camera_system_wide()
        self.assertFalse(result)
    
    @patch.object(CameraManager, 'check_admin_privileges')
    @patch('winreg.OpenKey')
    @patch('winreg.SetValueEx')
    @patch('winreg.CloseKey')
    def test_unblock_camera_system_wide_registry(self, mock_close, mock_set_value, mock_open_key, mock_admin):
        """Test system-wide camera unblocking via registry"""
        mock_admin.return_value = True
        mock_key = MagicMock()
        mock_open_key.return_value = mock_key
        
        result = self.camera_manager.unblock_camera_system_wide()
        self.assertTrue(result)
        mock_set_value.assert_called_once()
        mock_close.assert_called_once_with(mock_key)
    
    @patch('subprocess.run')
    @patch.object(CameraManager, 'check_admin_privileges')
    @patch('winreg.OpenKey')
    def test_disable_camera_via_devcon(self, mock_open_key, mock_admin, mock_subprocess):
        """Test camera disabling via PowerShell when registry method fails"""
        mock_admin.return_value = True
        mock_open_key.side_effect = FileNotFoundError()
        
        # Mock successful PowerShell execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = self.camera_manager.block_camera_system_wide()
        self.assertTrue(result)
        mock_subprocess.assert_called_once()
    
    @patch('cv2.VideoCapture')
    @patch.object(CameraManager, '_capture_video')
    def test_capture_intrusion_media_video(self, mock_capture_video, mock_video_capture):
        """Test intrusion media capture (video)"""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_video_capture.return_value = mock_cap
        mock_capture_video.return_value = "/path/to/video.avi"
        
        result = self.camera_manager.capture_intrusion_media(10)
        self.assertEqual(result, "/path/to/video.avi")
        mock_capture_video.assert_called_once()
    
    @patch('cv2.VideoCapture')
    @patch.object(CameraManager, '_capture_photo')
    def test_capture_intrusion_media_photo(self, mock_capture_photo, mock_video_capture):
        """Test intrusion media capture (photo)"""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_video_capture.return_value = mock_cap
        mock_capture_photo.return_value = "/path/to/photo.jpg"
        
        result = self.camera_manager.capture_intrusion_media(0)
        self.assertEqual(result, "/path/to/photo.jpg")
        mock_capture_photo.assert_called_once()
    
    @patch('cv2.VideoCapture')
    def test_capture_intrusion_media_camera_unavailable(self, mock_video_capture):
        """Test intrusion media capture when camera is unavailable"""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        # Mock get_camera_status to return False
        with patch.object(self.camera_manager, 'get_camera_status', return_value=False):
            result = self.camera_manager.capture_intrusion_media(10)
            self.assertIsNone(result)
    
    @patch('cv2.VideoWriter')
    @patch('cv2.VideoWriter_fourcc')
    def test_capture_video(self, mock_fourcc, mock_video_writer):
        """Test video capture functionality"""
        # Mock camera capture
        mock_cap = MagicMock()
        mock_cap.get.side_effect = [30, 640, 480]  # fps, width, height
        mock_cap.read.return_value = (True, "mock_frame")
        
        # Mock video writer
        mock_writer = MagicMock()
        mock_video_writer.return_value = mock_writer
        mock_fourcc.return_value = "mock_fourcc"
        
        result = self.camera_manager._capture_video(mock_cap, "/path/to/video.avi", 1)
        self.assertEqual(result, "/path/to/video.avi")
        mock_writer.write.assert_called()
        mock_writer.release.assert_called_once()
    
    @patch('cv2.imwrite')
    def test_capture_photo(self, mock_imwrite):
        """Test photo capture functionality"""
        mock_cap = MagicMock()
        mock_cap.read.return_value = (True, "mock_frame")
        mock_imwrite.return_value = True
        
        result = self.camera_manager._capture_photo(mock_cap, "/path/to/photo.jpg")
        self.assertEqual(result, "/path/to/photo.jpg")
        mock_imwrite.assert_called_once_with("/path/to/photo.jpg", "mock_frame")
        mock_cap.release.assert_called_once()


if __name__ == '__main__':
    unittest.main()