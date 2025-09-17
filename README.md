[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# OpenAI SIP Voice Agent

## Overview

This repository packages a Python application that registers as a SIP extension
on your PBX and connects callers to an OpenAI voice assistant.  It supports
both the legacy `/v1/audio/speech` WebSocket API and the newer realtime API
for ultra‑low‑latency speech‑to‑speech interactions.  When `OPENAI_MODE` is
set to `realtime`, audio from the caller is streamed directly to OpenAI and
responses are streamed back as audio deltas, eliminating the need to convert
speech to text and back and dramatically reducing latency【878443186554662†L53-L66】.  The
realtime API also introduces new voices such as **Cedar** and **Marin** which
provide a more natural and expressive sound【214777425731610†L286-L314】.

### Features

* **SIP client** using PJSIP that registers with your PBX, answers incoming
  calls and streams audio to OpenAI.
* **Realtime API support** for low‑latency speech‑to‑speech conversations.
  The agent sends a `session.update` message on connection specifying the
  model, voice, audio formats and system instructions as recommended in
  OpenAI’s documentation【826943400076790†L230-L249】.
* **Asynchronous architecture** using `asyncio` for efficient audio and
  WebSocket handling.
* **Web dashboard** displaying SIP registration state, active calls, token
  usage, call history and real‑time logs.  The dashboard also includes a
  configuration editor so you can update your `.env` settings from the
  browser.
* **Step‑by‑step integration** guides for FreePBX and VICIdial.

## Requirements

* Asterisk‑based PBX (FreePBX or VICIdial) with an extension configured
  for the agent.
* Docker and Docker Compose.
* An OpenAI API key.  If you plan to use the realtime API, ensure your
  key has access to the `gpt‑realtime` model【214777425731610†L286-L314】.

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your‑org/openai‑sip‑agent.git
   cd openai‑sip‑agent
   ```

2. **Configure the environment**

   Copy `.env.example` to `.env` and edit it.  At minimum you must set your
   SIP domain, username and password, your OpenAI API key and the agent ID.
   You can also select which API to use (legacy or realtime), the model,
   voice and temperature.  Example:

   ```env
   # PBX
   SIP_DOMAIN=pbx.example.com
   SIP_USER=1001
   SIP_PASS=secret

   # OpenAI
   OPENAI_API_KEY=sk‑...
   AGENT_ID=va_123456789

   # Choose API mode: legacy or realtime
   OPENAI_MODE=realtime

   # Realtime settings
   OPENAI_MODEL=gpt‑realtime
   OPENAI_VOICE=alloy
   OPENAI_TEMPERATURE=0.3
   SYSTEM_PROMPT=You are a helpful voice assistant.
   ```

   When using realtime mode the agent sends a `session.update` message to
   OpenAI containing the model, voice, audio format (16‑bit PCM at 16 kHz)
   and system prompt【826943400076790†L230-L249】.  This ensures the session is
   configured correctly before audio streaming begins.

### Advanced SIP configuration

The `.env` file also exposes optional knobs to tune media behaviour and NAT
traversal.  Every setting has a documented default so you can safely leave it
unset.  When the values are blank or set to `0`/`false` the agent relies on
PJSIP’s defaults and features remain disabled.

| Setting | Default | Description |
| --- | --- | --- |
| `SIP_TRANSPORT_PORT` | `5060` | UDP port used for signalling. |
| `SIP_JB_MIN`, `SIP_JB_MAX`, `SIP_JB_MAX_PRE` | `0` | Jitter buffer sizes in milliseconds. Zero keeps the library defaults. |
| `SIP_ENABLE_ICE` | `false` | Toggle ICE negotiation for NAT traversal. |
| `SIP_ENABLE_TURN` | `false` | Enable TURN relaying. Requires TURN server credentials. |
| `SIP_STUN_SERVER` | _blank_ | Optional STUN server URI. |
| `SIP_TURN_SERVER`, `SIP_TURN_USER`, `SIP_TURN_PASS` | _blank_ | TURN credentials. Leave blank to disable TURN. |
| `SIP_ENABLE_SRTP` | `false` | When `true`, SRTP is negotiated. |
| `SIP_SRTP_OPTIONAL` | `true` | If SRTP is enabled, `true` allows fallback to RTP, `false` enforces SRTP. |
| `SIP_PREFERRED_CODECS` | _blank_ | Comma-separated codec list. Unknown codecs are ignored; blank keeps library order. |
| `SIP_REG_RETRY_BASE`/`MAX` | `2.0` / `60.0` | Exponential backoff window for registration retries (seconds). |
| `SIP_INVITE_RETRY_BASE`/`MAX` | `1.0` / `30.0` | Backoff for INVITE retries when outbound calls fail with 4xx/5xx. |
| `SIP_INVITE_MAX_ATTEMPTS` | `5` | Maximum INVITE retry attempts before giving up. |

The monitoring dashboard exposes these fields so you can update them at
runtime.  If a setting is cleared, the agent automatically falls back to the
safe defaults listed above.

3. **Build and start the container**

   ```bash
   docker compose up --build
   ```

   This pulls the dependencies, builds PJSIP and starts the agent.  The
   container exposes the following ports:

   * `8080/tcp` — monitoring dashboard
   * `5060/udp` — SIP signalling
   * `16000–16100/udp` — RTP media

4. **Access the dashboard**

   Open your browser to `http://<docker-host>:8080`.  The home page shows the
   current registration state, active calls, token usage and a log view.
   Visit `/dashboard` for an advanced dashboard with a configuration form and
   call history.  After editing and saving the configuration, restart
   the container for changes to take effect.

## Dashboard

The built‑in dashboard provides a convenient way to monitor and manage the
agent:

* **Status** — Shows whether the SIP account is registered, lists active
  calls and displays the total number of tokens used.
* **Logs** — Streams recent log entries so you can watch events in real time.
* **Call history** — Lists each call’s start time, end time and duration,
  enabling you to visualise call flow.
* **Configuration editor** — Presents the contents of your `.env` file in a
  form.  Update values and click save to write them back to disk.  A container
  restart is required to apply changes.

## FreePBX Integration

Follow these steps to connect the agent to FreePBX:

1. **Create a PJSIP extension** matching your `SIP_USER` and `SIP_PASS`.
   Navigate to **Applications → Extensions** in the FreePBX GUI, choose
   “PJSIP” and configure the extension number and secret.  Disable voicemail
   if you don’t want unanswered calls to go to voicemail.
2. **Open media ports** by allowing UDP ports 16000–16100 on your firewall.
   These ports carry the RTP audio and must reach the Docker host.
3. **Add a dialplan entry** so callers can reach the AI assistant.  Edit
   `/etc/asterisk/extensions_custom.conf` and add:

   ```asterisk
   [from-internal-custom]
   exten => 5000,1,NoOp(Call AI assistant)
     same => n,Dial(PJSIP/${SIP_USER}@${SIP_DOMAIN},60)
     same => n,Hangup()
   ```

   Reload the dialplan (e.g. `fwconsole reload`) and dial **5000** from any
   internal phone to talk to the AI assistant.

## VICIdial Integration

VICIdial uses the underlying Asterisk dialplan, so integration is similar:

1. **Define a new in‑group or campaign** that dials an extension such as
   `5000`.  This will be the number that transfers calls to the agent.
2. **Add a custom dialplan entry** in `/etc/asterisk/extensions.conf` within
   the `[default]` or appropriate context:

   ```asterisk
   exten => 5000,1,NoOp(Call AI assistant)
     same => n,Dial(PJSIP/${SIP_USER}@${SIP_DOMAIN},60)
     same => n,Hangup()
   ```

3. **Assign the campaign** to dial this extension.  When VICIdial places an
   outbound call it will transfer the caller to the OpenAI voice assistant.

Alternatively, VICIdial agents can manually dial the agent’s SIP extension
from the agent interface.  Because the agent registers as a normal SIP
extension, any device on the PBX (softphone, hardphone or dialer) can reach
it using the configured extension number.

## Development

This project is containerized for ease of deployment, but if you want to
develop locally you can install the dependencies listed in
`requirements.txt` and run `python agent.py`.  The monitor will start on
port 8080 by default.

### Contributing

Contributions are welcome!  Please see `CONTRIBUTING.md` for guidelines on
submitting bug reports, feature requests and pull requests.

### Changelog

See `CHANGELOG.md` for a history of releases and notable changes.

---

Made with ❤️ to explore the future of real‑time AI voice interactions.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
