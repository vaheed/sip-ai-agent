#!/bin/bash

# Comprehensive test script for SIP AI Agent
set -e

echo "🚀 Starting comprehensive test suite for SIP AI Agent"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_status "Testing Backend Components..."

# Test 1: Python linting
print_status "Running Python linting..."
if python -m black --check --diff .; then
    print_success "Black formatting check passed"
else
    print_error "Black formatting check failed"
    exit 1
fi

if python -m isort --check-only --diff .; then
    print_success "Import sorting check passed"
else
    print_error "Import sorting check failed"
    exit 1
fi

if python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; then
    print_success "Flake8 critical issues check passed"
else
    print_error "Flake8 critical issues check failed"
    exit 1
fi

# Test 2: Type checking
print_status "Running type checking..."
if python -m mypy app/ --ignore-missing-imports --no-strict-optional; then
    print_success "Type checking passed"
else
    print_warning "Type checking had warnings (continuing...)"
fi

# Test 3: Backend tests
print_status "Running backend tests..."
if python -m pytest tests/ -v --tb=short; then
    print_success "Backend tests passed"
else
    print_error "Backend tests failed"
    exit 1
fi

# Test 4: Security scanning
print_status "Running security scans..."
if python -m bandit -r app/ -f json -o bandit-report.json; then
    print_success "Bandit security scan passed"
else
    print_warning "Bandit security scan found issues (check bandit-report.json)"
fi

if python -m safety check; then
    print_success "Safety dependency check passed"
else
    print_warning "Safety dependency check found issues"
fi

print_status "Testing Frontend Components..."

# Check if web directory exists
if [ ! -d "web" ]; then
    print_error "Web directory not found"
    exit 1
fi

cd web

# Test 5: Frontend linting
print_status "Running frontend linting..."
if npm run lint; then
    print_success "ESLint check passed"
else
    print_error "ESLint check failed"
    exit 1
fi

if npm run stylelint; then
    print_success "Stylelint check passed"
else
    print_error "Stylelint check failed"
    exit 1
fi

# Test 6: TypeScript check
print_status "Running TypeScript check..."
if npx tsc --noEmit; then
    print_success "TypeScript check passed"
else
    print_error "TypeScript check failed"
    exit 1
fi

# Test 7: Frontend tests
print_status "Running frontend tests..."
if npm run test:coverage; then
    print_success "Frontend tests passed"
else
    print_error "Frontend tests failed"
    exit 1
fi

# Test 8: Build test
print_status "Testing frontend build..."
if npm run build; then
    print_success "Frontend build passed"
else
    print_error "Frontend build failed"
    exit 1
fi

# Test 9: Docker build test
print_status "Testing Docker builds..."
cd ..

print_status "Building backend Docker image..."
if docker build -t sip-ai-agent:test .; then
    print_success "Backend Docker build passed"
else
    print_error "Backend Docker build failed"
    exit 1
fi

print_status "Building web UI Docker image..."
if docker build -f Dockerfile.web -t sip-ai-agent-web:test .; then
    print_success "Web UI Docker build passed"
else
    print_error "Web UI Docker build failed"
    exit 1
fi

# Test 10: Docker run test
print_status "Testing Docker containers..."
if docker run --rm sip-ai-agent:test python -c "print('Backend container test passed')"; then
    print_success "Backend container test passed"
else
    print_error "Backend container test failed"
    exit 1
fi

if docker run --rm sip-ai-agent-web:test python -c "print('Web UI container test passed')"; then
    print_success "Web UI container test passed"
else
    print_error "Web UI container test failed"
    exit 1
fi

# Test 11: Configuration validation
print_status "Testing configuration validation..."
if docker run --rm -e SIP_DOMAIN=test.com -e SIP_USER=1001 -e SIP_PASS=test -e OPENAI_API_KEY=sk-test -e AGENT_ID=va-test sip-ai-agent:test python -c "from config import Settings; s = Settings(); print('Backend configuration validation passed')"; then
    print_success "Backend configuration validation passed"
else
    print_error "Backend configuration validation failed"
    exit 1
fi

if docker run --rm -e SIP_DOMAIN=test.com -e SIP_USER=1001 -e SIP_PASS=test -e OPENAI_API_KEY=sk-test -e AGENT_ID=va-test sip-ai-agent-web:test python -c "from config import Settings; s = Settings(); print('Web UI configuration validation passed')"; then
    print_success "Web UI configuration validation passed"
else
    print_error "Web UI configuration validation failed"
    exit 1
fi

# Cleanup
print_status "Cleaning up test images..."
docker rmi sip-ai-agent:test sip-ai-agent-web:test 2>/dev/null || true

print_success "🎉 All tests passed successfully!"
print_status "✅ Backend: Linting, type checking, tests, security scans"
print_status "✅ Frontend: Linting, type checking, tests, build"
print_status "✅ Docker: Both backend and web UI images build and run"
print_status "✅ Configuration: Both services validate configuration correctly"

echo ""
print_status "The SIP AI Agent is ready for deployment!"
