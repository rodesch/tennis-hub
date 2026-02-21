#!/bin/bash
# Tennis Hub - Dev startup

echo "🎾 Tennis Hub - Starting server..."
echo ""

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "🚀 Starting FastAPI on port 5004"
echo "   http://localhost:5004"
echo ""
echo "   Press Ctrl+C to stop"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 5004 --reload
