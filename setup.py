"""
Setup script for Camera Privacy Manager
Handles dependency installation and environment setup
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"✗ Python 3.8+ required, but you have Python {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_dependencies():
    """Install required dependencies with proper versions"""
    print("\nInstalling dependencies...")
    
    # First, ensure we have the right NumPy version
    commands = [
        ("pip uninstall -y numpy opencv-python", "Removing conflicting packages"),
        ("pip install \"numpy<2.0.0\"", "Installing compatible NumPy"),
        ("pip install opencv-python==4.10.0.84", "Installing compatible OpenCV"),
        ("pip install Pillow==10.0.1", "Installing Pillow")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True


def verify_installation():
    """Verify that all modules can be imported"""
    print("\nVerifying installation...")
    
    modules_to_test = [
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
        ("tkinter", "tkinter (GUI)"),
        ("sqlite3", "SQLite3"),
        ("smtplib", "SMTP (email)")
    ]
    
    all_good = True
    for module, name in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {name} imported successfully")
        except ImportError as e:
            print(f"✗ {name} import failed: {e}")
            all_good = False
    
    return all_good


def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    directories = [
        "logs",
        "intrusion_media",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")


def main():
    """Main setup function"""
    print("=" * 60)
    print("Camera Privacy Manager - Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n✗ Dependency installation failed!")
        print("\nTry running these commands manually:")
        print("1. pip uninstall -y numpy opencv-python")
        print("2. pip install \"numpy<2.0.0\"")
        print("3. pip install opencv-python==4.10.0.84")
        print("4. pip install Pillow==10.0.1")
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        print("\n✗ Installation verification failed!")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n" + "=" * 60)
    print("✓ Setup completed successfully!")
    print("=" * 60)
    print("\nYou can now run the application:")
    print("python main.py")
    print("\nNote: Administrator privileges are required for full functionality.")


if __name__ == "__main__":
    main()