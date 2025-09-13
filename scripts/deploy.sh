#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="ghcr.io"
REPO_NAME="${GITHUB_REPOSITORY:-sip-ai-agent}"
VERSION="${VERSION:-latest}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        log_error ".env file not found"
        exit 1
    fi
    
    log_success "All requirements met"
}

pull_images() {
    log_info "Pulling Docker images..."
    
    # Pull SIP Agent image
    docker pull "${REGISTRY}/${REPO_NAME}:${VERSION}" || {
        log_error "Failed to pull SIP Agent image"
        exit 1
    }
    
    # Pull Web UI image
    docker pull "${REGISTRY}/${REPO_NAME}-web:${VERSION}" || {
        log_error "Failed to pull Web UI image"
        exit 1
    }
    
    log_success "Images pulled successfully"
}

deploy_services() {
    log_info "Deploying services..."
    
    # Stop existing services
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down || true
    
    # Start services
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    log_success "Services deployed successfully"
}

wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8080/healthz &> /dev/null; then
            log_success "SIP Agent is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "SIP Agent failed to become healthy"
            exit 1
        fi
        
        log_info "Waiting for SIP Agent... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    # Check Web UI if it's running on a different port
    if curl -f http://localhost:8081/healthz &> /dev/null; then
        log_success "Web UI is healthy"
    else
        log_warning "Web UI health check failed (may not be running)"
    fi
}

show_status() {
    log_info "Deployment Status:"
    echo ""
    echo "🐳 Docker Images:"
    docker images | grep "${REPO_NAME}" || echo "No images found"
    echo ""
    echo "📊 Running Containers:"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
    echo ""
    echo "🌐 Services:"
    echo "  - SIP Agent: http://localhost:8080"
    echo "  - Web UI: http://localhost:8081"
    echo "  - Metrics: http://localhost:9090/metrics"
    echo ""
    echo "📋 Logs:"
    echo "  - View logs: docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
    echo "  - SIP Agent logs: docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs sip-agent"
    echo "  - Web UI logs: docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs web"
}

rollback() {
    log_warning "Rolling back deployment..."
    
    # Stop current services
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
    
    # Pull previous version (you might want to implement version tracking)
    local prev_version="${PREVIOUS_VERSION:-latest}"
    docker pull "${REGISTRY}/${REPO_NAME}:${prev_version}"
    docker pull "${REGISTRY}/${REPO_NAME}-web:${prev_version}"
    
    # Deploy previous version
    VERSION="${prev_version}" docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    log_success "Rollback completed"
}

# Main function
main() {
    case "${1:-deploy}" in
        "deploy")
            log_info "Starting deployment..."
            log_info "Registry: ${REGISTRY}"
            log_info "Repository: ${REPO_NAME}"
            log_info "Version: ${VERSION}"
            log_info "Environment: ${ENVIRONMENT}"
            echo ""
            
            check_requirements
            pull_images
            deploy_services
            wait_for_health
            show_status
            
            log_success "Deployment completed successfully!"
            ;;
        "rollback")
            rollback
            ;;
        "status")
            show_status
            ;;
        "logs")
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
            ;;
        "stop")
            log_info "Stopping services..."
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
            log_success "Services stopped"
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  deploy   - Deploy the application (default)"
            echo "  rollback - Rollback to previous version"
            echo "  status   - Show deployment status"
            echo "  logs     - Show application logs"
            echo "  stop     - Stop all services"
            echo "  help     - Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  VERSION           - Docker image version (default: latest)"
            echo "  ENVIRONMENT       - Deployment environment (default: production)"
            echo "  GITHUB_REPOSITORY - GitHub repository name"
            echo "  PREVIOUS_VERSION  - Previous version for rollback"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
