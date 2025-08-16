"""
Enhanced Logs window for Camera Privacy Manager
Displays access logs and intrusion attempts with image preview
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import logging
import threading
from pathlib import Path
from PIL import Image, ImageTk
import cv2

from managers.log_manager import LogManager


class LogsWindow:
    """Window for displaying system logs"""
    
    def __init__(self, parent, log_manager: LogManager):
        """Initialize enhanced logs window"""
        self.parent = parent
        self.log_manager = log_manager
        self.logger = logging.getLogger(__name__)
        
        # Image cache for performance
        self.image_cache = {}
        self.thumbnail_size = (100, 75)
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("🔍 System Logs & Intrusion Evidence")
        self.window.geometry("1200x800")
        self.window.transient(parent)
        
        # Center the window
        self.center_window()
        
        # Create widgets
        self.create_widgets()
        
        # Load initial logs asynchronously
        self.refresh_logs_async()
        
        self.logger.info("Enhanced logs window opened")
    
    def center_window(self):
        """Center the window on the screen"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 600
        y = (self.window.winfo_screenheight() // 2) - 400
        self.window.geometry(f"1200x800+{x}+{y}")
    
    def create_widgets(self):
        """Create enhanced GUI widgets with image display"""
        # Configure window grid
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Main paned window for resizable layout
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Left panel for logs
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)
        
        # Right panel for image preview
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # Create left panel (logs)
        self.create_logs_panel(left_frame)
        
        # Create right panel (image preview)
        self.create_image_panel(right_frame)
    
    def create_logs_panel(self, parent):
        """Create the logs display panel"""
        # Title
        title_label = ttk.Label(parent, text="📋 System Activity Logs", font=("Segoe UI", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Filter frame
        filter_frame = ttk.LabelFrame(parent, text="🔍 Filters", padding="5")
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Filter controls
        filter_controls = ttk.Frame(filter_frame)
        filter_controls.pack(fill=tk.X)
        
        # Log type filter
        ttk.Label(filter_controls, text="Type:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.log_type_var = tk.StringVar(value="All")
        log_type_combo = ttk.Combobox(
            filter_controls, 
            textvariable=self.log_type_var,
            values=["All", "Camera Access", "Authentication", "Intrusion Attempts", "System Events"],
            state="readonly",
            width=15
        )
        log_type_combo.grid(row=0, column=1, padx=(0, 10), sticky="w")
        
        # Date range filter
        ttk.Label(filter_controls, text="Period:").grid(row=0, column=2, padx=(0, 5), sticky="w")
        self.date_range_var = tk.StringVar(value="Last 7 days")
        date_range_combo = ttk.Combobox(
            filter_controls,
            textvariable=self.date_range_var,
            values=["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
            state="readonly",
            width=15
        )
        date_range_combo.grid(row=0, column=3, padx=(0, 10), sticky="w")
        
        # Buttons
        refresh_btn = ttk.Button(filter_controls, text="🔄 Refresh", command=self.refresh_logs_async)
        refresh_btn.grid(row=0, column=4, padx=(10, 5))
        
        export_btn = ttk.Button(filter_controls, text="📤 Export", command=self.export_logs)
        export_btn.grid(row=0, column=5, padx=(5, 0))
        
        # Logs display frame
        logs_frame = ttk.LabelFrame(parent, text="📊 Log Entries", padding="5")
        logs_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Configure logs frame grid
        logs_frame.grid_rowconfigure(0, weight=1)
        logs_frame.grid_columnconfigure(0, weight=1)
        
        # Create enhanced treeview for logs
        columns = ("Time", "Type", "User", "Action", "Details", "Evidence")
        self.logs_tree = ttk.Treeview(logs_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.logs_tree.heading("Time", text="🕒 Time")
        self.logs_tree.heading("Type", text="📋 Type")
        self.logs_tree.heading("User", text="👤 User")
        self.logs_tree.heading("Action", text="⚡ Action")
        self.logs_tree.heading("Details", text="📝 Details")
        self.logs_tree.heading("Evidence", text="📷 Evidence")
        
        # Set column widths
        self.logs_tree.column("Time", width=120)
        self.logs_tree.column("Type", width=80)
        self.logs_tree.column("User", width=70)
        self.logs_tree.column("Action", width=120)
        self.logs_tree.column("Details", width=200)
        self.logs_tree.column("Evidence", width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, command=self.logs_tree.yview)
        h_scrollbar = ttk.Scrollbar(logs_frame, orient=tk.HORIZONTAL, command=self.logs_tree.xview)
        self.logs_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.logs_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bind selection event
        self.logs_tree.bind('<<TreeviewSelect>>', self.on_log_select)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(parent, text="📈 Statistics", padding="5")
        stats_frame.pack(fill=tk.X)
        
        self.stats_label = ttk.Label(stats_frame, text="Loading statistics...")
        self.stats_label.pack()
    
    def create_image_panel(self, parent):
        """Create the image preview panel"""
        # Title
        title_label = ttk.Label(parent, text="🖼️ Evidence Preview", font=("Segoe UI", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Image display frame
        image_frame = ttk.LabelFrame(parent, text="📷 Intruder Evidence", padding="10")
        image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Image canvas with scrollbars
        canvas_frame = ttk.Frame(image_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.image_canvas = tk.Canvas(canvas_frame, bg="white", relief="sunken", bd=2)
        img_v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        img_h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.image_canvas.xview)
        
        self.image_canvas.configure(yscrollcommand=img_v_scroll.set, xscrollcommand=img_h_scroll.set)
        
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        img_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        img_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Image info frame
        info_frame = ttk.LabelFrame(parent, text="ℹ️ Evidence Details", padding="5")
        info_frame.pack(fill=tk.X)
        
        self.image_info_label = ttk.Label(info_frame, text="Select an intrusion log to view evidence", 
                                         font=("Segoe UI", 9), foreground="gray")
        self.image_info_label.pack()
        
        # Image controls
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.zoom_in_btn = ttk.Button(controls_frame, text="🔍 Zoom In", command=self.zoom_in, state="disabled")
        self.zoom_in_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.zoom_out_btn = ttk.Button(controls_frame, text="🔍 Zoom Out", command=self.zoom_out, state="disabled")
        self.zoom_out_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.save_btn = ttk.Button(controls_frame, text="💾 Save Image", command=self.save_image, state="disabled")
        self.save_btn.pack(side=tk.RIGHT)
        
        # Initialize image variables
        self.current_image = None
        self.current_image_path = None
        self.zoom_factor = 1.0
    
    def on_log_select(self, event):
        """Handle log selection to show evidence"""
        selection = self.logs_tree.selection()
        if not selection:
            self.clear_image_display()
            return
        
        item = self.logs_tree.item(selection[0])
        values = item['values']
        
        # Check if this is an intrusion log with evidence
        if len(values) >= 6 and values[5] and values[5] not in ["", "❌ Missing"]:
            # For intrusion logs, we need to get the actual file path
            # Since we can't store it directly in the tree, we'll reconstruct it
            if values[1] == 'Intrusion':  # Type column
                # Get intrusion logs and find matching one
                intrusion_logs = self.log_manager.get_intrusion_logs()
                timestamp_str = values[0]  # Time column
                
                # Find matching intrusion log
                for intrusion in intrusion_logs:
                    log_time = intrusion.timestamp.strftime("%m-%d %H:%M")
                    if log_time == timestamp_str:
                        self.load_evidence_async(intrusion.media_path, values)
                        return
            
        self.clear_image_display()
    
    def load_evidence_async(self, evidence_path, log_values):
        """Load evidence image asynchronously"""
        def load_image():
            try:
                if evidence_path and evidence_path != "None":
                    # Update UI to show loading
                    self.image_info_label.config(text="🔄 Loading evidence...")
                    
                    # Load image
                    image_path = Path(evidence_path)
                    if image_path.exists():
                        # Load image based on file type
                        if evidence_path.lower().endswith(('.mp4', '.avi', '.mov')):
                            # Extract frame from video
                            image = self.extract_video_frame(evidence_path)
                        else:
                            # Load image file
                            image = Image.open(evidence_path)
                        
                        if image:
                            # Update UI in main thread
                            self.window.after(0, lambda: self.display_image(image, evidence_path, log_values))
                        else:
                            self.window.after(0, lambda: self.show_image_error("Could not load image"))
                    else:
                        self.window.after(0, lambda: self.show_image_error("Evidence file not found"))
                else:
                    self.window.after(0, self.clear_image_display)
                    
            except Exception as e:
                self.logger.error(f"Error loading evidence: {e}")
                self.window.after(0, lambda: self.show_image_error(f"Error: {e}"))
        
        # Run in background thread
        threading.Thread(target=load_image, daemon=True).start()
    
    def extract_video_frame(self, video_path):
        """Extract first frame from video file"""
        try:
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(frame_rgb)
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting video frame: {e}")
            return None
    
    def display_image(self, image, image_path, log_values):
        """Display image in the canvas"""
        try:
            self.current_image = image
            self.current_image_path = image_path
            self.zoom_factor = 1.0
            
            # Calculate display size
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not ready, try again later
                self.window.after(100, lambda: self.display_image(image, image_path, log_values))
                return
            
            # Resize image to fit canvas while maintaining aspect ratio
            img_width, img_height = image.size
            scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(display_image)
            
            # Clear canvas and display image
            self.image_canvas.delete("all")
            self.image_canvas.create_image(
                canvas_width // 2, canvas_height // 2, 
                image=self.photo, anchor=tk.CENTER
            )
            
            # Update scroll region
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            
            # Update info label
            timestamp = log_values[0] if len(log_values) > 0 else "Unknown"
            file_size = Path(image_path).stat().st_size if Path(image_path).exists() else 0
            info_text = f"📅 {timestamp} | 📏 {img_width}x{img_height} | 💾 {file_size // 1024}KB"
            self.image_info_label.config(text=info_text, foreground="black")
            
            # Enable controls
            self.zoom_in_btn.config(state="normal")
            self.zoom_out_btn.config(state="normal")
            self.save_btn.config(state="normal")
            
        except Exception as e:
            self.logger.error(f"Error displaying image: {e}")
            self.show_image_error(f"Display error: {e}")
    
    def clear_image_display(self):
        """Clear the image display"""
        self.image_canvas.delete("all")
        self.image_info_label.config(text="Select an intrusion log to view evidence", foreground="gray")
        self.zoom_in_btn.config(state="disabled")
        self.zoom_out_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.current_image = None
        self.current_image_path = None
    
    def show_image_error(self, error_msg):
        """Show error message in image panel"""
        self.image_canvas.delete("all")
        self.image_canvas.create_text(
            self.image_canvas.winfo_width() // 2,
            self.image_canvas.winfo_height() // 2,
            text=f"❌ {error_msg}",
            fill="red",
            font=("Segoe UI", 12)
        )
        self.image_info_label.config(text=error_msg, foreground="red")
    
    def zoom_in(self):
        """Zoom in on the image"""
        if self.current_image:
            self.zoom_factor *= 1.2
            self.update_image_zoom()
    
    def zoom_out(self):
        """Zoom out on the image"""
        if self.current_image:
            self.zoom_factor /= 1.2
            self.update_image_zoom()
    
    def update_image_zoom(self):
        """Update image display with current zoom factor"""
        if not self.current_image:
            return
        
        try:
            img_width, img_height = self.current_image.size
            new_width = int(img_width * self.zoom_factor)
            new_height = int(img_height * self.zoom_factor)
            
            display_image = self.current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(display_image)
            
            self.image_canvas.delete("all")
            self.image_canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            
        except Exception as e:
            self.logger.error(f"Error updating zoom: {e}")
    
    def save_image(self):
        """Save the current image"""
        if not self.current_image_path:
            return
        
        try:
            from tkinter import filedialog
            
            # Get save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*")
                ],
                title="Save Evidence Image"
            )
            
            if filename:
                if self.current_image_path.lower().endswith(('.mp4', '.avi', '.mov')):
                    # Save extracted frame
                    self.current_image.save(filename)
                else:
                    # Copy original image
                    import shutil
                    shutil.copy2(self.current_image_path, filename)
                
                messagebox.showinfo("Success", f"Evidence saved to {filename}")
                
        except Exception as e:
            self.logger.error(f"Error saving image: {e}")
            messagebox.showerror("Error", f"Failed to save image: {e}")
        
        # Title
        title_label = ttk.Label(main_frame, text="System Logs", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Filter frame
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="5")
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Log type filter
        ttk.Label(filter_frame, text="Log Type:").grid(row=0, column=0, padx=(0, 5))
        self.log_type_var = tk.StringVar(value="All")
        log_type_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.log_type_var,
            values=["All", "Camera Access", "Authentication", "Intrusion Attempts", "System Events"],
            state="readonly",
            width=15
        )
        log_type_combo.grid(row=0, column=1, padx=(0, 10))
        
        # Date range filter
        ttk.Label(filter_frame, text="Date Range:").grid(row=0, column=2, padx=(0, 5))
        self.date_range_var = tk.StringVar(value="Last 7 days")
        date_range_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.date_range_var,
            values=["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
            state="readonly",
            width=15
        )
        date_range_combo.grid(row=0, column=3, padx=(0, 10))
        
        # Refresh button
        refresh_btn = ttk.Button(filter_frame, text="Refresh", command=self.refresh_logs)
        refresh_btn.grid(row=0, column=4, padx=(10, 0))
        
        # Export button
        export_btn = ttk.Button(filter_frame, text="Export", command=self.export_logs)
        export_btn.grid(row=0, column=5, padx=(5, 0))
        
        # Logs display frame
        logs_frame = ttk.LabelFrame(main_frame, text="Log Entries", padding="5")
        logs_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview for logs
        columns = ("Timestamp", "Type", "User", "Action", "Details")
        self.logs_tree = ttk.Treeview(logs_frame, columns=columns, show="headings", height=20)
        
        # Configure columns
        self.logs_tree.heading("Timestamp", text="Timestamp")
        self.logs_tree.heading("Type", text="Type")
        self.logs_tree.heading("User", text="User")
        self.logs_tree.heading("Action", text="Action")
        self.logs_tree.heading("Details", text="Details")
        
        self.logs_tree.column("Timestamp", width=150)
        self.logs_tree.column("Type", width=100)
        self.logs_tree.column("User", width=80)
        self.logs_tree.column("Action", width=150)
        self.logs_tree.column("Details", width=300)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, command=self.logs_tree.yview)
        h_scrollbar = ttk.Scrollbar(logs_frame, orient=tk.HORIZONTAL, command=self.logs_tree.xview)
        self.logs_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.logs_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        logs_frame.grid_rowconfigure(0, weight=1)
        logs_frame.grid_columnconfigure(0, weight=1)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="5")
        stats_frame.pack(fill=tk.X)
        
        self.stats_label = ttk.Label(stats_frame, text="Loading statistics...")
        self.stats_label.pack()
        
        # Close button
        close_btn = ttk.Button(main_frame, text="Close", command=self.window.destroy)
        close_btn.pack(pady=(10, 0))
    
    def refresh_logs(self):
        """Refresh the logs display"""
        try:
            # Clear existing items
            for item in self.logs_tree.get_children():
                self.logs_tree.delete(item)
            
            # Get filtered logs
            logs = self.get_filtered_logs()
            
            # Populate treeview
            for log in logs:
                self.add_log_to_tree(log)
            
            # Update statistics
            self.update_statistics(logs)
            
            self.logger.info(f"Refreshed logs display with {len(logs)} entries")
            
        except Exception as e:
            self.logger.error(f"Error refreshing logs: {e}")
            messagebox.showerror("Error", f"Failed to refresh logs: {e}")
    
    def get_filtered_logs(self):
        """Get logs based on current filters"""
        try:
            # Get date range
            end_date = datetime.now()
            date_range = self.date_range_var.get()
            
            if date_range == "Last 24 hours":
                start_date = end_date - timedelta(days=1)
            elif date_range == "Last 7 days":
                start_date = end_date - timedelta(days=7)
            elif date_range == "Last 30 days":
                start_date = end_date - timedelta(days=30)
            else:  # All time
                start_date = datetime(2000, 1, 1)  # Very old date
            
            # Get logs by date range
            access_logs = self.log_manager.get_logs_by_date_range(start_date, end_date)
            
            # Filter by log type
            log_type = self.log_type_var.get()
            if log_type != "All":
                filtered_logs = []
                for log in access_logs:
                    if self.matches_log_type(log, log_type):
                        filtered_logs.append(log)
                access_logs = filtered_logs
            
            # Also get intrusion logs if requested
            intrusion_logs = []
            if log_type in ["All", "Intrusion Attempts"]:
                all_intrusions = self.log_manager.get_intrusion_logs()
                intrusion_logs = [
                    intrusion for intrusion in all_intrusions
                    if start_date <= intrusion.timestamp <= end_date
                ]
            
            # Combine and sort logs
            combined_logs = []
            
            # Add access logs
            for log in access_logs:
                combined_logs.append({
                    'timestamp': log.timestamp,
                    'type': self.get_log_type_display(log.action),
                    'user_id': log.user_id,
                    'action': log.action,
                    'details': '',
                    'evidence_path': None
                })
            
            # Add intrusion logs with evidence paths
            for intrusion in intrusion_logs:
                combined_logs.append({
                    'timestamp': intrusion.timestamp,
                    'type': 'Intrusion',
                    'user_id': -1,
                    'action': 'INTRUSION_DETECTED',
                    'details': f"Evidence captured",
                    'evidence_path': intrusion.media_path
                })
            
            # Sort by timestamp (newest first)
            combined_logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return combined_logs
            
        except Exception as e:
            self.logger.error(f"Error getting filtered logs: {e}")
            return []
    
    def matches_log_type(self, log, log_type):
        """Check if log matches the selected log type"""
        action = log.action.upper()
        
        if log_type == "Camera Access":
            return "CAMERA" in action
        elif log_type == "Authentication":
            return "AUTH" in action
        elif log_type == "System Events":
            return "SYSTEM" in action or "SETUP" in action
        
        return True
    
    def get_log_type_display(self, action):
        """Get display-friendly log type from action"""
        action = action.upper()
        
        if "CAMERA" in action:
            return "Camera"
        elif "AUTH" in action:
            return "Auth"
        elif "SYSTEM" in action or "SETUP" in action:
            return "System"
        else:
            return "Other"
    
    def add_log_to_tree(self, log):
        """Add a log entry to the treeview with evidence support"""
        try:
            timestamp_str = log['timestamp'].strftime("%m-%d %H:%M")
            user_str = f"User {log['user_id']}" if log['user_id'] > 0 else "System"
            
            # Determine evidence status
            evidence_status = ""
            if log.get('evidence_path'):
                evidence_path = Path(log['evidence_path'])
                if evidence_path.exists():
                    if evidence_path.suffix.lower() in ['.mp4', '.avi', '.mov']:
                        evidence_status = "🎥 Video"
                    else:
                        evidence_status = "📷 Photo"
                else:
                    evidence_status = "❌ Missing"
            
            # Add color coding for intrusion logs
            item_id = self.logs_tree.insert("", tk.END, values=(
                timestamp_str,
                log['type'],
                user_str,
                log['action'],
                log['details'],
                evidence_status
            ))
            
            # Color code intrusion attempts
            if log['type'] == 'Intrusion':
                self.logs_tree.item(item_id, tags=('intrusion',))
            
            # Store evidence path in item for later retrieval
            if log.get('evidence_path'):
                # Store the evidence path as a hidden value
                current_values = list(self.logs_tree.item(item_id)['values'])
                current_values.append(log['evidence_path'])  # Hidden evidence path
                
        except Exception as e:
            self.logger.error(f"Error adding log to tree: {e}")
    
    def refresh_logs_async(self):
        """Refresh logs asynchronously for better performance"""
        def refresh_in_background():
            try:
                # Show loading state
                self.window.after(0, lambda: self.stats_label.config(text="🔄 Loading logs..."))
                
                # Get logs in background
                logs = self.get_filtered_logs()
                
                # Update UI in main thread
                def update_ui():
                    try:
                        # Clear existing items
                        for item in self.logs_tree.get_children():
                            self.logs_tree.delete(item)
                        
                        # Configure tags for styling
                        self.logs_tree.tag_configure('intrusion', background='#ffebee', foreground='#c62828')
                        
                        # Populate treeview
                        for log in logs:
                            self.add_log_to_tree(log)
                        
                        # Update statistics
                        self.update_statistics(logs)
                        
                        self.logger.info(f"Refreshed logs display with {len(logs)} entries")
                        
                    except Exception as e:
                        self.logger.error(f"Error updating logs UI: {e}")
                        self.stats_label.config(text=f"❌ Error loading logs: {e}")
                
                self.window.after(0, update_ui)
                
            except Exception as e:
                self.logger.error(f"Error refreshing logs: {e}")
                self.window.after(0, lambda: self.stats_label.config(text=f"❌ Error: {e}"))
        
        # Run in background thread
        threading.Thread(target=refresh_in_background, daemon=True).start()
    
    def update_statistics(self, logs):
        """Update the statistics display"""
        try:
            total_logs = len(logs)
            
            # Count by type
            type_counts = {}
            for log in logs:
                log_type = log['type']
                type_counts[log_type] = type_counts.get(log_type, 0) + 1
            
            # Create statistics text
            stats_text = f"Total Entries: {total_logs}"
            
            if type_counts:
                stats_text += " | "
                type_stats = []
                for log_type, count in type_counts.items():
                    type_stats.append(f"{log_type}: {count}")
                stats_text += ", ".join(type_stats)
            
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
            self.stats_label.config(text="Statistics unavailable")
    
    def export_logs(self):
        """Export logs to a file"""
        try:
            from tkinter import filedialog
            import csv
            
            # Get current logs
            logs = self.get_filtered_logs()
            
            if not logs:
                messagebox.showinfo("No Data", "No logs to export")
                return
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Logs"
            )
            
            if not filename:
                return
            
            # Write CSV file
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["Timestamp", "Type", "User", "Action", "Details"])
                
                # Write data
                for log in logs:
                    timestamp_str = log['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                    user_str = f"User {log['user_id']}" if log['user_id'] > 0 else "System"
                    
                    writer.writerow([
                        timestamp_str,
                        log['type'],
                        user_str,
                        log['action'],
                        log['details']
                    ])
            
            messagebox.showinfo("Export Complete", f"Logs exported to {filename}")
            self.logger.info(f"Logs exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            messagebox.showerror("Export Error", f"Failed to export logs: {e}")