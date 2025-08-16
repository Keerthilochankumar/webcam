"""
Main entry point for Camera Privacy Manager
Handles application startup, GUI initialization, and error handling
"""
import sys
import os
import logging
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app_config import initialize_application
    from gui.main_window import MainWindow
    from config import APP_NAME, APP_VERSION, REQUIRE_ADMIN
except ImportError as e:
    print(f"Critical import error: {e}")
    print("Please ensure all required dependencies are installed.")
    sys.exit(1)


def check_admin_privileges():
    """Check if running with administrator privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def request_admin_privileges():
    """Request administrator privileges by restarting the application"""
    try:
        import ctypes
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
        print(f"Failed to request administrator privileges: {e}")
        return False


def show_error_dialog(title, message, details=None):
    """Show error dialog to user"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        # Create a temporary root window (hidden)
        root = tk.Tk()
        root.withdraw()
        
        # Show error message
        if details:
            full_message = f"{message}\n\nDetails:\n{details}"
        else:
            full_message = message
        
        messagebox.showerror(title, full_message)
        root.destroy()
        
    except Exception:
        # Fallback to console output
        print(f"ERROR: {title}")
        print(f"Message: {message}")
        if details:
            print(f"Details: {details}")


def show_admin_warning():
    """Show warning about administrator privileges"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        
        message = (
            f"{APP_NAME} requires administrator privileges to control camera access at the system level.\n\n"
            "Without admin privileges, the camera blocking feature will not work properly.\n\n"
            "Would you like to restart the application as administrator?"
        )
        
        result = messagebox.askyesno("Administrator Privileges Required", message)
        root.destroy()
        
        return result
        
    except Exception:
        print("Administrator privileges are required for full functionality.")
        return False


def handle_critical_error(error_type, error_message, error_details=None):
    """Handle critical errors that prevent application startup"""
    logger = logging.getLogger(__name__)
    
    # Log the error
    logger.critical(f"{error_type}: {error_message}")
    if error_details:
        logger.critical(f"Details: {error_details}")
    
    # Show error to user
    show_error_dialog(
        f"{APP_NAME} - Critical Error",
        f"A critical error occurred that prevents the application from starting:\n\n{error_message}",
        error_details
    )
    
    sys.exit(1)


def main():
    """Main application entry point"""
    logger = None
    app_config = None
    main_window = None
    
    try:
        print(f"Starting {APP_NAME} v{APP_VERSION}...")
        
        # Initialize application configuration
        app_config, init_errors = initialize_application()
        
        if not app_config:
            handle_critical_error(
                "Initialization Error",
                "Failed to initialize application configuration.",
                "\n".join(init_errors) if init_errors else None
            )
        
        logger = logging.getLogger(__name__)
        logger.info(f"{APP_NAME} v{APP_VERSION} starting...")
        
        # Check administrator privileges if required
        if REQUIRE_ADMIN and not check_admin_privileges():
            logger.warning("Administrator privileges not detected")
            
            if show_admin_warning():
                logger.info("Requesting administrator privileges...")
                if request_admin_privileges():
                    logger.info("Restarting with administrator privileges...")
                    sys.exit(0)
                else:
                    handle_critical_error(
                        "Privilege Error",
                        "Failed to obtain administrator privileges.",
                        "Administrator privileges are required for system-wide camera control."
                    )
            else:
                logger.warning("User chose to continue without administrator privileges")
                print("Warning: Running without administrator privileges. Camera blocking may not work properly.")
        
        # Check system requirements
        requirements_met, requirement_issues = app_config.check_system_requirements()
        if not requirements_met:
            handle_critical_error(
                "System Requirements",
                "System requirements are not met.",
                "\n".join(requirement_issues)
            )
        
        logger.info("System requirements check passed")
        
        # Initialize and run GUI
        logger.info("Initializing GUI...")
        main_window = MainWindow()
        
        logger.info("Starting GUI main loop...")
        main_window.run()
        
        logger.info("Application shutdown completed normally")
        
    except KeyboardInterrupt:
        if logger:
            logger.info("Application interrupted by user (Ctrl+C)")
        else:
            print("Application interrupted by user")
        sys.exit(0)
        
    except ImportError as e:
        error_msg = f"Missing required dependency: {e}"
        if logger:
            logger.critical(error_msg)
        handle_critical_error(
            "Import Error",
            error_msg,
            "Please install all required dependencies using: pip install -r requirements.txt"
        )
        
    except PermissionError as e:
        error_msg = f"Permission denied: {e}"
        if logger:
            logger.critical(error_msg)
        handle_critical_error(
            "Permission Error",
            error_msg,
            "Please ensure the application has necessary file system permissions."
        )
        
    except FileNotFoundError as e:
        error_msg = f"Required file not found: {e}"
        if logger:
            logger.critical(error_msg)
        handle_critical_error(
            "File Not Found",
            error_msg,
            "Please ensure all application files are present and accessible."
        )
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        error_details = traceback.format_exc()
        
        if logger:
            logger.critical(error_msg)
            logger.critical(f"Traceback:\n{error_details}")
        
        handle_critical_error(
            "Unexpected Error",
            error_msg,
            error_details
        )
        
    finally:
        # Cleanup
        try:
            if main_window:
                main_window.cleanup()
            if app_config:
                # Save any final configuration changes
                app_config.save_configuration()
            if logger:
                logger.info("Cleanup completed")
        except Exception as e:
            if logger:
                logger.error(f"Error during cleanup: {e}")
            else:
                print(f"Error during cleanup: {e}")


def run_tests():
    """Run application tests"""
    try:
        import unittest
        
        # Discover and run tests
        loader = unittest.TestLoader()
        start_dir = project_root / "tests"
        suite = loader.discover(str(start_dir), pattern='test_*.py')
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Return appropriate exit code
        sys.exit(0 if result.wasSuccessful() else 1)
        
    except ImportError:
        print("unittest module not available")
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)


def show_help():
    """Show command line help"""
    help_text = f"""
{APP_NAME} v{APP_VERSION}

A comprehensive camera privacy management system that provides secure control 
over webcam access with authentication, activity logging, and intrusion detection.

Usage:
    python main.py [options]

Options:
    --help, -h          Show this help message
    --version, -v       Show version information
    --test              Run application tests
    --no-admin          Skip administrator privilege check (not recommended)
    --config-file FILE  Use custom configuration file
    --debug             Enable debug logging

Examples:
    python main.py                  # Start the application normally
    python main.py --test           # Run tests
    python main.py --debug          # Start with debug logging
    python main.py --no-admin       # Skip admin check (not recommended)

Requirements:
    - Python 3.8 or higher
    - Windows operating system
    - Administrator privileges (recommended)
    - OpenCV (cv2) for camera operations
    - tkinter for GUI (usually included with Python)

For more information, visit the project documentation.
    """.strip()
    
    print(help_text)


def show_version():
    """Show version information"""
    version_info = f"""
{APP_NAME} v{APP_VERSION}

Python: {sys.version}
Platform: {sys.platform}
Architecture: {os.name}

Build Information:
- Configuration: Release
- Features: Camera Control, Intrusion Detection, Email Alerts
- Database: SQLite3
- GUI Framework: tkinter
    """.strip()
    
    print(version_info)


if __name__ == "__main__":
    # Parse command line arguments
    args = sys.argv[1:]
    
    # Handle command line options
    if "--help" in args or "-h" in args:
        show_help()
        sys.exit(0)
    elif "--version" in args or "-v" in args:
        show_version()
        sys.exit(0)
    elif "--test" in args:
        run_tests()
    else:
        # Handle other options
        if "--no-admin" in args:
            # Temporarily disable admin requirement
            import config
            config.REQUIRE_ADMIN = False
        
        if "--debug" in args:
            # Enable debug logging
            logging.getLogger().setLevel(logging.DEBUG)
        
        if "--config-file" in args:
            try:
                config_index = args.index("--config-file")
                if config_index + 1 < len(args):
                    config_file = args[config_index + 1]
                    # This would be handled by app_config if implemented
                    print(f"Using config file: {config_file}")
                else:
                    print("Error: --config-file requires a filename")
                    sys.exit(1)
            except ValueError:
                pass
        
        # Start the main application
        main()