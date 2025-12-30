#!/bin/bash
# Helper script to restart Streamlit with cache clearing

echo "=================================================="
echo "Restarting Streamlit with cache cleared"
echo "=================================================="
echo ""

# Clear Python cache
echo "1. Clearing Python bytecode cache..."
rm -rf __pycache__
rm -f *.pyc
echo "   ✅ Python cache cleared"
echo ""

# Kill existing Streamlit processes
echo "2. Stopping existing Streamlit processes..."
pkill -f "streamlit run" 2>/dev/null && echo "   ✅ Stopped existing processes" || echo "   (No existing processes found)"
echo ""

# Start Streamlit
echo "3. Starting Streamlit..."
echo ""
echo "=================================================="
echo "Your app will open at: http://localhost:8501"
echo "=================================================="
echo ""

export STREAMLIT_SERVER_HEADLESS=true
streamlit run streamlit_app.py
