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

---

Made with ❤️ for real-time AI voice interaction.
