"""
Configuration settings for Camera Privacy Manager
"""
import os
from pathlib import Path

# Application settings
APP_NAME = "Camera Privacy Manager"
APP_VERSION = "1.0.0"

# Database settings
DATABASE_PATH = "camera_privacy.db"

# Security settings
PASSWORD_SALT_LENGTH = 32
HASH_ALGORITHM = "sha256"

# Camera settings
INTRUSION_VIDEO_DURATION = 10  # seconds
INTRUSION_MEDIA_DIR = "intrusion_media"

# Email settings
DEFAULT_SMTP_PORT = 2525
EMAIL_TIMEOUT = 30  # seconds

# GUI settings
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 300
POPUP_DISPLAY_TIME = 3000  # milliseconds

# File paths
BASE_DIR = Path(__file__).parent
MEDIA_DIR = BASE_DIR / INTRUSION_MEDIA_DIR
DATABASE_FILE = BASE_DIR / DATABASE_PATH

# Ensure directories exist
MEDIA_DIR.mkdir(exist_ok=True)

# Administrative settings
REQUIRE_ADMIN = True