"""
Intrusion detector for Camera Privacy Manager
Handles unauthorized access detection, evidence collection, and alert triggering
"""
import logging
import socket
from datetime import datetime
from typing import Optional
from pathlib import Path

from managers.camera_manager import CameraManager
from managers.log_manager import LogManager
from config import INTRUSION_VIDEO_DURATION, MEDIA_DIR


class IntrusionDetector:
    """Manages intrusion detection and evidence collection"""
    
    def __init__(self, camera_manager: CameraManager = None, log_manager: LogManager = None):
        """Initialize intrusion detector with required managers"""
        self.camera_manager = camera_manager or CameraManager()
        self.log_manager = log_manager or LogManager()
        self.logger = logging.getLogger(__name__)
        self.intrusion_in_progress = False
    
    def handle_failed_authentication(self, username: str, timestamp: datetime = None) -> Optional[str]:
        """
        Handle failed authentication attempt by capturing evidence
        
        Args:
            username: Username that failed authentication
            timestamp: Optional timestamp, defaults to current time
            
        Returns:
            Path to captured media file, None if capture failed
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            self.logger.warning(f"Handling failed authentication for user: {username}")
            
            # Prevent multiple simultaneous intrusion captures
            if self.intrusion_in_progress:
                self.logger.info("Intrusion capture already in progress, skipping")
                return None
            
            self.intrusion_in_progress = True
            
            try:
                # Capture evidence
                media_path = self.capture_and_store_evidence(timestamp)
                
                if media_path:
                    # Log the intrusion attempt
                    ip_address = self._get_local_ip_address()
                    self.log_manager.log_intrusion_attempt(media_path, timestamp, ip_address)
                    
                    # Log the authentication failure
                    self.log_manager.log_authentication_attempt(username, success=False, timestamp=timestamp)
                    
                    self.logger.warning(f"Intrusion evidence captured: {media_path}")
                    return media_path
                else:
                    self.logger.error("Failed to capture intrusion evidence")
                    # Still log the failed authentication attempt
                    self.log_manager.log_authentication_attempt(username, success=False, timestamp=timestamp)
                    return None
                    
            finally:
                self.intrusion_in_progress = False
                
        except Exception as e:
            self.logger.error(f"Error handling failed authentication: {e}")
            self.intrusion_in_progress = False
            return None
    
    def capture_and_store_evidence(self, timestamp: datetime = None) -> Optional[str]:
        """
        Capture and store evidence of intrusion attempt
        
        Args:
            timestamp: Optional timestamp for file naming
            
        Returns:
            Path to captured media file, None if capture failed
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            self.logger.info("Capturing intrusion evidence")
            
            # Ensure media directory exists
            MEDIA_DIR.mkdir(exist_ok=True)
            
            # Capture media using camera manager
            media_path = self.camera_manager.capture_intrusion_media(INTRUSION_VIDEO_DURATION)
            
            if media_path:
                # Verify the file was created and has content
                if Path(media_path).exists() and Path(media_path).stat().st_size > 0:
                    self.logger.info(f"Intrusion evidence stored: {media_path}")
                    return media_path
                else:
                    self.logger.error(f"Captured media file is empty or missing: {media_path}")
                    return None
            else:
                # Fallback: try to capture a photo instead of video
                self.logger.warning("Video capture failed, attempting photo capture")
                photo_path = self.camera_manager.capture_intrusion_media(0)  # 0 duration = photo
                
                if photo_path and Path(photo_path).exists():
                    self.logger.info(f"Intrusion photo captured as fallback: {photo_path}")
                    return photo_path
                else:
                    self.logger.error("Both video and photo capture failed")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to capture and store evidence: {e}")
            return None
    
    def trigger_email_alert(self, media_path: str, username: str = None, timestamp: datetime = None) -> bool:
        """
        Trigger email alert for intrusion attempt
        
        Args:
            media_path: Path to captured media file
            username: Optional username that triggered the intrusion
            timestamp: Optional timestamp of the intrusion
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            self.logger.info(f"Triggering email alert for intrusion: {media_path}")
            
            # Try to send email alert if EmailService is available
            try:
                from managers.email_service import EmailService
                email_service = EmailService()
                
                # Check if email service is configured
                if email_service.is_configured:
                    additional_details = f"Username involved: {username}" if username else None
                    return email_service.send_intrusion_alert(timestamp, media_path, additional_details)
                else:
                    self.logger.warning("Email service not configured, skipping email alert")
                    return False
                    
            except ImportError:
                self.logger.warning("EmailService not available, skipping email alert")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to trigger email alert: {e}")
            return False
    
    def detect_multiple_failed_attempts(self, username: str, time_window_minutes: int = 15, max_attempts: int = 3) -> bool:
        """
        Detect multiple failed authentication attempts within a time window
        
        Args:
            username: Username to check for failed attempts
            time_window_minutes: Time window in minutes to check
            max_attempts: Maximum allowed failed attempts
            
        Returns:
            True if multiple failed attempts detected, False otherwise
        """
        try:
            # Get recent authentication logs
            from datetime import timedelta
            current_time = datetime.now()
            start_time = current_time - timedelta(minutes=time_window_minutes)
            
            # Get logs by action pattern for failed authentication
            failed_auth_logs = self.log_manager.get_logs_by_action(f"AUTH_FAILED_{username}")
            
            # Filter logs within time window
            recent_failures = [
                log for log in failed_auth_logs
                if log.timestamp >= start_time
            ]
            
            if len(recent_failures) >= max_attempts:
                self.logger.warning(
                    f"Multiple failed attempts detected for {username}: "
                    f"{len(recent_failures)} attempts in {time_window_minutes} minutes"
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting multiple failed attempts: {e}")
            return False
    
    def handle_suspicious_activity(self, activity_type: str, details: str = None, timestamp: datetime = None) -> bool:
        """
        Handle general suspicious activity detection
        
        Args:
            activity_type: Type of suspicious activity
            details: Optional additional details
            timestamp: Optional timestamp
            
        Returns:
            True if handled successfully, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            self.logger.warning(f"Suspicious activity detected: {activity_type}")
            
            # Log the suspicious activity
            self.log_manager.log_system_event(
                user_id=-1,  # System event
                event=f"SUSPICIOUS_ACTIVITY_{activity_type}",
                details=details,
                timestamp=timestamp
            )
            
            # Depending on activity type, we might want to capture evidence
            if activity_type in ["UNAUTHORIZED_CAMERA_ACCESS", "SYSTEM_TAMPERING"]:
                media_path = self.capture_and_store_evidence(timestamp)
                if media_path:
                    self.trigger_email_alert(media_path, timestamp=timestamp)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling suspicious activity: {e}")
            return False
    
    def cleanup_old_evidence(self, days_to_keep: int = 30) -> int:
        """
        Clean up old intrusion evidence files
        
        Args:
            days_to_keep: Number of days to keep evidence files
            
        Returns:
            Number of files cleaned up
        """
        try:
            from datetime import timedelta
            import os
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cleanup_count = 0
            
            if not MEDIA_DIR.exists():
                return 0
            
            for file_path in MEDIA_DIR.iterdir():
                if file_path.is_file():
                    # Get file modification time
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        try:
                            file_path.unlink()  # Delete the file
                            cleanup_count += 1
                            self.logger.info(f"Cleaned up old evidence file: {file_path}")
                        except OSError as e:
                            self.logger.error(f"Failed to delete file {file_path}: {e}")
            
            if cleanup_count > 0:
                self.logger.info(f"Cleaned up {cleanup_count} old evidence files")
            
            return cleanup_count
            
        except Exception as e:
            self.logger.error(f"Error during evidence cleanup: {e}")
            return 0
    
    def get_intrusion_statistics(self) -> dict:
        """
        Get statistics about intrusion attempts
        
        Returns:
            Dictionary containing intrusion statistics
        """
        try:
            intrusion_logs = self.log_manager.get_intrusion_logs()
            
            # Count intrusions by date
            intrusion_dates = {}
            for intrusion in intrusion_logs:
                date_key = intrusion.timestamp.strftime("%Y-%m-%d")
                intrusion_dates[date_key] = intrusion_dates.get(date_key, 0) + 1
            
            # Count evidence files
            evidence_files = 0
            total_evidence_size = 0
            if MEDIA_DIR.exists():
                for file_path in MEDIA_DIR.iterdir():
                    if file_path.is_file():
                        evidence_files += 1
                        total_evidence_size += file_path.stat().st_size
            
            statistics = {
                'total_intrusion_attempts': len(intrusion_logs),
                'intrusions_by_date': intrusion_dates,
                'evidence_files_count': evidence_files,
                'total_evidence_size_bytes': total_evidence_size,
                'latest_intrusion': intrusion_logs[0].timestamp if intrusion_logs else None,
                'media_directory': str(MEDIA_DIR)
            }
            
            self.logger.info(f"Generated intrusion statistics: {statistics}")
            return statistics
            
        except Exception as e:
            self.logger.error(f"Failed to generate intrusion statistics: {e}")
            return {
                'total_intrusion_attempts': 0,
                'intrusions_by_date': {},
                'evidence_files_count': 0,
                'total_evidence_size_bytes': 0,
                'latest_intrusion': None,
                'error': str(e)
            }
    
    def _get_local_ip_address(self) -> Optional[str]:
        """
        Get local IP address for logging purposes
        
        Returns:
            Local IP address as string, None if unable to determine
        """
        try:
            # Create a socket connection to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Connect to a remote address (doesn't actually send data)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except Exception:
            # Fallback methods
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"  # Localhost fallback
    
    def is_intrusion_in_progress(self) -> bool:
        """
        Check if an intrusion capture is currently in progress
        
        Returns:
            True if intrusion capture is in progress, False otherwise
        """
        return self.intrusion_in_progress