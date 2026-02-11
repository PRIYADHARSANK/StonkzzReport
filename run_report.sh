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


# 2. Start PDF Generation & Email (This will also handle the frontend server)
echo "Starting PDF Generation and Email Service..."
if [ -f "backend/venv/bin/python3" ]; then
    backend/venv/bin/python3 generate_pdf_report.py
else
    echo "Virtual environment not found. Trying global python3..."
    python3 generate_pdf_report.py
fi

# Check exit status
if [ $? -ne 0 ]; then
    echo "PDF Generation/Email failed!"
    # Optional: Don't exit here if you want to keep the local server running for debugging
fi

# 3. Setup Complete
echo "Process Complete! PDF generated and email sent (if enabled)."

