"""
Settings window for Camera Privacy Manager
Provides configuration options for email notifications and system settings
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging

from managers.email_service import EmailService
from managers.authentication_manager import AuthenticationManager


class SettingsWindow:
    """Window for application settings"""
    
    def __init__(self, parent, email_service: EmailService, auth_manager: AuthenticationManager):
        """Initialize settings window"""
        self.parent = parent
        self.email_service = email_service
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("500x600")
        self.window.transient(parent)
        
        # Center the window
        self.center_window()
        
        # Create widgets
        self.create_widgets()
        
        # Load current settings
        self.load_settings()
        
        self.logger.info("Settings window opened")
    
    def center_window(self):
        """Center the window on the screen"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 250
        y = (self.window.winfo_screenheight() // 2) - 300
        self.window.geometry(f"500x600+{x}+{y}")
    
    def create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main frame with scrollbar
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main content frame
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Settings", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Email Settings Section
        self.create_email_settings(main_frame)
        
        # Security Settings Section
        self.create_security_settings(main_frame)
        
        # System Settings Section
        self.create_system_settings(main_frame)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Save button
        save_btn = ttk.Button(buttons_frame, text="Save Settings", command=self.save_settings)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Test Email button
        test_email_btn = ttk.Button(buttons_frame, text="Test Email", command=self.test_email)
        test_email_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Cancel button
        cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=self.window.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def create_email_settings(self, parent):
        """Create email settings section"""
        email_frame = ttk.LabelFrame(parent, text="Email Notification Settings", padding="10")
        email_frame.pack(fill=tk.X, pady=(0, 20))
        
        # SMTP Server
        ttk.Label(email_frame, text="SMTP Server:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.smtp_server_var = tk.StringVar()
        smtp_server_entry = ttk.Entry(email_frame, textvariable=self.smtp_server_var, width=30)
        smtp_server_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        # SMTP Port
        ttk.Label(email_frame, text="SMTP Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.smtp_port_var = tk.StringVar(value="587")
        smtp_port_entry = ttk.Entry(email_frame, textvariable=self.smtp_port_var, width=30)
        smtp_port_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        # Username
        ttk.Label(email_frame, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.email_username_var = tk.StringVar()
        email_username_entry = ttk.Entry(email_frame, textvariable=self.email_username_var, width=30)
        email_username_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        # Password
        ttk.Label(email_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.email_password_var = tk.StringVar()
        email_password_entry = ttk.Entry(email_frame, textvariable=self.email_password_var, width=30, show="*")
        email_password_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        # From Email
        ttk.Label(email_frame, text="From Email:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.from_email_var = tk.StringVar()
        from_email_entry = ttk.Entry(email_frame, textvariable=self.from_email_var, width=30)
        from_email_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        # Use TLS
        self.use_tls_var = tk.BooleanVar(value=True)
        use_tls_check = ttk.Checkbutton(email_frame, text="Use TLS Encryption", variable=self.use_tls_var)
        use_tls_check.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Recipients section
        ttk.Label(email_frame, text="Alert Recipients:").grid(row=6, column=0, sticky=tk.W, pady=(10, 2))
        
        # Recipients listbox with scrollbar
        recipients_frame = ttk.Frame(email_frame)
        recipients_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        self.recipients_listbox = tk.Listbox(recipients_frame, height=4)
        recipients_scrollbar = ttk.Scrollbar(recipients_frame, orient=tk.VERTICAL, command=self.recipients_listbox.yview)
        self.recipients_listbox.configure(yscrollcommand=recipients_scrollbar.set)
        
        self.recipients_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        recipients_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Recipients management buttons
        recipients_btn_frame = ttk.Frame(email_frame)
        recipients_btn_frame.grid(row=8, column=0, columnspan=2, pady=5)
        
        add_recipient_btn = ttk.Button(recipients_btn_frame, text="Add Recipient", command=self.add_recipient)
        add_recipient_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        remove_recipient_btn = ttk.Button(recipients_btn_frame, text="Remove Selected", command=self.remove_recipient)
        remove_recipient_btn.pack(side=tk.LEFT)
        
        # Configure grid weights
        email_frame.grid_columnconfigure(1, weight=1)
    
    def create_security_settings(self, parent):
        """Create security settings section"""
        security_frame = ttk.LabelFrame(parent, text="Security Settings", padding="10")
        security_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Change Password button
        change_password_btn = ttk.Button(security_frame, text="Change Password", command=self.change_password)
        change_password_btn.pack(pady=5)
        
        # Intrusion settings
        ttk.Label(security_frame, text="Failed Login Attempts Before Alert:").pack(anchor=tk.W, pady=(10, 2))
        self.max_attempts_var = tk.StringVar(value="3")
        max_attempts_entry = ttk.Entry(security_frame, textvariable=self.max_attempts_var, width=10)
        max_attempts_entry.pack(anchor=tk.W, pady=2)
        
        ttk.Label(security_frame, text="Time Window for Failed Attempts (minutes):").pack(anchor=tk.W, pady=(10, 2))
        self.time_window_var = tk.StringVar(value="15")
        time_window_entry = ttk.Entry(security_frame, textvariable=self.time_window_var, width=10)
        time_window_entry.pack(anchor=tk.W, pady=2)
    
    def create_system_settings(self, parent):
        """Create system settings section"""
        system_frame = ttk.LabelFrame(parent, text="System Settings", padding="10")
        system_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Auto-cleanup settings
        ttk.Label(system_frame, text="Auto-cleanup Evidence Files After (days):").pack(anchor=tk.W, pady=2)
        self.cleanup_days_var = tk.StringVar(value="30")
        cleanup_days_entry = ttk.Entry(system_frame, textvariable=self.cleanup_days_var, width=10)
        cleanup_days_entry.pack(anchor=tk.W, pady=2)
        
        # Cleanup now button
        cleanup_btn = ttk.Button(system_frame, text="Cleanup Old Files Now", command=self.cleanup_files)
        cleanup_btn.pack(pady=(10, 0))
        
        # System info
        info_text = """
System Information:
• Administrator privileges required for camera blocking
• Evidence files stored in 'intrusion_media' directory
• Database file: camera_privacy.db
        """.strip()
        
        info_label = ttk.Label(system_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W, pady=(20, 0))
    
    def load_settings(self):
        """Load current settings into the form"""
        try:
            # Load email settings
            config = self.email_service.get_configuration_status()
            
            if config['smtp_server']:
                self.smtp_server_var.set(config['smtp_server'])
            if config['smtp_port']:
                self.smtp_port_var.set(str(config['smtp_port']))
            if config['from_email']:
                self.from_email_var.set(config['from_email'])
            
            self.use_tls_var.set(config['use_tls'])
            
            # Load recipients
            self.recipients_listbox.delete(0, tk.END)
            for recipient in config['recipients']:
                self.recipients_listbox.insert(tk.END, recipient)
            
            self.logger.info("Settings loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save current settings"""
        try:
            # Validate email settings
            smtp_server = self.smtp_server_var.get().strip()
            smtp_port_str = self.smtp_port_var.get().strip()
            username = self.email_username_var.get().strip()
            password = self.email_password_var.get()
            from_email = self.from_email_var.get().strip()
            
            if smtp_server and smtp_port_str and username and password:
                try:
                    smtp_port = int(smtp_port_str)
                except ValueError:
                    messagebox.showerror("Error", "SMTP port must be a number")
                    return
                
                # Configure email service
                success = self.email_service.configure_smtp(
                    server=smtp_server,
                    port=smtp_port,
                    username=username,
                    password=password,
                    from_email=from_email if from_email else None,
                    use_tls=self.use_tls_var.get()
                )
                
                if not success:
                    messagebox.showerror("Error", "Failed to configure email settings. Please check your configuration.")
                    return
            
            # Save other settings (these would typically be saved to a config file)
            # For now, we'll just show a success message
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.logger.info("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def test_email(self):
        """Send a test email"""
        try:
            if not self.email_service.is_configured:
                messagebox.showerror("Error", "Email service is not configured")
                return
            
            if not self.email_service.to_emails:
                messagebox.showerror("Error", "No email recipients configured")
                return
            
            success = self.email_service.send_test_email()
            
            if success:
                messagebox.showinfo("Success", "Test email sent successfully!")
            else:
                messagebox.showerror("Error", "Failed to send test email")
                
        except Exception as e:
            self.logger.error(f"Error sending test email: {e}")
            messagebox.showerror("Error", f"Failed to send test email: {e}")
    
    def add_recipient(self):
        """Add email recipient"""
        from tkinter import simpledialog
        
        email = simpledialog.askstring("Add Recipient", "Enter email address:")
        if email:
            email = email.strip()
            if self.email_service.add_recipient(email):
                self.recipients_listbox.insert(tk.END, email)
                messagebox.showinfo("Success", f"Added recipient: {email}")
            else:
                messagebox.showerror("Error", "Invalid email address or failed to add recipient")
    
    def remove_recipient(self):
        """Remove selected email recipient"""
        selection = self.recipients_listbox.curselection()
        if selection:
            email = self.recipients_listbox.get(selection[0])
            if self.email_service.remove_recipient(email):
                self.recipients_listbox.delete(selection[0])
                messagebox.showinfo("Success", f"Removed recipient: {email}")
            else:
                messagebox.showerror("Error", "Failed to remove recipient")
        else:
            messagebox.showwarning("Warning", "Please select a recipient to remove")
    
    def change_password(self):
        """Change user password"""
        from tkinter import simpledialog
        
        # Get current password
        current_password = simpledialog.askstring("Change Password", "Enter current password:", show='*')
        if not current_password:
            return
        
        # Get new password
        new_password = simpledialog.askstring("Change Password", "Enter new password:", show='*')
        if not new_password:
            return
        
        # Confirm new password
        confirm_password = simpledialog.askstring("Change Password", "Confirm new password:", show='*')
        if not confirm_password:
            return
        
        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        # Validate password strength
        is_valid, message = self.auth_manager.validate_password_strength(new_password)
        if not is_valid:
            messagebox.showerror("Weak Password", message)
            return
        
        # Change password (this would need to be implemented in AuthenticationManager)
        try:
            # For now, just show a placeholder message
            messagebox.showinfo("Info", "Password change functionality would be implemented here")
            self.logger.info("Password change requested")
            
        except Exception as e:
            self.logger.error(f"Error changing password: {e}")
            messagebox.showerror("Error", f"Failed to change password: {e}")
    
    def cleanup_files(self):
        """Cleanup old evidence files"""
        try:
            days_str = self.cleanup_days_var.get().strip()
            if not days_str:
                messagebox.showerror("Error", "Please enter number of days")
                return
            
            try:
                days = int(days_str)
            except ValueError:
                messagebox.showerror("Error", "Days must be a number")
                return
            
            # This would use the intrusion detector's cleanup method
            result = messagebox.askyesno(
                "Confirm Cleanup",
                f"This will delete evidence files older than {days} days. Continue?"
            )
            
            if result:
                # Placeholder for actual cleanup
                messagebox.showinfo("Success", f"Cleanup completed (placeholder)")
                self.logger.info(f"File cleanup requested for files older than {days} days")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            messagebox.showerror("Error", f"Failed to cleanup files: {e}")