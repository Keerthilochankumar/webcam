"""
Quick fix for NumPy/OpenCV compatibility issue
"""
import subprocess
import sys

def run_pip_command(command):
    """Run pip command and show output"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✓ Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def main():
    print("Fixing NumPy/OpenCV compatibility...")
    
    commands = [
        "pip uninstall -y numpy opencv-python",
        "pip install numpy==1.24.3",
        "pip install opencv-python==4.10.0.84",
        "pip install Pillow==10.0.1"
    ]
    
    for cmd in commands:
        print(f"\n{'-'*50}")
        if not run_pip_command(cmd):
            print("Command failed, but continuing...")
    
    print(f"\n{'='*50}")
    print("Fix completed! Try running 'python main.py' now.")

if __name__ == "__main__":
    main()