#!/bin/bash

# 1. Fetch latest data (Backend)
echo "Starting Backend Data Fetch..."
cd backend

# Check if venv exists and use its python directly to avoid activation path issues after move
if [ -f "venv/bin/python3" ]; then
    ./venv/bin/python3 fetch_data_v3.py
else
    echo "Virtual environment not found in backend/venv. Trying global python3..."
    python3 fetch_data_v3.py
fi

# Check exit status
if [ $? -ne 0 ]; then
    echo "Data fetch failed!"
    exit 1
fi

cd ..

# 2. Start the Frontend Server
echo "Starting Report Frontend..."
cd frontend
npm run dev
