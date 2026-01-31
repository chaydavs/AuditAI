#!/bin/bash

# HokieAd - Quick Start Script
# Run both frontend and backend with one command

set -e

echo "======================================"
echo "  HokieAd - VT Academic Optimizer"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "Error: Please run this script from the HokieAd root directory"
    exit 1
fi

# Check for .env file
if [ ! -f "backend/.env" ]; then
    echo ""
    echo "Warning: backend/.env not found!"
    echo "Copy backend/.env.example to backend/.env and add your API keys"
    echo ""
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing root dependencies..."
    npm install
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Check Python dependencies
echo "Checking Python dependencies..."
pip3 install -q -r backend/requirements.txt 2>/dev/null || {
    echo "Installing Python dependencies..."
    pip3 install -r backend/requirements.txt
}

echo ""
echo "Starting servers..."
echo "  - Backend:  http://localhost:8000"
echo "  - Frontend: http://localhost:5173"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Run both servers
npm run dev
