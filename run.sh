#!/bin/bash

echo "Satellite Telemetry Dashboard"
echo "============================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "Starting Ground Station Dashboard..."
echo
echo "Open your browser to: http://localhost:5501"
echo "Press Ctrl+C to stop the server"
echo

python3 app.py
