# Camera Privacy Manager

A comprehensive camera privacy management system that provides secure control over webcam access with authentication, activity logging, and intrusion detection capabilities.

## Features

- Password-protected camera enable/disable with administrative control
- System-wide camera blocking (prevents other applications from accessing camera)
- Detailed access logging with timestamps
- Intrusion detection with automatic video/photo capture
- Email notifications for security events
- Database storage for users and logs
- Pure Python implementation

## Requirements

- Python 3.8+
- Windows OS (for administrative camera control)
- Administrator privileges required

## Installation

### Option 1: Automatic Setup (Recommended)
```bash
python setup.py
```

### Option 2: Manual Installation
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application as Administrator:
```bash
python main.py
```

### Option 3: Windows Batch Fix (if you encounter NumPy/OpenCV errors)
```bash
fix_dependencies.bat
```

## Troubleshooting

### NumPy/OpenCV Compatibility Error
If you see an error about NumPy 2.x compatibility with OpenCV, run:
```bash
pip uninstall -y numpy opencv-python
pip install "numpy<2.0.0"
pip install opencv-python==4.10.0.84
```

Or simply run the provided batch file:
```bash
fix_dependencies.bat
```

## Project Structure

```
camera-privacy-manager/
├── models/           # Data models
├── managers/         # Business logic managers
├── database/         # Database operations
├── gui/             # GUI components
├── tests/           # Unit tests
├── intrusion_media/ # Captured intrusion media
├── config.py        # Configuration settings
└── main.py          # Application entry point
```