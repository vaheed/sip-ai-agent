# SIP AI Agent Web UI

A comprehensive web interface for monitoring and managing the SIP AI Agent, built with FastAPI backend and React frontend with Tailwind CSS.

## Features

### 🎯 Live Status Monitoring
- **SIP Registration Status**: Real-time SIP registration state
- **Active Calls**: Current active call count and details
- **API Token Usage**: OpenAI API token consumption tracking
- **System Uptime**: Service uptime and health metrics
- **Real-time Logs**: Live log streaming with WebSocket

### 📞 Call History Management
- **Call Tracking**: Complete call history with start/end times
- **Duration Analytics**: Call duration tracking and statistics
- **CSV Export**: Export call history data for analysis
- **Call Statistics**: Success rates, average duration, and metrics
- **Real-time Updates**: Live call status updates

### ⚙️ Configuration Management
- **Form-based Editor**: Easy configuration editing for all settings
- **Live Reload**: Configuration changes with safe reload endpoint
- **Environment Variables**: Support for all SIP and OpenAI settings
- **Validation**: Input validation and error handling
- **Persistent Storage**: Changes saved to `.env` file

### 🔐 Authentication & Security
- **Admin Login**: Simple session-based authentication
- **Secure Cookies**: HTTP-only session cookies
- **Protected Routes**: All admin functions require authentication
- **Default Credentials**: admin/admin123 (change in production)

### 🎨 Modern UI/UX
- **Dark/Light Theme**: Toggle between themes
- **Responsive Design**: Works on desktop and mobile
- **Tailwind CSS**: Modern, clean styling
- **Real-time Updates**: WebSocket-powered live updates
- **Intuitive Navigation**: Easy-to-use interface

## Architecture

### Backend (FastAPI)
- **REST API**: Comprehensive REST endpoints
- **WebSocket Support**: Real-time event streaming
- **Authentication**: Session-based auth with cookies
- **Configuration Management**: Environment variable handling
- **Call History**: Persistent call tracking with JSON storage
- **CSV Export**: Data export functionality

### Frontend (React + Tailwind)
- **Single Page Application**: React-based SPA
- **Real-time Updates**: WebSocket integration
- **Theme Support**: Dark/light mode toggle
- **Responsive Design**: Mobile-first approach
- **Modern Components**: Clean, professional UI

## Quick Start

### 1. Development Setup

```bash
# Install dependencies
make install

# Start the web UI (development)
make web-ui

# Start with demo calls
make web-demo
```

### 2. Docker Setup

```bash
# Build web UI container
make web-build

# Run web UI in Docker
make web-run

# Or use docker-compose
docker-compose up web
```

### 3. Access the Dashboard

- **URL**: http://localhost:8080
- **Username**: admin
- **Password**: admin123

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/logout` - Logout and clear session
- `GET /api/auth/status` - Check authentication status

### System Status
- `GET /api/status` - Get system status and metrics
- `GET /api/logs` - Get recent system logs
- `GET /api/call_history` - Get call history
- `GET /api/call_history/csv` - Export call history as CSV
- `GET /api/call_history/statistics` - Get call statistics

### Configuration
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `POST /api/config/reload` - Reload configuration

### WebSocket
- `WS /ws/events` - Real-time event stream

### Health Check
- `GET /healthz` - Health check endpoint

## Configuration

The web UI supports all SIP AI Agent configuration options:

### SIP Settings
- `SIP_DOMAIN` - SIP domain or IP address
- `SIP_USER` - SIP username
- `SIP_PASS` - SIP password
- `SIP_SRTP_ENABLED` - Enable SRTP encryption
- `SIP_JITTER_BUFFER_SIZE` - Jitter buffer size

### OpenAI Settings
- `OPENAI_API_KEY` - OpenAI API key
- `AGENT_ID` - OpenAI agent ID
- `OPENAI_MODE` - API mode (legacy/realtime)
- `OPENAI_MODEL` - Model name
- `OPENAI_VOICE` - Voice selection
- `OPENAI_TEMPERATURE` - Temperature setting
- `SYSTEM_PROMPT` - System prompt

### Advanced Settings
- `AUDIO_BACKPRESSURE_THRESHOLD` - Audio queue threshold
- `SIP_REGISTRATION_RETRY_MAX` - Max registration retries
- `SIP_REGISTRATION_RETRY_BACKOFF` - Retry backoff multiplier

## Call History

### Features
- **Automatic Tracking**: All calls are automatically tracked
- **Persistent Storage**: History saved to `call_history.json`
- **Rich Metadata**: Includes caller, callee, duration, tokens, cost
- **Audio Quality Metrics**: Packet loss, jitter, latency, MOS score
- **Error Tracking**: Failed calls with error messages

### Data Structure
```json
{
  "call_id": "call-123",
  "caller": "+15551234567",
  "callee": "+15557654321",
  "direction": "incoming",
  "start_time": 1640995200.0,
  "end_time": 1640995260.0,
  "duration": 60.0,
  "status": "completed",
  "tokens_used": 1500,
  "cost": 0.0015,
  "audio_quality_metrics": {
    "packet_loss": 0.01,
    "jitter": 25.5,
    "latency": 120.0,
    "mos_score": 4.2
  },
  "error_message": null
}
```

## WebSocket Events

Real-time events are broadcast via WebSocket:

```json
{
  "type": "system_update",
  "data": {
    "sip_registered": true,
    "active_calls": ["call-123", "call-124"],
    "api_tokens_used": 5000,
    "timestamp": 1640995200.0
  }
}
```

Event types:
- `system_update` - System status updates
- `config_updated` - Configuration changes
- `config_reloaded` - Configuration reload
- `call_started` - New call started
- `call_ended` - Call ended

## Demo Mode

Run with demo calls to test the interface:

```bash
# Start with demo data
make web-demo

# Or manually
python -m app.start_web_ui --demo
```

This creates:
- 10 historical demo calls
- Live call simulation
- Realistic call data
- Token usage simulation

## Docker Configuration

### docker-compose.yml
```yaml
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    container_name: sip-ai-web
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./web:/app/web
      - ./app:/app/app
      - ./.env:/app/.env
    depends_on:
      - sip-agent
```

### Dockerfile.web
Multi-stage build with:
- Python 3.11 base image
- FastAPI and dependencies
- Static file serving
- Health checks
- Proper signal handling

## Security Considerations

### Production Deployment
1. **Change Default Password**: Update admin credentials
2. **Use HTTPS**: Enable SSL/TLS encryption
3. **Environment Variables**: Use secure secret management
4. **Network Security**: Restrict access with firewalls
5. **Session Security**: Use secure session tokens

### Authentication
- Session-based authentication with HTTP-only cookies
- CSRF protection via SameSite cookies
- Secure password hashing (SHA-256)
- Session timeout handling

## Monitoring & Observability

### Health Checks
- `/healthz` endpoint for container orchestration
- Service status monitoring
- Dependency health checks

### Logging
- Structured JSON logging
- Correlation IDs for tracing
- Request/response logging
- Error tracking and reporting

### Metrics
- Prometheus metrics integration
- Call statistics and analytics
- Performance monitoring
- Resource usage tracking

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check firewall settings
   - Verify WebSocket proxy configuration
   - Check browser console for errors

2. **Authentication Issues**
   - Verify credentials (admin/admin123)
   - Check session cookie settings
   - Clear browser cache/cookies

3. **Configuration Not Saving**
   - Check file permissions on `.env`
   - Verify environment variable format
   - Check application logs for errors

4. **Call History Not Updating**
   - Verify call history manager is running
   - Check JSON file permissions
   - Restart the service

### Debug Mode
```bash
# Enable debug logging
export MONITOR_LOG_LEVEL=DEBUG
make web-ui
```

### Logs
Check application logs for detailed error information:
```bash
# Docker logs
docker-compose logs web

# Application logs
tail -f logs/sip-ai-agent.log
```

## Development

### Adding New Features

1. **Backend**: Add endpoints in `web_backend.py`
2. **Frontend**: Update React components in `web/index.html`
3. **Configuration**: Add new config options to the form
4. **WebSocket**: Add new event types for real-time updates

### Testing
```bash
# Run tests
make test

# Test web UI specifically
pytest tests/test_web_backend.py -v
```

### Code Quality
```bash
# Format code
make format

# Run linting
make lint

# Type checking
make typecheck
```

## License

This web UI is part of the SIP AI Agent project and follows the same license terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Create an issue in the project repository
4. Check the main SIP AI Agent documentation
