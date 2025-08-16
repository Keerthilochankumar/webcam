"""
Camera manager for Camera Privacy Manager
Handles camera operations, system-wide blocking, and administrative privileges
"""
import cv2
import ctypes
import sys
import logging
import winreg
import subprocess
from datetime import datetime
from typing import Optional
from pathlib import Path

from config import INTRUSION_VIDEO_DURATION, MEDIA_DIR


class CameraManager:
    """Manages camera operations and system-wide access control"""
    
    def __init__(self):
        """Initialize camera manager"""
        self.logger = logging.getLogger(__name__)
        self.camera_enabled = True  # Track internal camera state
        self._camera_device_id = 0  # Default camera device ID
    
    def check_admin_privileges(self) -> bool:
        """
        Check if the application is running with administrator privileges
        Returns True if running as admin, False otherwise
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            self.logger.error(f"Failed to check admin privileges: {e}")
            return False
    
    def request_admin_privileges(self) -> bool:
        """
        Request administrator privileges by restarting the application
        Returns True if successful, False otherwise
        """
        try:
            if self.check_admin_privileges():
                return True
            
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                " ".join(sys.argv), 
                None, 
                1
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to request admin privileges: {e}")
            return False
    
    def get_camera_status(self) -> bool:
        """
        Get current camera status
        Returns True if camera is available/enabled, False if blocked/disabled
        """
        try:
            # Check internal state first
            if not self.camera_enabled:
                return False
            
            # Try to access camera to check if it's actually available
            cap = cv2.VideoCapture(self._camera_device_id)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret:
                    self.logger.info("Camera is accessible and working")
                    return True
                else:
                    self.logger.warning("Camera opened but failed to read frame")
                    return False
            else:
                self.logger.info("Camera is not accessible (blocked)")
                return False
        except Exception as e:
            self.logger.error(f"Failed to check camera status: {e}")
            return False
    
    def verify_camera_blocked(self) -> bool:
        """
        Verify that camera is blocked using SAFE methods
        Returns True if camera appears to be blocked, False if accessible
        """
        try:
            # Check if lock file exists
            lock_file = MEDIA_DIR / "camera_blocked.lock"
            if not lock_file.exists():
                self.logger.warning("Camera lock file not found")
                return False
            
            # Check privacy registry settings
            try:
                registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, "Value")
                winreg.CloseKey(key)
                
                if value != "Deny":
                    self.logger.warning("Privacy registry not set to Deny")
                    return False
            except:
                self.logger.warning("Could not verify privacy registry")
            
            # Try a quick camera access test (but don't rely on it completely)
            camera_accessible = False
            try:
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        camera_accessible = True
                    cap.release()
            except:
                pass  # Camera access failed, which is good for blocking
            
            if camera_accessible:
                self.logger.warning("Camera is still accessible via OpenCV")
                return False
            
            self.logger.info("Camera appears to be properly blocked")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to verify camera blocking: {e}")
            return False
    
    def get_blocking_status(self) -> dict:
        """Get detailed status of camera blocking methods (optimized)"""
        # Use cached status if recent (within 5 seconds)
        if hasattr(self, '_cached_status') and hasattr(self, '_cache_time'):
            from datetime import datetime, timedelta
            if datetime.now() - self._cache_time < timedelta(seconds=5):
                return self._cached_status
        
        status = {
            "privacy_registry": False,
            "group_policy": False,
            "lock_file": False,
            "camera_accessible": False
        }
        
        try:
            # Check privacy registry (fast)
            try:
                registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, "Value")
                winreg.CloseKey(key)
                status["privacy_registry"] = (value == "Deny")
            except:
                pass
            
            # Check group policy (fast)
            try:
                registry_path = r"SOFTWARE\Policies\Microsoft\Camera"
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, "AllowCamera")
                winreg.CloseKey(key)
                status["group_policy"] = (value == 0)
            except:
                pass
            
            # Check lock file (very fast)
            lock_file = MEDIA_DIR / "camera_blocked.lock"
            status["lock_file"] = lock_file.exists()
            
            # Check camera accessibility (slower - do this last and with timeout)
            try:
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Lower resolution for faster check
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                
                if cap.isOpened():
                    # Quick frame read with timeout
                    ret, frame = cap.read()
                    status["camera_accessible"] = (ret and frame is not None)
                cap.release()
            except:
                pass
            
            # Cache the result
            self._cached_status = status
            self._cache_time = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Failed to get blocking status: {e}")
        
        return status
    
    def clear_status_cache(self):
        """Clear cached status to force refresh"""
        if hasattr(self, '_cached_status'):
            delattr(self, '_cached_status')
        if hasattr(self, '_cache_time'):
            delattr(self, '_cache_time')
    
    def enable_camera(self) -> bool:
        """
        Enable camera access (optimized)
        Returns True if successful, False otherwise
        """
        try:
            # Clear cache before operation
            self.clear_status_cache()
            
            # Set internal state first
            self.camera_enabled = True
            
            # Unblock camera at system level
            if not self.unblock_camera_system_wide():
                self.logger.error("Failed to unblock camera at system level")
                self.camera_enabled = False
                return False
            
            # Quick verification (don't do full camera test here for performance)
            self.logger.info("Camera enabled successfully")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to enable camera: {e}")
            self.camera_enabled = False
            return False
    
    def disable_camera(self) -> bool:
        """
        Disable camera access (optimized)
        Returns True if successful, False otherwise
        """
        try:
            # Clear cache before operation
            self.clear_status_cache()
            
            # Set internal state first
            self.camera_enabled = False
            
            # Block camera at system level
            if not self.block_camera_system_wide():
                self.logger.error("Failed to block camera at system level")
                return False
            
            self.logger.info("Camera disabled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable camera: {e}")
            return False
    
    def block_camera_system_wide(self) -> bool:
        """
        Block camera access at Windows system level using SAFE methods
        Avoids breaking system drivers
        Returns True if successful, False otherwise
        """
        try:
            if not self.check_admin_privileges():
                self.logger.error("Administrator privileges required for system-wide camera blocking")
                return False
            
            success_count = 0
            total_methods = 0
            
            # Method 1: Block via Windows Privacy Settings (SAFE)
            total_methods += 1
            if self._block_camera_privacy_registry():
                success_count += 1
                self.logger.info("Camera blocked via privacy registry")
            
            # Method 2: Block via Group Policy (SAFE)
            total_methods += 1
            if self._block_camera_group_policy():
                success_count += 1
                self.logger.info("Camera blocked via Group Policy")
            
            # Method 3: Block via Application-level registry (SAFE)
            total_methods += 1
            if self._block_camera_app_registry():
                success_count += 1
                self.logger.info("Camera blocked via application registry")
            
            # Method 4: Create camera lock file (SAFE)
            total_methods += 1
            if self._create_camera_lock_file():
                success_count += 1
                self.logger.info("Camera blocked via lock file")
            
            # Consider successful if at least 2 methods worked
            if success_count >= 2:
                self.logger.info(f"Camera blocked safely ({success_count}/{total_methods} methods)")
                return True
            else:
                self.logger.error(f"Camera blocking failed ({success_count}/{total_methods} methods)")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to block camera system-wide: {e}")
            return False
    
    def unblock_camera_system_wide(self) -> bool:
        """
        Unblock camera access at Windows system level using SAFE methods
        Reverses all blocking methods without breaking drivers
        Returns True if successful, False otherwise
        """
        try:
            if not self.check_admin_privileges():
                self.logger.error("Administrator privileges required for system-wide camera unblocking")
                return False
            
            success_count = 0
            total_methods = 0
            
            # Method 1: Unblock via Windows Privacy Settings (SAFE)
            total_methods += 1
            if self._unblock_camera_privacy_registry():
                success_count += 1
                self.logger.info("Camera enabled via privacy registry")
            
            # Method 2: Unblock via Group Policy (SAFE)
            total_methods += 1
            if self._unblock_camera_group_policy():
                success_count += 1
                self.logger.info("Camera enabled via Group Policy")
            
            # Method 3: Unblock via Application-level registry (SAFE)
            total_methods += 1
            if self._unblock_camera_app_registry():
                success_count += 1
                self.logger.info("Camera enabled via application registry")
            
            # Method 4: Remove camera lock file (SAFE)
            total_methods += 1
            if self._remove_camera_lock_file():
                success_count += 1
                self.logger.info("Camera enabled via lock file removal")
            
            # Consider successful if at least 2 methods worked
            if success_count >= 2:
                self.logger.info(f"Camera enabled safely ({success_count}/{total_methods} methods)")
                return True
            else:
                self.logger.error(f"Camera enabling failed ({success_count}/{total_methods} methods)")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to unblock camera system-wide: {e}")
            return False
    
    def _block_camera_privacy_registry(self) -> bool:
        """Block camera via Windows privacy settings registry (SAFE)"""
        try:
            # Block for all users
            registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Deny")
            winreg.CloseKey(key)
            
            # Also block for current user
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Deny")
                winreg.CloseKey(key)
            except:
                pass  # Current user registry might not exist
            
            return True
        except Exception as e:
            self.logger.error(f"Privacy registry block failed: {e}")
            return False
    
    def _unblock_camera_privacy_registry(self) -> bool:
        """Unblock camera via Windows privacy settings registry (SAFE)"""
        try:
            # Unblock for all users
            registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Allow")
            winreg.CloseKey(key)
            
            # Also unblock for current user
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Allow")
                winreg.CloseKey(key)
            except:
                pass  # Current user registry might not exist
            
            return True
        except Exception as e:
            self.logger.error(f"Privacy registry unblock failed: {e}")
            return False
    
    def _block_camera_app_registry(self) -> bool:
        """Block camera access for specific applications (SAFE)"""
        try:
            # Block camera access for common applications
            apps_to_block = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\Microsoft.WindowsCamera_8wekyb3d8bbwe",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\NonPackaged"
            ]
            
            for app_path in apps_to_block:
                try:
                    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, app_path)
                    winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Deny")
                    winreg.CloseKey(key)
                except:
                    continue
            
            return True
        except Exception as e:
            self.logger.error(f"App registry block failed: {e}")
            return False
    
    def _unblock_camera_app_registry(self) -> bool:
        """Unblock camera access for specific applications (SAFE)"""
        try:
            # Unblock camera access for common applications
            apps_to_unblock = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\Microsoft.WindowsCamera_8wekyb3d8bbwe",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\NonPackaged"
            ]
            
            for app_path in apps_to_unblock:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, app_path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Allow")
                    winreg.CloseKey(key)
                except:
                    continue
            
            return True
        except Exception as e:
            self.logger.error(f"App registry unblock failed: {e}")
            return False
    
    def _create_camera_lock_file(self) -> bool:
        """Create a lock file to indicate camera is blocked (SAFE)"""
        try:
            lock_file = MEDIA_DIR / "camera_blocked.lock"
            with open(lock_file, 'w') as f:
                f.write(f"Camera blocked at {datetime.now().isoformat()}\n")
                f.write("This file indicates the camera is intentionally blocked.\n")
            return True
        except Exception as e:
            self.logger.error(f"Lock file creation failed: {e}")
            return False
    
    def _remove_camera_lock_file(self) -> bool:
        """Remove camera lock file (SAFE)"""
        try:
            lock_file = MEDIA_DIR / "camera_blocked.lock"
            if lock_file.exists():
                lock_file.unlink()
            return True
        except Exception as e:
            self.logger.error(f"Lock file removal failed: {e}")
            return False
    
    def _block_camera_group_policy(self) -> bool:
        """Block camera access via Group Policy registry"""
        try:
            registry_path = r"SOFTWARE\Policies\Microsoft\Camera"
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, registry_path)
                winreg.SetValueEx(key, "AllowCamera", 0, winreg.REG_DWORD, 0)  # Block camera
                winreg.CloseKey(key)
                return True
            except Exception:
                return False
        except Exception as e:
            self.logger.error(f"Group policy camera block failed: {e}")
            return False
    
    def _unblock_camera_group_policy(self) -> bool:
        """Unblock camera access via Group Policy registry"""
        try:
            registry_path = r"SOFTWARE\Policies\Microsoft\Camera"
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "AllowCamera", 0, winreg.REG_DWORD, 1)  # Allow camera
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                # Key doesn't exist, camera is allowed by default
                return True
            except Exception:
                return False
        except Exception as e:
            self.logger.error(f"Group policy camera unblock failed: {e}")
            return False
    
    def capture_intrusion_media(self, duration: int = None) -> Optional[str]:
        """
        Capture video or photo for intrusion detection
        Returns path to captured media file, None if failed
        """
        try:
            duration = duration or INTRUSION_VIDEO_DURATION
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Temporarily enable camera for capture if needed
            temp_enable = False
            if not self.get_camera_status():
                # For intrusion capture, we need to temporarily access camera
                cap = cv2.VideoCapture(self._camera_device_id)
                if not cap.isOpened():
                    self.logger.error("Cannot access camera for intrusion capture")
                    return None
            else:
                cap = cv2.VideoCapture(self._camera_device_id)
            
            # Determine if we should capture video or photo
            if duration > 0:
                # Capture video
                media_path = MEDIA_DIR / f"intrusion_video_{timestamp}.avi"
                return self._capture_video(cap, str(media_path), duration)
            else:
                # Capture photo
                media_path = MEDIA_DIR / f"intrusion_photo_{timestamp}.jpg"
                return self._capture_photo(cap, str(media_path))
                
        except Exception as e:
            self.logger.error(f"Failed to capture intrusion media: {e}")
            return None
    
    def _capture_video(self, cap: cv2.VideoCapture, output_path: str, duration: int) -> Optional[str]:
        """Capture video for specified duration"""
        try:
            # Get camera properties
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
            
            # Define codec and create VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frames_to_capture = fps * duration
            frames_captured = 0
            
            while frames_captured < frames_to_capture:
                ret, frame = cap.read()
                if ret:
                    out.write(frame)
                    frames_captured += 1
                else:
                    break
            
            # Release everything
            out.release()
            cap.release()
            
            if frames_captured > 0:
                self.logger.info(f"Intrusion video captured: {output_path}")
                return output_path
            else:
                self.logger.error("No frames captured for intrusion video")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to capture intrusion video: {e}")
            if 'out' in locals():
                out.release()
            if 'cap' in locals():
                cap.release()
            return None
    
    def _capture_photo(self, cap: cv2.VideoCapture, output_path: str) -> Optional[str]:
        """Capture single photo"""
        try:
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                cv2.imwrite(output_path, frame)
                self.logger.info(f"Intrusion photo captured: {output_path}")
                return output_path
            else:
                self.logger.error("Failed to capture intrusion photo")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to capture intrusion photo: {e}")
            if 'cap' in locals():
                cap.release()
            return None