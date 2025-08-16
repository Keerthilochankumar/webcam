"""
Application configuration and initialization for Camera Privacy Manager
Handles startup sequence, dependency initialization, and configuration management
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
import json

from config import (
    APP_NAME, APP_VERSION, DATABASE_FILE, MEDIA_DIR, 
    REQUIRE_ADMIN, BASE_DIR
)


class AppConfig:
    """Application configuration and initialization manager"""
    
    def __init__(self):
        """Initialize application configuration"""
        self.logger = None
        self.config_file = BASE_DIR / "app_settings.json"
        self.log_file = BASE_DIR / "app.log"
        self.settings = {}
        
        # Initialize logging first
        self.setup_logging()
        
        # Load configuration
        self.load_configuration()
        
        # Initialize directories
        self.initialize_directories()
        
        self.logger.info(f"{APP_NAME} v{APP_VERSION} initializing...")
    
    def setup_logging(self):
        """Configure application logging"""
        try:
            # Create logs directory if it doesn't exist
            log_dir = BASE_DIR / "logs"
            log_dir.mkdir(exist_ok=True)
            
            # Configure logging
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            
            # File handler
            file_handler = logging.FileHandler(
                log_dir / f"camera_privacy_{datetime.now().strftime('%Y%m%d')}.log",
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter(log_format))
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(logging.Formatter(log_format))
            
            # Root logger configuration
            logging.basicConfig(
                level=logging.INFO,
                handlers=[file_handler, console_handler],
                format=log_format
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("Logging system initialized")
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")
            # Fallback to basic logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
    
    def load_configuration(self):
        """Load application configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                self.logger.info("Configuration loaded from file")
            else:
                # Create default configuration
                self.settings = self.get_default_settings()
                self.save_configuration()
                self.logger.info("Default configuration created")
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.settings = self.get_default_settings()
    
    def get_default_settings(self):
        """Get default application settings"""
        return {
            "app": {
                "name": APP_NAME,
                "version": APP_VERSION,
                "first_run": True,
                "last_startup": None,
                "startup_count": 0
            },
            "security": {
                "require_admin": REQUIRE_ADMIN,
                "max_failed_attempts": 3,
                "failed_attempt_window_minutes": 15,
                "auto_cleanup_days": 30,
                "password_min_length": 8
            },
            "email": {
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "use_tls": True,
                "recipients": []
            },
            "camera": {
                "intrusion_video_duration": 10,
                "default_device_id": 0,
                "capture_format": "avi"
            },
            "gui": {
                "window_width": 400,
                "window_height": 300,
                "popup_display_time": 3000,
                "remember_window_position": False
            },
            "logging": {
                "log_level": "INFO",
                "max_log_files": 30,
                "max_log_size_mb": 10
            }
        }
    
    def save_configuration(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            self.logger.info("Configuration saved to file")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def initialize_directories(self):
        """Initialize required directories"""
        try:
            directories = [
                MEDIA_DIR,
                BASE_DIR / "logs",
                BASE_DIR / "backups"
            ]
            
            for directory in directories:
                directory.mkdir(exist_ok=True)
                self.logger.debug(f"Directory initialized: {directory}")
            
            self.logger.info("All directories initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize directories: {e}")
            raise
    
    def check_system_requirements(self):
        """Check system requirements and dependencies"""
        requirements_met = True
        issues = []
        
        try:
            # Check Python version
            if sys.version_info < (3, 8):
                issues.append("Python 3.8 or higher is required")
                requirements_met = False
            
            # Check required modules
            required_modules = ['cv2', 'tkinter', 'sqlite3', 'smtplib']
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    issues.append(f"Required module not found: {module}")
                    requirements_met = False
            
            # Check file permissions
            try:
                test_file = BASE_DIR / "test_permissions.tmp"
                test_file.write_text("test")
                test_file.unlink()
            except Exception:
                issues.append("Insufficient file system permissions")
                requirements_met = False
            
            # Check database accessibility
            try:
                import sqlite3
                conn = sqlite3.connect(":memory:")
                conn.close()
            except Exception:
                issues.append("SQLite database not accessible")
                requirements_met = False
            
            if requirements_met:
                self.logger.info("All system requirements met")
            else:
                self.logger.error(f"System requirements not met: {', '.join(issues)}")
            
            return requirements_met, issues
            
        except Exception as e:
            self.logger.error(f"Error checking system requirements: {e}")
            return False, [f"Error checking requirements: {e}"]
    
    def initialize_database(self):
        """Initialize database and perform any necessary migrations"""
        try:
            from database.database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # Check if this is a fresh installation
            user_count = db_manager.get_user_count()
            if user_count == 0:
                self.settings["app"]["first_run"] = True
                self.logger.info("Fresh installation detected")
            else:
                self.settings["app"]["first_run"] = False
                self.logger.info(f"Existing installation with {user_count} users")
            
            self.logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            return False
    
    def update_startup_info(self):
        """Update startup information"""
        try:
            self.settings["app"]["last_startup"] = datetime.now().isoformat()
            self.settings["app"]["startup_count"] = self.settings["app"].get("startup_count", 0) + 1
            self.save_configuration()
            
            self.logger.info(f"Startup #{self.settings['app']['startup_count']}")
            
        except Exception as e:
            self.logger.error(f"Failed to update startup info: {e}")
    
    def cleanup_old_logs(self):
        """Cleanup old log files"""
        try:
            log_dir = BASE_DIR / "logs"
            if not log_dir.exists():
                return
            
            max_files = self.settings["logging"]["max_log_files"]
            log_files = sorted(log_dir.glob("camera_privacy_*.log"))
            
            if len(log_files) > max_files:
                files_to_delete = log_files[:-max_files]
                for file_path in files_to_delete:
                    file_path.unlink()
                    self.logger.debug(f"Deleted old log file: {file_path}")
                
                self.logger.info(f"Cleaned up {len(files_to_delete)} old log files")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
    
    def get_setting(self, section: str, key: str, default=None):
        """Get a configuration setting"""
        try:
            return self.settings.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def set_setting(self, section: str, key: str, value):
        """Set a configuration setting"""
        try:
            if section not in self.settings:
                self.settings[section] = {}
            self.settings[section][key] = value
            self.save_configuration()
            
        except Exception as e:
            self.logger.error(f"Failed to set setting {section}.{key}: {e}")
    
    def is_first_run(self):
        """Check if this is the first run of the application"""
        return self.settings["app"].get("first_run", True)
    
    def get_app_info(self):
        """Get application information"""
        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "startup_count": self.settings["app"].get("startup_count", 0),
            "last_startup": self.settings["app"].get("last_startup"),
            "first_run": self.is_first_run(),
            "config_file": str(self.config_file),
            "database_file": str(DATABASE_FILE),
            "media_directory": str(MEDIA_DIR)
        }
    
    def create_backup(self):
        """Create backup of important files"""
        try:
            backup_dir = BASE_DIR / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            
            import shutil
            
            # Backup database
            if DATABASE_FILE.exists():
                shutil.copy2(DATABASE_FILE, backup_dir / f"{backup_name}_database.db")
            
            # Backup configuration
            if self.config_file.exists():
                shutil.copy2(self.config_file, backup_dir / f"{backup_name}_config.json")
            
            self.logger.info(f"Backup created: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def validate_configuration(self):
        """Validate current configuration"""
        issues = []
        
        try:
            # Validate email settings if configured
            email_config = self.settings.get("email", {})
            if email_config.get("smtp_server"):
                if not email_config.get("username"):
                    issues.append("Email username is required when SMTP server is configured")
                if not email_config.get("password"):
                    issues.append("Email password is required when SMTP server is configured")
            
            # Validate security settings
            security_config = self.settings.get("security", {})
            max_attempts = security_config.get("max_failed_attempts", 3)
            if not isinstance(max_attempts, int) or max_attempts < 1:
                issues.append("Max failed attempts must be a positive integer")
            
            # Validate camera settings
            camera_config = self.settings.get("camera", {})
            video_duration = camera_config.get("intrusion_video_duration", 10)
            if not isinstance(video_duration, int) or video_duration < 0:
                issues.append("Intrusion video duration must be a non-negative integer")
            
            if issues:
                self.logger.warning(f"Configuration validation issues: {', '.join(issues)}")
            else:
                self.logger.info("Configuration validation passed")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            self.logger.error(f"Error validating configuration: {e}")
            return False, [f"Validation error: {e}"]


def initialize_application():
    """Initialize the application and return configuration"""
    try:
        # Create application configuration
        app_config = AppConfig()
        
        # Check system requirements
        requirements_met, issues = app_config.check_system_requirements()
        if not requirements_met:
            app_config.logger.critical(f"System requirements not met: {', '.join(issues)}")
            return None, issues
        
        # Initialize database
        if not app_config.initialize_database():
            app_config.logger.critical("Failed to initialize database")
            return None, ["Database initialization failed"]
        
        # Update startup information
        app_config.update_startup_info()
        
        # Cleanup old files
        app_config.cleanup_old_logs()
        
        # Validate configuration
        config_valid, config_issues = app_config.validate_configuration()
        if not config_valid:
            app_config.logger.warning(f"Configuration issues detected: {', '.join(config_issues)}")
        
        # Create backup on startup (optional)
        if app_config.get_setting("app", "create_startup_backup", False):
            app_config.create_backup()
        
        app_config.logger.info("Application initialization completed successfully")
        return app_config, []
        
    except Exception as e:
        if 'app_config' in locals() and app_config.logger:
            app_config.logger.critical(f"Application initialization failed: {e}")
        else:
            print(f"Critical error during initialization: {e}")
        return None, [f"Initialization error: {e}"]