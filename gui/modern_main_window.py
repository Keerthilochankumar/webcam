"""
Modern, optimized main window for Camera Privacy Manager
Enhanced UI with better performance and user experience
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from datetime import datetime
from typing import Optional
import threading
import time

from managers.camera_manager import CameraManager
from managers.authentication_manager import AuthenticationManager
from managers.log_manager import LogManager
from managers.intrusion_detector import IntrusionDetector
from managers.email_service import EmailService
from database.database_manager import DatabaseManager
from config import APP_NAME


class ModernMainWindow:
    """Modern, optimized main application window"""
    
    def __init__(self):
        """Initialize the modern main window"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize managers (lazy loading for better startup performance)
        self._managers_initialized = False
        self.db_manager = None
        self.auth_manager = None
        self.camera_manager = None
        self.log_manager = None
        self.intrusion_detector = None
        self.email_service = None
        
        # UI state
        self.status_updating = False
        self.last_status_update = None
        
        # Initialize GUI
        self.root = tk.Tk()
        self.setup_modern_window()
        self.create_modern_widgets()
        
        # Initialize managers after UI is ready
        self.root.after(100, self.initialize_managers_async)
        
        self.logger.info("Modern main window initialized")
    
    def initialize_managers_async(self):
        """Initialize managers asynchronously for better startup performance"""
        def init_managers():
            try:
                self.show_loading("Initializing system...")
                
                self.db_manager = DatabaseManager()
              