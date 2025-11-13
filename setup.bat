@echo off
REM Auto Job Application Bot Setup Script (Windows)
REM This script helps you set up the bot quickly on Windows

echo ==================================================
echo Auto Job Application Bot - Setup Script (Windows)
echo ==================================================
echo.

REM Check Python
echo 1. Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo    X Python not found! Please install Python 3.8 or higher
    echo    Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo    √ Python is installed

REM Install dependencies
echo.
echo 2. Installing dependencies...
echo    This may take a few minutes...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo    X Failed to install dependencies
    pause
    exit /b 1
)
echo    √ Python packages installed

REM Install Playwright browsers
echo.
echo 3. Installing browser automation tools...
python -m playwright install chromium
if errorlevel 1 (
    echo    X Failed to install Playwright browsers
    pause
    exit /b 1
)
echo    √ Playwright browsers installed

REM Create profile.json if it doesn't exist
echo.
echo 4. Checking configuration...
if not exist profile.json (
    echo    Creating profile.json from template...
    copy profile.json.example profile.json >nul
    echo    √ profile.json created
    echo.
    echo    ⚠ IMPORTANT: Edit profile.json with your information!
    echo    Required fields:
    echo      - first_name
    echo      - last_name
    echo      - email
    echo      - master_resume_path (use absolute path like C:\path\to\resume.pdf^)
) else (
    echo    √ profile.json already exists
)

REM Create necessary directories
echo.
echo 5. Creating directories...
if not exist tailored_resumes mkdir tailored_resumes
if not exist tailored_resumes\cover_letters mkdir tailored_resumes\cover_letters
if not exist logs mkdir logs
echo    √ Directories created

REM Run test
echo.
echo 6. Running functionality test...
python test_bot_functionality.py

REM Final instructions
echo.
echo ==================================================
echo Setup Complete!
echo ==================================================
echo.
echo Next steps:
echo.
echo 1. Edit your profile:
echo    notepad profile.json
echo.
echo 2. Run a test:
echo    python auto_apply.py --title "Software Engineer" --limit 1 --dry-run
echo.
echo 3. Check the results:
echo    type bot_run.log
echo    dir tailored_resumes
echo.
echo 4. Read the guides:
echo    - QUICKSTART.md (5-minute guide^)
echo    - SETUP_GUIDE.md (detailed documentation^)
echo    - README.md (overview and features^)
echo.
echo Happy job hunting! 🚀
echo ==================================================
pause
