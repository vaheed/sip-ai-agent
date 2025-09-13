# Changelog

All notable changes to this project will be documented in this file.  Dates
are given in UTC.

## [3.0.0] – 2025‑09‑14

### 🚀 Major Features Added

* **Modern Web Dashboard** - Complete FastAPI backend with React frontend
  * Real-time monitoring with WebSocket connections
  * Comprehensive call history with CSV export
  * Web-based configuration editor with live reload
  * Session-based authentication with secure defaults
  * Dark/light theme support with responsive design

* **Enterprise Call Analytics** - Advanced call tracking and reporting
  * Complete call history with audio quality metrics
  * Token usage and cost tracking per call
  * Performance analytics and success rate monitoring
  * CSV export functionality for data analysis
  * Persistent storage with automatic cleanup

* **Production-Ready Deployment** - Docker containerization and CI/CD
  * Multi-platform Docker builds (linux/amd64, linux/arm64)
  * Automated versioning with semantic versioning
  * GitHub Actions workflows for Docker and UI/UX quality
  * Security scanning with Trivy vulnerability scanner
  * Health checks and graceful shutdown handling

* **UI/UX Quality System** - Enterprise-grade frontend quality assurance
  * ESLint and Stylelint with design token validation
  * Accessibility testing with axe-core and pa11y
  * Visual regression testing with Playwright
  * Performance testing with Lighthouse CI
  * Component testing with Storybook

### 🔧 Enhanced Features

* **Configuration Management** - Improved configuration handling
  * Pydantic-based configuration validation
  * Web-based configuration editor with form validation
  * Environment variable management with live reload
  * Configuration backup and restore capabilities

* **Monitoring & Observability** - Comprehensive system monitoring
  * Structured JSON logging with correlation IDs
  * Prometheus metrics for all system components
  * Health checks for container orchestration
  * Real-time system status updates via WebSocket
  * Performance metrics and resource usage tracking

* **Developer Experience** - Enhanced development workflow
  * Comprehensive Makefile with 30+ targets
  * Pre-commit hooks for code quality
  * Automated testing with coverage reporting
  * Security scanning and vulnerability detection
  * Version management and release automation

### 🐳 Infrastructure Improvements

* **Docker Architecture** - Multi-container deployment
  * Separate containers for SIP agent and web dashboard
  * Production-ready Docker Compose configurations
  * Health checks and restart policies
  * Resource limits and monitoring

* **CI/CD Pipelines** - Automated testing and deployment
  * GitHub Actions workflows for Python and frontend
  * Automated Docker image building and publishing
  * Quality gates for code style, security, and performance
  * Branch-based deployment strategies

### 🔒 Security Enhancements

* **Authentication System** - Secure web interface
  * Session-based authentication with HTTP-only cookies
  * CSRF protection with SameSite cookies
  * Secure password hashing and validation
  * Protected routes and API endpoints

* **Security Scanning** - Automated security validation
  * Bandit security scanning for Python code
  * Trivy vulnerability scanning for Docker images
  * Safety dependency scanning
  * Pre-commit security hooks

### 📚 Documentation & Quality

* **Comprehensive Documentation** - Complete project documentation
  * Updated README with all new features
  * Deployment guides and troubleshooting
  * API documentation and integration examples
  * Contributing guidelines and development setup

* **Code Quality** - Enterprise-grade code standards
  * Black formatting and isort import sorting
  * MyPy type checking and flake8 linting
  * Comprehensive test coverage with pytest
  * Pre-commit hooks for consistent code quality

## [2.1.0] – 2025‑08‑31

### Added

* **Configuration dashboard.**  The monitoring UI now includes a `/dashboard`
  endpoint with a configuration editor, call history table and live logs.  You
  can update your `.env` values from the browser and restart the container to
  apply them.
* **Call history.**  Active calls are tracked along with start and end times,
  and displayed with duration in the dashboard.
* **Editable environment.**  The dashboard writes changes back to the `.env`
  file so you no longer need to manually edit it.
* **Improved documentation.**  Added step‑by‑step integration guides for
  FreePBX and VICIdial, clarified realtime API usage and elaborated on
  dashboard functionality.  Added this `CHANGELOG.md` and a
  `CONTRIBUTING.md` with contribution guidelines.

### Changed

* **Monitor code refactoring.**  Factored out `load_config` and `save_config`
  helpers to read and persist the `.env` file.  Added imports for
  `request` and improved error handling.
* **Project structure.**  The project is now packaged as a complete Git
  repository with top‑level README, CONTRIBUTING and CHANGELOG files.

## [2.0.0] – 2024

### Added

* **Realtime API support.**  Added `OPENAI_MODE` environment variable to
  switch between the legacy `/v1/audio/speech` API and OpenAI’s new
  realtime API.  The realtime API streams audio in both directions and
  eliminates the latency associated with converting speech to text and back
  again【878443186554662†L53-L66】.  Support for new voices like Cedar and Marin
  was added【214777425731610†L286-L314】.
* **Asynchronous audio handling.**  Refactored the agent to use
  `asyncio` for WebSocket and audio streaming, improving performance.
* **Monitoring server.**  Added a simple Flask monitor to display SIP
  registration state, active calls, token usage and logs.

## [1.x] – 2023

Initial releases of the SIP AI agent with support for the legacy speech API,
Dockerisation and basic logging.

---

For older history and details, see the commit log.