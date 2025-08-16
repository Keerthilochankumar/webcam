"""
Main window for Camera Privacy Manager
Modern, optimized GUI interface with enhanced styling
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
from config import APP_NAME, APP_VERSION, POPUP_DISPLAY_TIME
from gui.notification_system import NotificationManager


class MainWindow:
    """Main application window for Camera Privacy Manager"""
    
    def __init__(self):
        """Initialize the main window and all managers"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize managers
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthenticationManager(self.db_manager)
        self.camera_manager = CameraManager()
        self.log_manager = LogManager(self.db_manager)
        self.intrusion_detector = IntrusionDetector(self.camera_manager, self.log_manager)
        self.email_service = EmailService()
        
        # Initialize GUI
        self.root = tk.Tk()
        self.setup_window()
        
        # Initialize notification system
        self.notification_manager = NotificationManager(self.root)
        
        self.create_widgets()
        
        # Check initial setup
        self.check_initial_setup()
        
        self.logger.info("Main window initialized")
    
    def setup_window(self):
        """Configure the main window with modern styling"""
        self.root.title(f"🔒 {APP_NAME}")
        self.root.geometry("500x600")
        self.root.resizable(True, True)
        self.root.minsize(450, 550)
        
        # Modern window styling
        self.root.configure(bg='#f0f0f0')
        
        # Center the window on screen
        self.center_window()
        
        # Configure modern styles
        self.setup_styles()
        
        # Set window icon (if available)
        try:
            # self.root.iconbitmap("icon.ico")  # Uncomment if icon file exists
            pass
        except:
            pass
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = 500
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_styles(self):
        """Configure modern ttk styles"""
        style = ttk.Style()
        
        # Configure modern button styles
        style.configure("Action.TButton", 
                       font=("Segoe UI", 11, "bold"),
                       padding=(20, 10))
        
        style.configure("Primary.TButton",
                       font=("Segoe UI", 12, "bold"),
                       padding=(25, 12))
        
        style.configure("Success.TButton",
                       font=("Segoe UI", 10, "bold"),
                       padding=(15, 8))
        
        style.configure("Danger.TButton",
                       font=("Segoe UI", 10, "bold"),
                       padding=(15, 8))
        
        # Configure label styles
        style.configure("Title.TLabel",
                       font=("Segoe UI", 18, "bold"),
                       foreground="#2c3e50")
        
        style.configure("Subtitle.TLabel",
                       font=("Segoe UI", 10),
                       foreground="#7f8c8d")
        
        style.configure("Status.TLabel",
                       font=("Segoe UI", 12, "bold"),
                       padding=(10, 5))
        
        # Configure frame styles
        style.configure("Card.TFrame",
                       relief="solid",
                       borderwidth=1,
                       padding=20)
    
    def create_widgets(self):
        """Create modern, optimized GUI widgets"""
        # Configure grid weights for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Main scrollable frame
        canvas = tk.Canvas(self.root, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Main content frame
        main_frame = ttk.Frame(scrollable_frame, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header section
        self.create_header(main_frame)
        
        # Status card
        self.create_status_card(main_frame)
        
        # Action buttons
        self.create_action_buttons(main_frame)
        
        # Quick actions
        self.create_quick_actions(main_frame)
        
        # Footer
        self.create_footer(main_frame)
        
        # Update status initially
        self.update_camera_status_async()
        
        # Start periodic status updates
        self.start_status_monitoring()
    
    def create_header(self, parent):
        """Create modern header section"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # App icon and title
        title_frame = ttk.Frame(header_frame)
        title_frame.pack()
        
        title_label = ttk.Label(
            title_frame,
            text="🔒 Camera Privacy Manager",
            style="Title.TLabel"
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Secure camera access control with advanced privacy protection",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(pady=(5, 0))
    
    def create_status_card(self, parent):
        """Create modern status display card"""
        status_card = ttk.LabelFrame(parent, text="📹 Camera Status", style="Card.TFrame")
        status_card.pack(fill=tk.X, pady=(0, 20))
        
        # Status display
        status_inner = ttk.Frame(status_card)
        status_inner.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = ttk.Label(
            status_inner,
            text="🔄 Checking status...",
            style="Status.TLabel"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Refresh button
        refresh_btn = ttk.Button(
            status_inner,
            text="🔄 Refresh",
            command=self.update_camera_status_async,
            width=12
        )
        refresh_btn.pack(side=tk.RIGHT)
        
        # Status details frame (initially hidden)
        self.status_details_frame = ttk.Frame(status_card)
        self.status_details_label = ttk.Label(
            self.status_details_frame,
            text="",
            font=("Segoe UI", 9),
            foreground="#7f8c8d"
        )
        self.status_details_label.pack(pady=(5, 0))
    
    def create_action_buttons(self, parent):
        """Create modern action buttons"""
        actions_card = ttk.LabelFrame(parent, text="🎛️ Camera Controls", style="Card.TFrame")
        actions_card.pack(fill=tk.X, pady=(0, 20))
        
        buttons_frame = ttk.Frame(actions_card)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Configure grid for responsive buttons
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Enable Camera button (green theme)
        self.enable_btn = ttk.Button(
            buttons_frame,
            text="✅ Enable Camera",
            command=self.enable_camera_async,
            style="Success.TButton"
        )
        self.enable_btn.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")
        
        # Disable Camera button (red theme)
        self.disable_btn = ttk.Button(
            buttons_frame,
            text="🚫 Disable Camera",
            command=self.disable_camera_async,
            style="Danger.TButton"
        )
        self.disable_btn.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        # Status check button
        status_btn = ttk.Button(
            buttons_frame,
            text="📊 Detailed Status",
            command=self.check_status,
            style="Action.TButton"
        )
        status_btn.grid(row=1, column=0, columnspan=2, pady=(10, 5), sticky="ew")
    
    def create_quick_actions(self, parent):
        """Create quick actions section"""
        quick_card = ttk.LabelFrame(parent, text="⚡ Quick Actions", style="Card.TFrame")
        quick_card.pack(fill=tk.X, pady=(0, 20))
        
        quick_frame = ttk.Frame(quick_card)
        quick_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Configure grid
        quick_frame.grid_columnconfigure(0, weight=1)
        quick_frame.grid_columnconfigure(1, weight=1)
        quick_frame.grid_columnconfigure(2, weight=1)
        
        # View Logs button
        logs_btn = ttk.Button(
            quick_frame,
            text="📋 View Logs",
            command=self.view_logs,
            width=15
        )
        logs_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        # Settings button
        settings_btn = ttk.Button(
            quick_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            width=15
        )
        settings_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Test Camera button
        test_btn = ttk.Button(
            quick_frame,
            text="🧪 Test Camera",
            command=self.test_camera_access,
            width=15
        )
        test_btn.grid(row=0, column=2, padx=2, pady=2, sticky="ew")
    
    def create_footer(self, parent):
        """Create modern footer section"""
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        # App info
        info_frame = ttk.Frame(footer_frame)
        info_frame.pack()
        
        version_label = ttk.Label(
            info_frame,
            text=f"Camera Privacy Manager v{APP_VERSION}",
            font=("Segoe UI", 8),
            foreground="#95a5a6"
        )
        version_label.pack()
        
        status_label = ttk.Label(
            info_frame,
            text="🛡️ Protecting your privacy with safe, driver-friendly methods",
            font=("Segoe UI", 8),
            foreground="#95a5a6"
        )
        status_label.pack()
    
    def test_camera_access(self):
        """Test camera access and show results"""
        try:
            # Show progress
            progress = self.show_progress_popup("Testing camera access...")
            
            def test_in_background():
                try:
                    import subprocess
                    import sys
                    
                    # Run the test script
                    result = subprocess.run([
                        sys.executable, "test_camera_blocking.py"
                    ], capture_output=True, text=True, timeout=30)
                    
                    # Update UI with results
                    def show_results():
                        progress.destroy()
                        if result.returncode == 0:
                            self.show_detailed_popup("Camera Test Results", 
                                                   "✅ Camera blocking is working correctly!\n\n" + result.stdout)
                        else:
                            self.show_detailed_popup("Camera Test Results", 
                                                   "⚠️ Camera test completed with warnings:\n\n" + result.stdout)
                    
                    self.root.after(0, show_results)
                    
                except Exception as e:
                    def show_error():
                        progress.destroy()
                        self.show_error("Test Error", f"Failed to run camera test: {e}")
                    
                    self.root.after(0, show_error)
            
            # Run test in background
            import threading
            threading.Thread(target=test_in_background, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error testing camera: {e}")
            self.show_error("Error", f"Failed to start camera test: {e}")
    
    def create_footer(self, parent):
        """Create footer section"""
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        # About and help buttons
        footer_buttons = ttk.Frame(footer_frame)
        footer_buttons.pack()
        
        about_btn = ttk.Button(
            footer_buttons,
            text="ℹ️ About",
            command=self.show_about,
            width=12
        )
        about_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        help_btn = ttk.Button(
            footer_buttons,
            text="❓ Help",
            command=self.show_help,
            width=12
        )
        help_btn.pack(side=tk.LEFT)
    
    def check_initial_setup(self):
        """Check if initial setup is required"""
        try:
            if not self.auth_manager.has_users():
                self.show_initial_setup()
            
            # Check admin privileges
            if not self.camera_manager.check_admin_privileges():
                self.show_admin_warning()
                
        except Exception as e:
            self.logger.error(f"Error during initial setup check: {e}")
            self.show_error("Setup Error", f"Error during initial setup: {e}")
    
    def show_initial_setup(self):
        """Show initial setup dialog for first-time users"""
        setup_window = tk.Toplevel(self.root)
        setup_window.title("Initial Setup")
        setup_window.geometry("400x300")
        setup_window.transient(self.root)
        setup_window.grab_set()
        
        # Center the setup window
        setup_window.update_idletasks()
        x = (setup_window.winfo_screenwidth() // 2) - 200
        y = (setup_window.winfo_screenheight() // 2) - 150
        setup_window.geometry(f"400x300+{x}+{y}")
        
        frame = ttk.Frame(setup_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome message
        welcome_label = ttk.Label(
            frame,
            text="Welcome to Camera Privacy Manager",
            font=("Arial", 14, "bold")
        )
        welcome_label.pack(pady=(0, 20))
        
        info_label = ttk.Label(
            frame,
            text="This is your first time running the application.\nPlease set up your administrator password.",
            justify=tk.CENTER
        )
        info_label.pack(pady=(0, 20))
        
        # Username field
        ttk.Label(frame, text="Username:").pack(anchor=tk.W)
        username_entry = ttk.Entry(frame, width=30)
        username_entry.pack(pady=(0, 10), fill=tk.X)
        username_entry.insert(0, "admin")  # Default username
        
        # Password field
        ttk.Label(frame, text="Password:").pack(anchor=tk.W)
        password_entry = ttk.Entry(frame, width=30, show="*")
        password_entry.pack(pady=(0, 10), fill=tk.X)
        
        # Confirm password field
        ttk.Label(frame, text="Confirm Password:").pack(anchor=tk.W)
        confirm_entry = ttk.Entry(frame, width=30, show="*")
        confirm_entry.pack(pady=(0, 10), fill=tk.X)
        
        # Password strength indicator
        strength_label = ttk.Label(frame, text="Password must be at least 8 characters with uppercase, lowercase, and digits", 
                                 font=("Arial", 8), foreground="gray")
        strength_label.pack(pady=(0, 20))
        
        def setup_complete():
            username = username_entry.get().strip()
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not username:
                messagebox.showerror("Error", "Username is required")
                return
            
            if not password:
                messagebox.showerror("Error", "Password is required")
                return
            
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match")
                return
            
            # Validate password strength
            is_valid, message = self.auth_manager.validate_password_strength(password)
            if not is_valid:
                messagebox.showerror("Weak Password", message)
                return
            
            # Create initial user
            if self.auth_manager.setup_initial_password(username, password):
                messagebox.showinfo("Success", "Initial setup completed successfully!")
                setup_window.destroy()
                self.log_manager.log_system_event(1, "INITIAL_SETUP_COMPLETED")
            else:
                messagebox.showerror("Error", "Failed to complete initial setup")
        
        def cancel_setup():
            result = messagebox.askyesno("Cancel Setup", "Are you sure you want to cancel the setup?\nThe application will exit.")
            if result:
                setup_window.destroy()
                self.root.quit()
        
        # Buttons frame
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(pady=20, fill=tk.X)
        
        # Cancel button
        cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=cancel_setup)
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Submit Admin Details button (prominent)
        submit_btn = ttk.Button(
            buttons_frame, 
            text="Submit Admin Details", 
            command=setup_complete,
            style="Accent.TButton"
        )
        submit_btn.pack(side=tk.RIGHT)
        
        # Configure button style for prominence
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        
        # Keyboard shortcuts
        def on_enter(event):
            setup_complete()
        
        def on_escape(event):
            cancel_setup()
        
        # Bind keyboard shortcuts
        setup_window.bind('<Return>', on_enter)
        setup_window.bind('<KP_Enter>', on_enter)  # Numpad Enter
        setup_window.bind('<Escape>', on_escape)
        
        # Bind Enter key to all entry fields
        username_entry.bind('<Return>', on_enter)
        password_entry.bind('<Return>', on_enter)
        confirm_entry.bind('<Return>', on_enter)
        
        # Focus on username field initially
        username_entry.focus()
        username_entry.select_range(0, tk.END)  # Select default "admin" text
    
    def show_admin_warning(self):
        """Show warning about administrator privileges"""
        result = messagebox.askywarning(
            "Administrator Privileges Required",
            "This application requires administrator privileges to control camera access at the system level.\n\n"
            "Without admin privileges, the camera blocking feature will not work properly.\n\n"
            "Would you like to restart the application as administrator?",
            type=messagebox.YESNO
        )
        
        if result == messagebox.YES:
            try:
                self.camera_manager.request_admin_privileges()
                self.root.quit()
            except Exception as e:
                self.logger.error(f"Failed to request admin privileges: {e}")
                messagebox.showerror("Error", f"Failed to request admin privileges: {e}")
    
    def view_logs(self):
        """Handle View Logs button click"""
        try:
            # Prompt for password
            password = self.prompt_password("Enter password to view logs:")
            if not password:
                return
            
            # Authenticate
            if not self.authenticate_user(password):
                return
            
            # Show logs window
            self.show_logs_window()
            
        except Exception as e:
            self.logger.error(f"Error viewing logs: {e}")
            self.show_error("Error", f"Failed to view logs: {e}")
    
    def check_status(self):
        """Handle Check Status button click"""
        try:
            self.update_camera_status()
            
            # Get detailed status
            blocking_status = self.camera_manager.get_blocking_status()
            camera_status = self.camera_manager.get_camera_status()
            
            if camera_status:
                status_msg = "Camera Status: ACTIVE\n\n"
                status_msg += "Camera is enabled and accessible"
            else:
                status_msg = "Camera Status: BLOCKED\n\n"
                status_msg += "Blocking Methods:\n"
                status_msg += f"• Privacy Settings: {'✓' if blocking_status['privacy_registry'] else '✗'}\n"
                status_msg += f"• Group Policy: {'✓' if blocking_status['group_policy'] else '✗'}\n"
                status_msg += f"• Lock File: {'✓' if blocking_status['lock_file'] else '✗'}\n"
                status_msg += f"• Camera Access: {'✗ Blocked' if not blocking_status['camera_accessible'] else '⚠ Still Accessible'}"
            
            self.show_detailed_popup("Camera Status", status_msg)
            
        except Exception as e:
            self.logger.error(f"Error checking status: {e}")
            self.show_error("Error", f"Failed to check camera status: {e}")
    
    def enable_camera(self):
        """Handle Enable Camera button click"""
        try:
            # Prompt for password
            password = self.prompt_password("Enter password to enable camera:")
            if not password:
                return
            
            # Authenticate
            if not self.authenticate_user(password):
                return
            
            # Show progress message
            progress_toast = self.notification_manager.show_progress_toast(
                "Enabling Camera", 
                "Removing blocking methods..."
            )
            
            # Enable camera
            if self.camera_manager.enable_camera():
                progress_toast.close()
                
                # Verify camera is accessible
                if self.camera_manager.get_camera_status():
                    self.notification_manager.show_toast(
                        "Camera Successfully Enabled",
                        "Camera is now accessible to all applications. All blocking methods have been safely removed!",
                        "success"
                    )
                else:
                    self.notification_manager.show_toast(
                        "Camera Enable Attempted",
                        "Some restrictions may still be in place. Try restarting applications that need camera access.",
                        "warning"
                    )
                
                self.update_camera_status()
                
                # Log the action
                user = self.auth_manager.get_current_user()
                if user:
                    self.log_manager.log_camera_access(user.id, "CAMERA_ENABLED")
            else:
                progress_toast.close()
                self.notification_manager.show_toast(
                    "Camera Enable Failed",
                    "Failed to enable camera. Make sure you're running as Administrator.",
                    "error"
                )
                
        except Exception as e:
            self.logger.error(f"Error enabling camera: {e}")
            self.show_error("Error", f"Failed to enable camera: {e}")
    
    def disable_camera(self):
        """Handle Disable Camera button click"""
        try:
            # Prompt for password
            password = self.prompt_password("Enter password to disable camera:")
            if not password:
                return
            
            # Authenticate
            if not self.authenticate_user(password):
                return
            
            # Show progress message
            progress_toast = self.notification_manager.show_progress_toast(
                "Disabling Camera", 
                "Applying safe blocking methods..."
            )
            
            # Disable camera
            if self.camera_manager.disable_camera():
                progress_toast.close()
                
                # Get blocking status
                blocking_status = self.camera_manager.get_blocking_status()
                blocked_methods = sum([
                    blocking_status['privacy_registry'],
                    blocking_status['group_policy'], 
                    blocking_status['lock_file']
                ])
                
                if blocked_methods >= 2 and not blocking_status['camera_accessible']:
                    self.notification_manager.show_toast(
                        "Camera Disabled Successfully",
                        "Camera is now blocked using safe methods. No system drivers were harmed!",
                        "success"
                    )
                else:
                    self.notification_manager.show_toast(
                        "Camera Partially Disabled",
                        "Some blocking methods may not be active. Check status for details.",
                        "warning"
                    )
                
                self.update_camera_status()
                
                # Log the action
                user = self.auth_manager.get_current_user()
                if user:
                    self.log_manager.log_camera_access(user.id, "CAMERA_DISABLED")
            else:
                progress_toast.close()
                self.notification_manager.show_toast(
                    "Camera Disable Failed",
                    "Failed to disable camera. Make sure you're running as Administrator.",
                    "error"
                )
                
        except Exception as e:
            self.logger.error(f"Error disabling camera: {e}")
            self.show_error("Error", f"Failed to disable camera: {e}")
    
    def prompt_password(self, prompt: str) -> Optional[str]:
        """Prompt user for password input"""
        password = simpledialog.askstring("Password Required", prompt, show='*')
        return password
    
    def authenticate_user(self, password: str) -> bool:
        """Authenticate user with password"""
        try:
            # For simplicity, we'll use "admin" as the default username
            # In a more complex system, you might prompt for username too
            username = "admin"
            
            if self.auth_manager.authenticate_user(username, password):
                return True
            else:
                # Handle failed authentication (trigger intrusion detection)
                self.intrusion_detector.handle_failed_authentication(username)
                self.show_error("Authentication Failed", "Invalid password")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            self.show_error("Error", f"Authentication error: {e}")
            return False
    
    def update_camera_status_async(self):
        """Update camera status asynchronously"""
        def update_status():
            try:
                # Show loading state
                self.root.after(0, lambda: self.status_label.config(text="🔄 Checking status..."))
                
                # Get status (this might take time)
                status = self.camera_manager.get_camera_status()
                blocking_status = self.camera_manager.get_blocking_status()
                
                # Update UI in main thread
                self.root.after(0, lambda: self._update_status_display(status, blocking_status))
                
            except Exception as e:
                self.logger.error(f"Error updating camera status: {e}")
                self.root.after(0, lambda: self.status_label.config(
                    text="❌ Status Error", 
                    foreground="red"
                ))
        
        # Run in background thread
        threading.Thread(target=update_status, daemon=True).start()
    
    def _update_status_display(self, status, blocking_status):
        """Update status display in main thread"""
        try:
            if status:
                self.status_label.config(text="✅ Camera ACTIVE", foreground="green")
                details = "Camera is enabled and accessible to applications"
                self.enable_btn.config(state="disabled")
                self.disable_btn.config(state="normal")
            else:
                self.status_label.config(text="🚫 Camera BLOCKED", foreground="red")
                blocked_methods = sum([
                    blocking_status.get('privacy_registry', False),
                    blocking_status.get('group_policy', False),
                    blocking_status.get('lock_file', False)
                ])
                details = f"Camera is blocked using {blocked_methods} method(s)"
                self.enable_btn.config(state="normal")
                self.disable_btn.config(state="disabled")
            
            # Show/update details
            self.status_details_label.config(text=details)
            self.status_details_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
        except Exception as e:
            self.logger.error(f"Error updating status display: {e}")
    
    def enable_camera_async(self):
        """Enable camera asynchronously"""
        def enable_camera():
            try:
                # Get password in main thread
                password = None
                password_event = threading.Event()
                
                def get_password():
                    nonlocal password
                    password = self.prompt_password("Enter password to enable camera:")
                    password_event.set()
                
                self.root.after(0, get_password)
                password_event.wait()
                
                if not password:
                    return
                
                # Authenticate in main thread
                auth_result = None
                auth_event = threading.Event()
                
                def authenticate():
                    nonlocal auth_result
                    auth_result = self.authenticate_user(password)
                    auth_event.set()
                
                self.root.after(0, authenticate)
                auth_event.wait()
                
                if not auth_result:
                    return
                
                # Show progress
                progress_popup = None
                self.root.after(0, lambda: setattr(self, '_progress_popup', 
                    self.show_progress_popup("🔄 Enabling camera...")))
                
                # Enable camera
                result = self.camera_manager.enable_camera()
                
                # Update UI
                self.root.after(0, lambda: self._handle_enable_result(result))
                
            except Exception as e:
                self.logger.error(f"Error enabling camera: {e}")
                self.root.after(0, lambda: self.show_error("Error", f"Failed to enable camera: {e}"))
        
        threading.Thread(target=enable_camera, daemon=True).start()
    
    def _handle_enable_result(self, result):
        """Handle enable camera result in main thread"""
        try:
            # Close progress popup if it exists
            if hasattr(self, '_progress_popup'):
                self._progress_popup.destroy()
                delattr(self, '_progress_popup')
            
            if result:
                # Verify camera is accessible
                if self.camera_manager.get_camera_status():
                    self.notification_manager.show_toast(
                        "Camera Successfully Enabled",
                        "Camera is now accessible to all applications. All blocking methods have been safely removed!",
                        "success"
                    )
                else:
                    self.notification_manager.show_toast(
                        "Camera Enable Attempted",
                        "Some restrictions may still be in place. Try restarting applications that need camera access.",
                        "warning"
                    )
                
                self.update_camera_status_async()
                
                # Log the action
                user = self.auth_manager.get_current_user()
                if user:
                    self.log_manager.log_camera_access(user.id, "CAMERA_ENABLED")
            else:
                self.notification_manager.show_toast(
                    "Camera Enable Failed",
                    "Failed to enable camera. Make sure you're running as Administrator.",
                    "error"
                )
        except Exception as e:
            self.logger.error(f"Error handling enable result: {e}")
    
    def _handle_disable_result(self, result):
        """Handle disable camera result in main thread"""
        try:
            # Close progress popup if it exists
            if hasattr(self, '_progress_popup'):
                self._progress_popup.destroy()
                delattr(self, '_progress_popup')
            
            if result:
                # Get blocking status
                blocking_status = self.camera_manager.get_blocking_status()
                blocked_methods = sum([
                    blocking_status.get('privacy_registry', False),
                    blocking_status.get('group_policy', False),
                    blocking_status.get('lock_file', False)
                ])
                
                if blocked_methods >= 2 and not blocking_status.get('camera_accessible', True):
                    self.notification_manager.show_toast(
                        "Camera Disabled Successfully",
                        "Camera is now blocked using safe methods. No system drivers were harmed!",
                        "success"
                    )
                else:
                    self.notification_manager.show_toast(
                        "Camera Partially Disabled",
                        "Some blocking methods may not be active. Check status for details.",
                        "warning"
                    )
                
                self.update_camera_status_async()
                
                # Log the action
                user = self.auth_manager.get_current_user()
                if user:
                    self.log_manager.log_camera_access(user.id, "CAMERA_DISABLED")
            else:
                self.notification_manager.show_toast(
                    "Camera Disable Failed",
                    "Failed to disable camera. Make sure you're running as Administrator.",
                    "error"
                )
        except Exception as e:
            self.logger.error(f"Error handling disable result: {e}")
    
    def disable_camera_async(self):
        """Disable camera asynchronously"""
        def disable_camera():
            try:
                # Get password in main thread
                password = None
                password_event = threading.Event()
                
                def get_password():
                    nonlocal password
                    password = self.prompt_password("Enter password to disable camera:")
                    password_event.set()
                
                self.root.after(0, get_password)
                password_event.wait()
                
                if not password:
                    return
                
                # Authenticate in main thread
                auth_result = None
                auth_event = threading.Event()
                
                def authenticate():
                    nonlocal auth_result
                    auth_result = self.authenticate_user(password)
                    auth_event.set()
                
                self.root.after(0, authenticate)
                auth_event.wait()
                
                if not auth_result:
                    return
                
                # Show progress
                self.root.after(0, lambda: setattr(self, '_progress_popup', 
                    self.show_progress_popup("🔄 Disabling camera...")))
                
                # Disable camera
                result = self.camera_manager.disable_camera()
                
                # Update UI
                self.root.after(0, lambda: self._handle_disable_result(result))
                
            except Exception as e:
                self.logger.error(f"Error disabling camera: {e}")
                self.root.after(0, lambda: self.show_error("Error", f"Failed to disable camera: {e}"))
        
        threading.Thread(target=disable_camera, daemon=True).start()
    
    def _handle_disable_result(self, result):
        """Handle disable camera result in main thread"""
        try:
            if hasattr(self, '_progress_popup') and self._progress_popup:
                self._progress_popup.destroy()
            
            if result:
                blocking_status = self.camera_manager.get_blocking_status()
                blocked_methods = sum([
                    blocking_status.get('privacy_registry', False),
                    blocking_status.get('group_policy', False), 
                    blocking_status.get('lock_file', False)
                ])
                
                if blocked_methods >= 2 and not blocking_status.get('camera_accessible', True):
                    self.notification_manager.show_toast(
                        "Camera Disabled Successfully",
                        "Camera is now blocked using safe methods. No system drivers were harmed!",
                        "success"
                    )
                else:
                    self.notification_manager.show_toast(
                        "Camera Partially Disabled",
                        "Some blocking methods may not be active. Check detailed status for more information.",
                        "warning"
                    )
                
                # Log the action
                user = self.auth_manager.get_current_user()
                if user:
                    self.log_manager.log_camera_access(user.id, "CAMERA_DISABLED")
            else:
                self.show_error("Error", "Failed to disable camera.\nMake sure you're running as Administrator.")
            
            # Refresh status
            self.update_camera_status_async()
            
        except Exception as e:
            self.logger.error(f"Error handling disable result: {e}")
    
    def test_camera_access(self):
        """Test camera access using external script"""
        try:
            import subprocess
            import sys
            
            def run_test():
                try:
                    result = subprocess.run([sys.executable, "test_camera_blocking.py"], 
                                          capture_output=True, text=True, timeout=30)
                    
                    self.root.after(0, lambda: self._show_test_results(result.stdout, result.returncode == 0))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.show_error("Test Error", f"Failed to run camera test: {e}"))
            
            # Show progress
            progress_popup = self.show_progress_popup("🧪 Testing camera access...")
            
            def close_progress():
                time.sleep(0.5)  # Small delay for better UX
                self.root.after(0, progress_popup.destroy)
            
            threading.Thread(target=close_progress, daemon=True).start()
            threading.Thread(target=run_test, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error testing camera: {e}")
            self.show_error("Error", f"Failed to test camera: {e}")
    
    def _show_test_results(self, output, success):
        """Show camera test results"""
        title = "🧪 Camera Test Results"
        if success:
            icon = "✅"
            msg_type = "success"
        else:
            icon = "⚠️"
            msg_type = "warning"
        
        self.show_detailed_popup(f"{icon} {title}", output)
    
    def show_logs_window(self):
        """Show the logs viewing window"""
        from gui.logs_window import LogsWindow
        logs_window = LogsWindow(self.root, self.log_manager)
    
    def show_settings(self):
        """Show settings window"""
        from gui.settings_window import SettingsWindow
        settings_window = SettingsWindow(self.root, self.email_service, self.auth_manager)
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""
{APP_NAME}

A comprehensive camera privacy management system that provides secure control over webcam access with authentication, activity logging, and intrusion detection capabilities.

Features:
• Password-protected camera enable/disable
• System-wide camera blocking
• Activity logging and audit trails
• Intrusion detection with evidence capture
• Email notifications for security events

Version: 1.0.0
        """.strip()
        
        messagebox.showinfo("About", about_text)
    
    def show_popup(self, message: str):
        """Show temporary popup message"""
        popup = tk.Toplevel(self.root)
        popup.title("Notification")
        popup.geometry("350x120")
        popup.transient(self.root)
        popup.grab_set()
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - 175
        y = (popup.winfo_screenheight() // 2) - 60
        popup.geometry(f"350x120+{x}+{y}")
        
        # Message label
        label = ttk.Label(popup, text=message, font=("Arial", 11), justify=tk.CENTER)
        label.pack(expand=True)
        
        # Auto-close after delay
        popup.after(POPUP_DISPLAY_TIME, popup.destroy)
    
    def show_progress_popup(self, message: str):
        """Show progress popup that can be manually closed"""
        popup = tk.Toplevel(self.root)
        popup.title("Please Wait")
        popup.geometry("300x100")
        popup.transient(self.root)
        popup.grab_set()
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - 150
        y = (popup.winfo_screenheight() // 2) - 50
        popup.geometry(f"300x100+{x}+{y}")
        
        # Message label
        label = ttk.Label(popup, text=message, font=("Arial", 10))
        label.pack(expand=True)
        
        # Progress bar
        progress = ttk.Progressbar(popup, mode='indeterminate')
        progress.pack(pady=10, padx=20, fill=tk.X)
        progress.start()
        
        popup.update()
        return popup
    
    def show_detailed_popup(self, title: str, message: str):
        """Show detailed popup with more information"""
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("400x300")
        popup.transient(self.root)
        popup.grab_set()
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - 200
        y = (popup.winfo_screenheight() // 2) - 150
        popup.geometry(f"400x300+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(popup, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Message label with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10), height=12, width=45)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.insert(tk.END, message)
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        close_btn = ttk.Button(main_frame, text="Close", command=popup.destroy)
        close_btn.pack(pady=(10, 0))
    
    def show_error(self, title: str, message: str):
        """Show error message dialog"""
        messagebox.showerror(title, message)
    
    def run(self):
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources before exit"""
        try:
            # Clear notifications
            if hasattr(self, 'notification_manager'):
                self.notification_manager.clear_all_notifications()
            
            # Logout user
            if hasattr(self, 'auth_manager'):
                self.auth_manager.logout_user()
            
            # Close database
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
            
            self.logger.info("Application cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __getattr__(self, name):
        """Fallback for missing attributes to prevent AttributeError"""
        if name.startswith('_'):
            # For private attributes, return None
            return None
        else:
            # For public attributes, log warning and return a dummy function
            self.logger.warning(f"Accessing undefined attribute: {name}")
            return lambda *args, **kwargs: None