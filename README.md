# OpenAI Voice SIP Agent

This project registers a Python SIP client as an extension in Asterisk/FreePBX and connects calls to OpenAI Voice Agent in real-time using WebSocket.

## 🧰 Requirements

- Asterisk/FreePBX server with a configured SIP extension
- Docker and Docker Compose
- OpenAI API Key and Voice Agent ID

## 📁 Project Structure

- `docker-compose.yml`: Sets up the container
- `Dockerfile`: Builds Python environment
- `app/agent.py`: Python SIP client code
- `.env`: Configuration for SIP and OpenAI

## ⚙️ Setup

1. **Edit `.env`:**

```env
SIP_DOMAIN=your.asterisk.ip.or.domain
SIP_USER=1001
SIP_PASS=yourpassword
OPENAI_API_KEY=sk-...
AGENT_ID=va_...
```

2. **Build and Run:**

```bash
docker compose up --build
```

3. **Check Logs:**

Make sure the SIP client registers and waits for incoming calls.

## 📞 How it works

- Registers as a SIP extension
- Answers incoming calls
- Streams audio to OpenAI's Voice Agent
- Sends replies back to the caller in real time

## 🧪 Test

Call the extension you configured in FreePBX and start a conversation with your AI assistant 🎙️

## 📋 Changelog

### v1.0.0 (Initial Release)
- Basic SIP client implementation
- OpenAI Voice API integration
- Docker containerization

### v1.1.0
- Multi-stage Docker build for optimized image size
- Improved error handling and logging
- Added port exposures for SIP and RTP

### v1.2.0
- Added monitoring interface
- Enhanced call state management
- Token usage tracking

## 🤝 Contributing

Contributions are welcome! Here's how you can help improve this project:

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit your changes**:
   ```bash
   git commit -m 'Add some feature'
   ```
4. **Push to the branch**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request**

### Coding Standards
- Follow PEP 8 style guide for Python code
- Document new functions and classes
- Add appropriate error handling
- Write tests for new features when possible

---

Made with ❤️ for real-time AI voice interaction.

