#!/bin/bash

# Test script to verify web UI Docker build
echo "Testing web UI Docker build..."

# Check if required files exist
echo "Checking required files..."
if [ ! -f "Dockerfile.web" ]; then
    echo "❌ Dockerfile.web not found"
    exit 1
fi

if [ ! -d "web" ]; then
    echo "❌ web directory not found"
    exit 1
fi

if [ ! -f "nginx.conf" ]; then
    echo "❌ nginx.conf not found"
    exit 1
fi

if [ ! -f "web/index.html" ]; then
    echo "❌ web/index.html not found"
    exit 1
fi

echo "✅ All required files exist"

# Test Docker build (if Docker is available)
if command -v docker &> /dev/null; then
    echo "Testing Docker build..."
    docker build -f Dockerfile.web -t sip-ai-agent-web:test .
    if [ $? -eq 0 ]; then
        echo "✅ Docker build successful"
        docker rmi sip-ai-agent-web:test  # Clean up
    else
        echo "❌ Docker build failed"
        exit 1
    fi
else
    echo "⚠️ Docker not available, skipping build test"
fi

echo "✅ Web UI build test completed successfully"
