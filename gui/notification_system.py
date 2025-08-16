"""
Modern notification system for Camera Privacy Manager
Provides toast notifications and modern popups
"""
import tkinter as tk
from tkinter import ttk
import threading
import time


class NotificationManager:
    """Manages modern notifications and popups"""
    
    def __init__(self, parent_window):
        """Initialize notification manager"""
        self.parent = parent_window
        self.active_notifications = []
    
    def show_toast(self, title: str, message: str, notification_type: str = "info", duration: int = 4000):
        """Show modern toast notification"""
        toast = ToastNotification(self.parent, title, message, notification_type, duration)
        self.active_notifications.append(toast)
        toast.show()
        
        # Auto-remove from list when closed
        def remove_notification():
            if toast in self.active_notifications:
                self.active_notifications.remove(toast)
        
        self.parent.after(duration + 500, remove_notification)
    
    def show_progress_toast(self, title: str, message: str):
        """Show progress toast that can be updated"""
        toast = ProgressToast(self.parent, title, message)
        self.active_notifications.append(toast)
        toast.show()
        return toast
    
    def clear_all_notifications(self):
        """Clear all active notifications"""
        for notification in self.active_notifications:
            try:
                notification.close()
            except:
                pass
        self.active_notifications.clear()


class ToastNotification:
    """Modern toast notification"""
    
    def __init__(self, parent, title, message, notification_type="info", duration=4000):
        """Initialize toast notification"""
        self.parent = parent
        self.title = title
        self.message = message
        self.type = notification_type
        self.duration = duration
        self.window = None
        
        # Type configurations
        self.type_config = {
            "info": {"bg": "#3498db", "fg": "white", "icon": "ℹ️"},
            "success": {"bg": "#27ae60", "fg": "white", "icon": "✅"},
            "warning": {"bg": "#f39c12", "fg": "white", "icon": "⚠️"},
            "error": {"bg": "#e74c3c", "fg": "white", "icon": "❌"}
        }
    
    def show(self):
        """Show the toast notification"""
        try:
            # Create toast window
            self.window = tk.Toplevel(self.parent)
            self.window.withdraw()  # Hide initially
            
            # Configure window
            self.window.overrideredirect(True)  # Remove window decorations
            self.window.attributes('-topmost', True)  # Always on top
            
            # Get configuration
            config = self.type_config.get(self.type, self.type_config["info"])
            
            # Create main frame
            main_frame = tk.Frame(
                self.window,
                bg=config["bg"],
                relief="solid",
                bd=1
            )
            main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # Icon and title frame
            header_frame = tk.Frame(main_frame, bg=config["bg"])
            header_frame.pack(fill=tk.X, padx=15, pady=(10, 5))
            
            # Icon
            icon_label = tk.Label(
                header_frame,
                text=config["icon"],
                bg=config["bg"],
                fg=config["fg"],
                font=("Segoe UI", 12)
            )
            icon_label.pack(side=tk.LEFT)
            
            # Title
            title_label = tk.Label(
                header_frame,
                text=self.title,
                bg=config["bg"],
                fg=config["fg"],
                font=("Segoe UI", 10, "bold")
            )
            title_label.pack(side=tk.LEFT, padx=(10, 0))
            
            # Close button
            close_btn = tk.Label(
                header_frame,
                text="✕",
                bg=config["bg"],
                fg=config["fg"],
                font=("Segoe UI", 10),
                cursor="hand2"
            )
            close_btn.pack(side=tk.RIGHT)
            close_btn.bind("<Button-1>", lambda e: self.close())
            
            # Message
            message_label = tk.Label(
                main_frame,
                text=self.message,
                bg=config["bg"],
                fg=config["fg"],
                font=("Segoe UI", 9),
                wraplength=300,
                justify=tk.LEFT
            )
            message_label.pack(fill=tk.X, padx=15, pady=(0, 10))
            
            # Position toast
            self.position_toast()
            
            # Show with animation
            self.animate_in()
            
            # Auto-close after duration
            self.window.after(self.duration, self.animate_out)
            
        except Exception as e:
            print(f"Error showing toast: {e}")
    
    def position_toast(self):
        """Position toast in bottom-right corner"""
        try:
            self.window.update_idletasks()
            
            # Get screen dimensions
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            # Get toast dimensions
            toast_width = 350
            toast_height = self.window.winfo_reqheight()
            
            # Calculate position (bottom-right with margin)
            x = screen_width - toast_width - 20
            y = screen_height - toast_height - 50
            
            # Adjust for multiple toasts
            offset = len([n for n in getattr(self.parent, 'notification_manager', {}).get('active_notifications', [])]) * (toast_height + 10)
            y -= offset
            
            self.window.geometry(f"{toast_width}x{toast_height}+{x}+{y}")
            
        except Exception as e:
            print(f"Error positioning toast: {e}")
    
    def animate_in(self):
        """Animate toast sliding in"""
        try:
            self.window.deiconify()  # Show window
            self.window.attributes('-alpha', 0.0)  # Start transparent
            
            # Fade in animation
            def fade_in(alpha=0.0):
                if alpha < 1.0:
                    alpha += 0.1
                    self.window.attributes('-alpha', alpha)
                    self.window.after(30, lambda: fade_in(alpha))
            
            fade_in()
            
        except Exception as e:
            print(f"Error animating toast in: {e}")
    
    def animate_out(self):
        """Animate toast sliding out"""
        try:
            # Fade out animation
            def fade_out(alpha=1.0):
                if alpha > 0.0:
                    alpha -= 0.1
                    self.window.attributes('-alpha', alpha)
                    self.window.after(30, lambda: fade_out(alpha))
                else:
                    self.close()
            
            fade_out()
            
        except Exception as e:
            print(f"Error animating toast out: {e}")
            self.close()
    
    def close(self):
        """Close the toast notification"""
        try:
            if self.window:
                self.window.destroy()
                self.window = None
        except Exception as e:
            print(f"Error closing toast: {e}")


class ProgressToast:
    """Progress toast notification"""
    
    def __init__(self, parent, title, message):
        """Initialize progress toast"""
        self.parent = parent
        self.title = title
        self.message = message
        self.window = None
        self.progress_var = None
        self.status_var = None
    
    def show(self):
        """Show progress toast"""
        try:
            # Create window
            self.window = tk.Toplevel(self.parent)
            self.window.withdraw()
            self.window.overrideredirect(True)
            self.window.attributes('-topmost', True)
            
            # Main frame
            main_frame = tk.Frame(
                self.window,
                bg="#34495e",
                relief="solid",
                bd=1
            )
            main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # Title
            title_label = tk.Label(
                main_frame,
                text=self.title,
                bg="#34495e",
                fg="white",
                font=("Segoe UI", 10, "bold")
            )
            title_label.pack(pady=(10, 5))
            
            # Status
            self.status_var = tk.StringVar(value=self.message)
            status_label = tk.Label(
                main_frame,
                textvariable=self.status_var,
                bg="#34495e",
                fg="white",
                font=("Segoe UI", 9)
            )
            status_label.pack(pady=(0, 10))
            
            # Progress bar
            self.progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(
                main_frame,
                variable=self.progress_var,
                mode='indeterminate'
            )
            progress_bar.pack(fill=tk.X, padx=15, pady=(0, 15))
            progress_bar.start()
            
            # Position and show
            self.position_toast()
            self.window.deiconify()
            
        except Exception as e:
            print(f"Error showing progress toast: {e}")
    
    def position_toast(self):
        """Position progress toast"""
        try:
            self.window.update_idletasks()
            
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            toast_width = 300
            toast_height = self.window.winfo_reqheight()
            
            x = (screen_width - toast_width) // 2
            y = (screen_height - toast_height) // 2
            
            self.window.geometry(f"{toast_width}x{toast_height}+{x}+{y}")
            
        except Exception as e:
            print(f"Error positioning progress toast: {e}")
    
    def update_status(self, message: str):
        """Update progress status"""
        try:
            if self.status_var:
                self.status_var.set(message)
        except Exception as e:
            print(f"Error updating progress status: {e}")
    
    def close(self):
        """Close progress toast"""
        try:
            if self.window:
                self.window.destroy()
                self.window = None
        except Exception as e:
            print(f"Error closing progress toast: {e}")