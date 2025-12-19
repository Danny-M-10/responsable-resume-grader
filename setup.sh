#!/bin/bash

# Recruitment Candidate Ranker - Setup Script
# Installs dependencies and verifies installation

echo "=========================================="
echo "Recruitment Candidate Ranker Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Found Python version: $PYTHON_VERSION"

# Check if version is 3.8 or higher
PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 8 ]; then
    echo "ERROR: Python 3.8 or higher required. Found version $PYTHON_VERSION"
    exit 1
fi

echo "Python version OK"
echo ""

# Install dependencies
echo "Installing dependencies..."
echo "This may take a few minutes..."
echo ""

$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to install dependencies"
    echo "Please try manually: $PYTHON_CMD -m pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Launch Web Interface (Recommended):"
echo "   streamlit run app.py"
echo ""
echo "2. Or use Python API:"
echo "   $PYTHON_CMD example_usage.py"
echo ""
echo "3. Read documentation:"
echo "   - QUICK_START.md for fast setup"
echo "   - USER_MANUAL.md for comprehensive guide"
echo "   - README.md for technical details"
echo ""
echo "=========================================="
