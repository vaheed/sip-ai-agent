# 🚀 SIP AI Agent - Production Deployment Guide

## 📋 Prerequisites

- Docker and Docker Compose installed
- GitHub Container Registry access
- SIP server credentials
- OpenAI API key

## 🔧 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/vaheed/sip-ai-agent.git
cd sip-ai-agent
```

### 2. Configure Environment

```bash
cp env.example .env
```

Edit `.env` with your settings:

```bash
# Required Settings
SIP_DOMAIN=your-sip-domain.com
SIP_USER=your-sip-username
SIP_PASS=your-sip-password
OPENAI_API_KEY=your-openai-api-key
AGENT_ID=your-agent-id

# Web UI Login (Default)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Optional Settings
OPENAI_MODE=realtime
OPENAI_MODEL=gpt-realtime
OPENAI_VOICE=alloy
```

### 3. Deploy with Docker Compose

#### Option A: Simple Deployment (Recommended)
```bash
# Start only the essential services
docker-compose -f docker-compose.prod.yml up sip-agent web -d
```

#### Option B: Full Deployment with Nginx
```bash
# Start all services including reverse proxy
docker-compose -f docker-compose.prod.yml up -d
```

## 🌐 Access Points

After deployment, access your services:

- **Web Dashboard**: http://localhost:8080 (sip-agent) or http://localhost:8081 (web)
- **Metrics**: http://localhost:9090/metrics
- **Health Check**: http://localhost:8080/healthz
- **Nginx (if enabled)**: http://localhost:80

## 🔐 Default Login Credentials

**Web UI Dashboard:**
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **IMPORTANT**: Change these credentials in production!

## 📊 Service Architecture

### Core Services

1. **sip-agent** (Port 8080)
   - Main SIP AI Agent
   - Handles SIP calls and OpenAI integration
   - Provides Web UI dashboard
   - Exposes metrics on port 9090

2. **web** (Port 8081)
   - Standalone Web UI service
   - Alternative dashboard interface
   - Depends on sip-agent service

### Optional Services

3. **nginx** (Port 80/443)
   - Reverse proxy for production
   - SSL termination
   - Load balancing

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SIP_DOMAIN` | SIP server domain | - | ✅ |
| `SIP_USER` | SIP username | - | ✅ |
| `SIP_PASS` | SIP password | - | ✅ |
| `OPENAI_API_KEY` | OpenAI API key | - | ✅ |
| `AGENT_ID` | Unique agent identifier | - | ✅ |
| `ADMIN_USERNAME` | Web UI username | `admin` | ❌ |
| `ADMIN_PASSWORD` | Web UI password | `admin123` | ❌ |
| `OPENAI_MODE` | OpenAI API mode | `legacy` | ❌ |
| `OPENAI_MODEL` | OpenAI model | `gpt-4` | ❌ |
| `OPENAI_VOICE` | OpenAI voice | `alloy` | ❌ |

### Port Configuration

| Service | Internal Port | External Port | Protocol |
|---------|---------------|---------------|----------|
| Web UI | 8080 | 8080/8081 | HTTP |
| Metrics | 9090 | 9090 | HTTP |
| SIP Signaling | 5060 | 5060 | UDP |
| RTP Media | 16000-16100 | 16000-16100 | UDP |

## 🛠️ Management Commands

### Start Services
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f sip-agent
```

### Update Services
```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart with new images
docker-compose -f docker-compose.prod.yml up -d
```

### Health Check
```bash
# Check service health
docker-compose -f docker-compose.prod.yml ps

# Test health endpoint
curl http://localhost:8080/healthz
```

## 🔒 Security Considerations

1. **Change default credentials**:
   ```bash
   ADMIN_USERNAME=your-username
   ADMIN_PASSWORD=your-secure-password
   ```

2. **Use HTTPS in production**:
   - Configure SSL certificates in `./ssl/`
   - Update nginx configuration

3. **Firewall configuration**:
   - Only expose necessary ports
   - Use VPN for SIP access if possible

4. **Environment file security**:
   - Never commit `.env` to version control
   - Use Docker secrets for sensitive data

## 📈 Monitoring

### Metrics Endpoint
- **URL**: http://localhost:9090/metrics
- **Format**: Prometheus metrics
- **Integration**: Grafana, Prometheus

### Health Monitoring
- **URL**: http://localhost:8080/healthz
- **Response**: JSON health status
- **Checks**: SIP registration, OpenAI connectivity, system resources

### Logs
- **Location**: `./logs/` directory
- **Format**: Structured JSON logs
- **Rotation**: Automatic log rotation configured

## 🚨 Troubleshooting

### Common Issues

1. **SIP Registration Failed**
   - Check SIP credentials
   - Verify network connectivity
   - Check firewall settings

2. **OpenAI API Errors**
   - Verify API key validity
   - Check API quota and billing
   - Review rate limits

3. **Web UI Not Accessible**
   - Check port configuration
   - Verify container health
   - Review logs for errors

4. **Audio Issues**
   - Check RTP port range
   - Verify NAT traversal settings
   - Review audio codec configuration

### Debug Commands

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View detailed logs
docker-compose -f docker-compose.prod.yml logs --tail=100 sip-agent

# Execute commands in container
docker-compose -f docker-compose.prod.yml exec sip-agent bash

# Check resource usage
docker stats
```

## 📞 Support

For issues and support:
- **GitHub Issues**: [Create an issue](https://github.com/vaheed/sip-ai-agent/issues)
- **Documentation**: Check the README.md
- **Logs**: Always include relevant logs when reporting issues

## 🔄 Updates

To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Pull latest Docker images
docker-compose -f docker-compose.prod.yml pull

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

---

**Note**: This deployment guide assumes you have basic Docker knowledge. For advanced configurations, refer to the Docker Compose documentation.