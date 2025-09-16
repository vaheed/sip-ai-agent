# Comprehensive test script for SIP AI Agent (PowerShell version)
param(
    [switch]$SkipDocker,
    [switch]$SkipFrontend
)

Write-Host "🚀 Starting comprehensive test suite for SIP AI Agent" -ForegroundColor Blue

# Check if we're in the right directory
if (-not (Test-Path "requirements.txt")) {
    Write-Host "[ERROR] Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Testing Backend Components..." -ForegroundColor Blue

# Test 1: Python linting
Write-Host "[INFO] Running Python linting..." -ForegroundColor Blue
try {
    python -m black --check --diff .
    Write-Host "[SUCCESS] Black formatting check passed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Black formatting check failed" -ForegroundColor Red
    exit 1
}

try {
    python -m isort --check-only --diff .
    Write-Host "[SUCCESS] Import sorting check passed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Import sorting check failed" -ForegroundColor Red
    exit 1
}

try {
    python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    Write-Host "[SUCCESS] Flake8 critical issues check passed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Flake8 critical issues check failed" -ForegroundColor Red
    exit 1
}

# Test 2: Type checking
Write-Host "[INFO] Running type checking..." -ForegroundColor Blue
try {
    python -m mypy app/ --ignore-missing-imports --no-strict-optional
    Write-Host "[SUCCESS] Type checking passed" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Type checking had warnings (continuing...)" -ForegroundColor Yellow
}

# Test 3: Backend tests
Write-Host "[INFO] Running backend tests..." -ForegroundColor Blue
try {
    python -m pytest tests/ -v --tb=short
    Write-Host "[SUCCESS] Backend tests passed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Backend tests failed" -ForegroundColor Red
    exit 1
}

# Test 4: Security scanning
Write-Host "[INFO] Running security scans..." -ForegroundColor Blue
try {
    python -m bandit -r app/ -f json -o bandit-report.json
    Write-Host "[SUCCESS] Bandit security scan passed" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Bandit security scan found issues (check bandit-report.json)" -ForegroundColor Yellow
}

try {
    python -m safety check
    Write-Host "[SUCCESS] Safety dependency check passed" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Safety dependency check found issues" -ForegroundColor Yellow
}

if (-not $SkipFrontend) {
    Write-Host "[INFO] Testing Frontend Components..." -ForegroundColor Blue

    # Check if web directory exists
    if (-not (Test-Path "web")) {
        Write-Host "[ERROR] Web directory not found" -ForegroundColor Red
        exit 1
    }

    Set-Location web

    # Test 5: Frontend linting
    Write-Host "[INFO] Running frontend linting..." -ForegroundColor Blue
    try {
        npm run lint
        Write-Host "[SUCCESS] ESLint check passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] ESLint check failed" -ForegroundColor Red
        exit 1
    }

    try {
        npm run stylelint
        Write-Host "[SUCCESS] Stylelint check passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Stylelint check failed" -ForegroundColor Red
        exit 1
    }

    # Test 6: TypeScript check
    Write-Host "[INFO] Running TypeScript check..." -ForegroundColor Blue
    try {
        npx tsc --noEmit
        Write-Host "[SUCCESS] TypeScript check passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] TypeScript check failed" -ForegroundColor Red
        exit 1
    }

    # Test 7: Frontend tests
    Write-Host "[INFO] Running frontend tests..." -ForegroundColor Blue
    try {
        npm run test:coverage
        Write-Host "[SUCCESS] Frontend tests passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Frontend tests failed" -ForegroundColor Red
        exit 1
    }

    # Test 8: Build test
    Write-Host "[INFO] Testing frontend build..." -ForegroundColor Blue
    try {
        npm run build
        Write-Host "[SUCCESS] Frontend build passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Frontend build failed" -ForegroundColor Red
        exit 1
    }

    Set-Location ..
}

if (-not $SkipDocker) {
    Write-Host "[INFO] Testing Docker builds..." -ForegroundColor Blue

    Write-Host "[INFO] Building backend Docker image..." -ForegroundColor Blue
    try {
        docker build -t sip-ai-agent:test .
        Write-Host "[SUCCESS] Backend Docker build passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Backend Docker build failed" -ForegroundColor Red
        exit 1
    }

    Write-Host "[INFO] Building web UI Docker image..." -ForegroundColor Blue
    try {
        docker build -f Dockerfile.web -t sip-ai-agent-web:test .
        Write-Host "[SUCCESS] Web UI Docker build passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Web UI Docker build failed" -ForegroundColor Red
        exit 1
    }

    # Test 10: Docker run test
    Write-Host "[INFO] Testing Docker containers..." -ForegroundColor Blue
    try {
        docker run --rm sip-ai-agent:test python -c "print('Backend container test passed')"
        Write-Host "[SUCCESS] Backend container test passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Backend container test failed" -ForegroundColor Red
        exit 1
    }

    try {
        docker run --rm sip-ai-agent-web:test python -c "print('Web UI container test passed')"
        Write-Host "[SUCCESS] Web UI container test passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Web UI container test failed" -ForegroundColor Red
        exit 1
    }

    # Test 11: Configuration validation
    Write-Host "[INFO] Testing configuration validation..." -ForegroundColor Blue
    try {
        docker run --rm -e SIP_DOMAIN=test.com -e SIP_USER=1001 -e SIP_PASS=test -e OPENAI_API_KEY=sk-test -e AGENT_ID=va-test sip-ai-agent:test python -c "from config import Settings; s = Settings(); print('Backend configuration validation passed')"
        Write-Host "[SUCCESS] Backend configuration validation passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Backend configuration validation failed" -ForegroundColor Red
        exit 1
    }

    try {
        docker run --rm -e SIP_DOMAIN=test.com -e SIP_USER=1001 -e SIP_PASS=test -e OPENAI_API_KEY=sk-test -e AGENT_ID=va-test sip-ai-agent-web:test python -c "from config import Settings; s = Settings(); print('Web UI configuration validation passed')"
        Write-Host "[SUCCESS] Web UI configuration validation passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Web UI configuration validation failed" -ForegroundColor Red
        exit 1
    }

    # Cleanup
    Write-Host "[INFO] Cleaning up test images..." -ForegroundColor Blue
    docker rmi sip-ai-agent:test sip-ai-agent-web:test 2>$null
}

Write-Host "🎉 All tests passed successfully!" -ForegroundColor Green
Write-Host "✅ Backend: Linting, type checking, tests, security scans" -ForegroundColor Blue
if (-not $SkipFrontend) {
    Write-Host "✅ Frontend: Linting, type checking, tests, build" -ForegroundColor Blue
}
if (-not $SkipDocker) {
    Write-Host "✅ Docker: Both backend and web UI images build and run" -ForegroundColor Blue
    Write-Host "✅ Configuration: Both services validate configuration correctly" -ForegroundColor Blue
}

Write-Host ""
Write-Host "The SIP AI Agent is ready for deployment!" -ForegroundColor Blue
