#!/bin/bash

# AI Service Startup Script
echo "🚀 Starting AI-Powered Tourist Recommendation Service..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=True
export PORT=5000
export HOST=0.0.0.0

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
FLASK_DEBUG=True
PORT=5000
HOST=0.0.0.0
SECRET_KEY=dev-secret-key-change-in-production
EOF
fi

echo "✅ Environment setup complete!"
echo "🌟 Starting AI Service on http://localhost:5000"
echo "📊 Health check available at: http://localhost:5000/health"
echo "🤖 Chat API available at: http://localhost:5000/chat"
echo "🎯 Recommendations API available at: http://localhost:5000/recommendations"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Start the Flask application
python app.py
