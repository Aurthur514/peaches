#!/bin/bash
# Auto Job Application Bot Setup Script
# This script helps you set up the bot quickly

set -e  # Exit on error

echo "=================================================="
echo "Auto Job Application Bot - Setup Script"
echo "=================================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found: Python $python_version"

# Check if Python is 3.8 or higher
required_version="3.8"
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "   ✓ Python version is compatible"
else
    echo "   ✗ Python 3.8 or higher required"
    exit 1
fi

# Install dependencies
echo ""
echo "2. Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt -q
echo "   ✓ Python packages installed"

# Install Playwright browsers
echo ""
echo "3. Installing browser automation tools..."
python3 -m playwright install chromium
echo "   ✓ Playwright browsers installed"

# Create profile.json if it doesn't exist
echo ""
echo "4. Checking configuration..."
if [ ! -f "profile.json" ]; then
    echo "   Creating profile.json from template..."
    cp profile.json.example profile.json
    echo "   ✓ profile.json created"
    echo ""
    echo "   ⚠ IMPORTANT: Edit profile.json with your information!"
    echo "   Required fields:"
    echo "     - first_name"
    echo "     - last_name"
    echo "     - email"
    echo "     - master_resume_path (use absolute path)"
else
    echo "   ✓ profile.json already exists"
fi

# Create necessary directories
echo ""
echo "5. Creating directories..."
mkdir -p tailored_resumes
mkdir -p tailored_resumes/cover_letters
mkdir -p logs
echo "   ✓ Directories created"

# Run test
echo ""
echo "6. Running functionality test..."
python3 test_bot_functionality.py

# Final instructions
echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit your profile:"
echo "   nano profile.json"
echo "   (or use your favorite editor)"
echo ""
echo "2. Run a test:"
echo "   python auto_apply.py --title 'Software Engineer' --limit 1 --dry-run"
echo ""
echo "3. Check the results:"
echo "   cat bot_run.log"
echo "   ls tailored_resumes/"
echo ""
echo "4. Read the guides:"
echo "   - QUICKSTART.md (5-minute guide)"
echo "   - SETUP_GUIDE.md (detailed documentation)"
echo "   - README.md (overview and features)"
echo ""
echo "Happy job hunting! 🚀"
echo "=================================================="
