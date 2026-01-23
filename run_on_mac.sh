#!/bin/bash
echo "🚗 Setting up AxelGuard Pothole System on Mac..."

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew (Required for Python/System tools)..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    brew install python
fi

# Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and Install
echo "Installing Dependencies (this may take a few minutes)..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run App
echo "Starting AxelGuard..."
streamlit run app.py
