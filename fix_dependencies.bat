@echo off
echo ============================================================
echo Camera Privacy Manager - Dependency Fix
echo ============================================================
echo.
echo This script will fix the NumPy/OpenCV compatibility issue.
echo.
pause

echo Uninstalling conflicting packages...
pip uninstall -y numpy opencv-python

echo.
echo Installing compatible NumPy version...
pip install "numpy<2.0.0"

echo.
echo Installing compatible OpenCV version...
pip install opencv-python==4.10.0.84

echo.
echo Installing Pillow...
pip install Pillow==10.0.1

echo.
echo ============================================================
echo Dependency fix completed!
echo ============================================================
echo.
echo You can now run the application with:
echo python main.py
echo.
pause