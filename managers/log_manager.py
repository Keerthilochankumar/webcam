"""
Log manager for Camera Privacy Manager
Handles activity logging, log retrieval, and audit trail management
"""
import logging
from datetime import datetime
from typing import List, Optional

from database.database_manager import DatabaseManager
from models.data_models import LogEntry, User


class LogManager:
    """Manages activity logging and audit trail for camera operations"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize log manager with database connection"""
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)
    
    def log_camera_access(self, user_id: int, action: str, timestamp: datetime = None) -> bool:
        """
        Log camera access action
        
        Args:
            user_id: ID of the user performing the action
            action: Action being performed (e.g., 'CAMERA_ENABLED', 'CAMERA_DISABLED')
            timestamp: Optional timestamp, defaults to current time
            
        Returns:
            True if logging successful, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            log_id = self.db_manager.log_access(user_id, action)
            self.logger.info(f"Camera access logged: {action} by user {user_id} at {timestamp}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log camera access: {e}")
            return False
    
    def get_access_logs(self, user_id: int = None, limit: int = 100) -> List[LogEntry]:
        """
        Retrieve access logs
        
        Args:
            user_id: Optional user ID to filter logs, None for all users
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of LogEntry objects
        """
        try:
            logs = self.db_manager.get_access_logs(user_id, limit)
            self.logger.info(f"Retrieved {len(logs)} access logs")
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve access logs: {e}")
            return []
    
    def log_intrusion_attempt(self, media_path: str, timestamp: datetime = None, ip_address: str = None) -> bool:
        """
        Log intrusion attempt
        
        Args:
            media_path: Path to captured media file
            timestamp: Optional timestamp, defaults to current time
            ip_address: Optional IP address of the intrusion attempt
            
        Returns:
            True if logging successful, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            intrusion_id = self.db_manager.log_intrusion_attempt(media_path, ip_address)
            self.logger.warning(f"Intrusion attempt logged: {media_path} at {timestamp}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log intrusion attempt: {e}")
            return False
    
    def get_intrusion_logs(self, limit: int = 50) -> List:
        """
        Retrieve intrusion attempt logs
        
        Args:
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of IntrusionAttempt objects
        """
        try:
            attempts = self.db_manager.get_intrusion_attempts(limit)
            self.logger.info(f"Retrieved {len(attempts)} intrusion logs")
            return attempts
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve intrusion logs: {e}")
            return []
    
    def log_authentication_attempt(self, username: str, success: bool, timestamp: datetime = None) -> bool:
        """
        Log authentication attempt (for audit purposes)
        
        Args:
            username: Username attempting authentication
            success: Whether authentication was successful
            timestamp: Optional timestamp, defaults to current time
            
        Returns:
            True if logging successful, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Get user ID if authentication was successful
            user_id = None
            if success:
                user = self.db_manager.get_user_by_username(username)
                if user:
                    user_id = user.id
            
            # Log the authentication attempt
            action = f"AUTH_SUCCESS_{username}" if success else f"AUTH_FAILED_{username}"
            
            if user_id:
                log_id = self.db_manager.log_access(user_id, action)
            else:
                # For failed attempts, we still want to log but without user_id
                # We'll use a special user_id of -1 for failed attempts
                log_id = self.db_manager.log_access(-1, action)
            
            log_level = "info" if success else "warning"
            getattr(self.logger, log_level)(f"Authentication attempt logged: {action} at {timestamp}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log authentication attempt: {e}")
            return False
    
    def log_system_event(self, user_id: int, event: str, details: str = None, timestamp: datetime = None) -> bool:
        """
        Log general system events
        
        Args:
            user_id: ID of the user associated with the event
            event: Event type (e.g., 'SYSTEM_STARTUP', 'ADMIN_PRIVILEGE_GRANTED')
            details: Optional additional details about the event
            timestamp: Optional timestamp, defaults to current time
            
        Returns:
            True if logging successful, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            action = f"{event}_{details}" if details else event
            log_id = self.db_manager.log_access(user_id, action)
            self.logger.info(f"System event logged: {action} by user {user_id} at {timestamp}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log system event: {e}")
            return False
    
    def get_logs_by_date_range(self, start_date: datetime, end_date: datetime, user_id: int = None) -> List[LogEntry]:
        """
        Retrieve logs within a specific date range
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            user_id: Optional user ID to filter logs
            
        Returns:
            List of LogEntry objects within the date range
        """
        try:
            # Get all logs first (this could be optimized with a database query)
            all_logs = self.get_access_logs(user_id, limit=1000)
            
            # Filter by date range
            filtered_logs = [
                log for log in all_logs
                if start_date <= log.timestamp <= end_date
            ]
            
            self.logger.info(f"Retrieved {len(filtered_logs)} logs for date range {start_date} to {end_date}")
            return filtered_logs
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve logs by date range: {e}")
            return []
    
    def get_logs_by_action(self, action_pattern: str, user_id: int = None, limit: int = 100) -> List[LogEntry]:
        """
        Retrieve logs by action pattern
        
        Args:
            action_pattern: Pattern to match in action field (case-insensitive)
            user_id: Optional user ID to filter logs
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of LogEntry objects matching the action pattern
        """
        try:
            all_logs = self.get_access_logs(user_id, limit)
            
            # Filter by action pattern (case-insensitive)
            filtered_logs = [
                log for log in all_logs
                if action_pattern.lower() in log.action.lower()
            ]
            
            self.logger.info(f"Retrieved {len(filtered_logs)} logs matching action pattern: {action_pattern}")
            return filtered_logs
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve logs by action pattern: {e}")
            return []
    
    def format_log_entry(self, log_entry: LogEntry) -> str:
        """
        Format a log entry for display
        
        Args:
            log_entry: LogEntry object to format
            
        Returns:
            Formatted string representation of the log entry
        """
        try:
            timestamp_str = log_entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            return f"[{timestamp_str}] User {log_entry.user_id}: {log_entry.action}"
            
        except Exception as e:
            self.logger.error(f"Failed to format log entry: {e}")
            return f"[ERROR] Failed to format log entry {log_entry.id}"
    
    def format_logs_for_display(self, logs: List[LogEntry]) -> List[str]:
        """
        Format multiple log entries for display
        
        Args:
            logs: List of LogEntry objects to format
            
        Returns:
            List of formatted string representations
        """
        try:
            formatted_logs = []
            for log in logs:
                formatted_logs.append(self.format_log_entry(log))
            
            return formatted_logs
            
        except Exception as e:
            self.logger.error(f"Failed to format logs for display: {e}")
            return [f"[ERROR] Failed to format {len(logs)} log entries"]
    
    def get_log_statistics(self, user_id: int = None) -> dict:
        """
        Get statistics about logged activities
        
        Args:
            user_id: Optional user ID to filter statistics
            
        Returns:
            Dictionary containing log statistics
        """
        try:
            logs = self.get_access_logs(user_id, limit=1000)
            intrusion_logs = self.get_intrusion_logs(limit=1000)
            
            # Count different types of actions
            action_counts = {}
            for log in logs:
                action_type = log.action.split('_')[0]  # Get first part of action
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            statistics = {
                'total_access_logs': len(logs),
                'total_intrusion_attempts': len(intrusion_logs),
                'action_breakdown': action_counts,
                'latest_activity': logs[0].timestamp if logs else None,
                'user_filter': user_id
            }
            
            self.logger.info(f"Generated log statistics: {statistics}")
            return statistics
            
        except Exception as e:
            self.logger.error(f"Failed to generate log statistics: {e}")
            return {
                'total_access_logs': 0,
                'total_intrusion_attempts': 0,
                'action_breakdown': {},
                'latest_activity': None,
                'error': str(e)
            }