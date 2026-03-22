#!/bin/bash
# Quick start script for Universal API Template

set -e

echo "🚀 Universal API Template - Quick Start Guide"
echo ""

# Check Python version
echo "✅ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

# Install dependencies
echo ""
echo "✅ Installing dependencies..."
pip install -q -r requirements.txt
echo "   Dependencies installed"

# Create required directories
echo ""
echo "✅ Creating required directories..."
mkdir -p data auth_data logs
echo "   Directories created: data/, auth_data/, logs/"

# Setup environment
echo ""
echo "✅ Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   Created .env from .env.example"
else
    echo "   .env already exists"
fi

# Verify imports
echo ""
echo "✅ Verifying API imports..."
python3 -c "from app.main import app; print('   ✓ API imports successfully')" || {
    echo "   ✗ Failed to import API"
    exit 1
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Setup complete! Ready to start the API"
echo ""
echo "   Start the API with:"
echo "   $ python run.py"
echo ""
echo "   Or with uvicorn directly:"
echo "   $ uvicorn app.main:app --reload"
echo ""
echo "   Then visit:"
echo "   • API Docs:  http://localhost:8000/docs"
echo "   • ReDoc:     http://localhost:8000/redoc"
echo "   • Health:    http://localhost:8000/health"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
