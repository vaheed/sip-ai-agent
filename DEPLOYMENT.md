# SIP AI Agent - Deployment Guide

This guide covers deploying the SIP AI Agent with Docker versioning and GitHub Container Registry.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- GitHub Container Registry access
- `.env` file configured

### Basic Deployment

```bash
# Deploy latest version
./scripts/deploy.sh

# Deploy specific version
VERSION=v1.2.3 ./scripts/deploy.sh

# Check deployment status
./scripts/deploy.sh status
```

## 📦 Docker Images

The application consists of two Docker images:

- **SIP Agent**: `ghcr.io/your-org/sip-ai-agent:version`
- **Web UI**: `ghcr.io/your-org/sip-ai-agent-web:version`

### Image Tags

- `latest` - Latest stable version
- `v1.2.3` - Specific semantic version
- `main-abc1234` - Branch-based version
- `develop-xyz5678` - Development version

## 🔄 Version Management

### Using the Version Script

```bash
# Show current version
make version

# Bump version
make version-bump-patch  # 1.0.0 -> 1.0.1
make version-bump-minor  # 1.0.0 -> 1.1.0
make version-bump-major  # 1.0.0 -> 2.0.0

# Create and push git tag
make version-tag

# Show Docker image info
make version-info

# Create a complete release
make release
```

### Manual Version Management

```bash
# Bump version and create tag
python scripts/version.py bump --type patch
python scripts/version.py tag --push

# Show version info
python scripts/version.py info
```

## 🏗️ GitHub Actions

### Automatic Builds

The GitHub Actions workflow automatically builds and pushes Docker images when:

- **Push to main**: Creates `latest` tag
- **Push to develop**: Creates `develop-<sha>` tag
- **Create tag**: Creates version-specific tags
- **Pull Request**: Builds but doesn't push

### Workflow Features

- ✅ Multi-platform builds
- ✅ Vulnerability scanning with Trivy
- ✅ Cache optimization
- ✅ Automatic tagging
- ✅ Security scanning

## 🚢 Production Deployment

### Using Docker Compose

```bash
# Deploy with production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Deploy specific version
VERSION=v1.2.3 docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Using the Deployment Script

```bash
# Deploy to production
ENVIRONMENT=production VERSION=v1.2.3 ./scripts/deploy.sh

# Check status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs

# Rollback if needed
PREVIOUS_VERSION=v1.2.2 ./scripts/deploy.sh rollback
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
SIP_DOMAIN=your-sip-domain.com
SIP_USER=your-sip-user
SIP_PASS=your-sip-password
OPENAI_API_KEY=your-openai-key
AGENT_ID=your-agent-id

# Optional
VERSION=latest
ENVIRONMENT=production
GITHUB_REPOSITORY=your-org/sip-ai-agent
```

### Docker Compose Overrides

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'
services:
  sip-agent:
    ports:
      - "8080:8080"
    environment:
      - DEBUG=true
```

## 📊 Monitoring

### Health Checks

- **SIP Agent**: `http://localhost:8080/healthz`
- **Web UI**: `http://localhost:8081/healthz`
- **Metrics**: `http://localhost:9090/metrics`

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f sip-agent
docker-compose logs -f web

# Last 100 lines
docker-compose logs --tail=100 sip-agent
```

## 🔒 Security

### Vulnerability Scanning

The GitHub Actions workflow includes Trivy vulnerability scanning:

- Scans all Docker images
- Reports to GitHub Security tab
- Fails build on high-severity issues

### Security Best Practices

- Use specific version tags in production
- Regularly update base images
- Scan images before deployment
- Use non-root users in containers
- Limit container privileges

## 🚨 Troubleshooting

### Common Issues

#### Image Pull Failures

```bash
# Check registry access
docker pull ghcr.io/your-org/sip-ai-agent:latest

# Login to registry
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin
```

#### Service Health Check Failures

```bash
# Check service logs
docker-compose logs sip-agent

# Check health endpoint manually
curl -f http://localhost:8080/healthz

# Restart service
docker-compose restart sip-agent
```

#### Port Conflicts

```bash
# Check port usage
netstat -tulpn | grep :8080

# Use different ports
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Debug Mode

```bash
# Enable debug logging
DEBUG=true docker-compose up

# Access container shell
docker-compose exec sip-agent bash
docker-compose exec web bash
```

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  sip-agent:
    deploy:
      replicas: 3
    ports:
      - "8080-8082:8080"
```

### Load Balancing

Use nginx or traefik for load balancing multiple instances.

## 🔄 Updates and Rollbacks

### Rolling Updates

```bash
# Update to new version
VERSION=v1.3.0 ./scripts/deploy.sh

# Rollback if issues
PREVIOUS_VERSION=v1.2.3 ./scripts/deploy.sh rollback
```

### Blue-Green Deployment

```bash
# Deploy to staging
ENVIRONMENT=staging VERSION=v1.3.0 ./scripts/deploy.sh

# Test staging
curl http://staging.example.com/healthz

# Switch to production
ENVIRONMENT=production VERSION=v1.3.0 ./scripts/deploy.sh
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Trivy Security Scanner](https://trivy.dev/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

## 🆘 Support

For deployment issues:

1. Check the logs: `./scripts/deploy.sh logs`
2. Verify configuration: `make env-check`
3. Test health endpoints: `make health`
4. Review GitHub Actions logs
5. Open an issue with deployment details
