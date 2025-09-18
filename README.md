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

   # Runtime toggles
   ENABLE_SIP=true
   ENABLE_AUDIO=true

   # Choose API mode: legacy or realtime
   OPENAI_MODE=realtime

   # Realtime settings
   OPENAI_MODEL=gpt‑realtime
   OPENAI_VOICE=alloy
   OPENAI_TEMPERATURE=0.3
   SYSTEM_PROMPT=You are a helpful voice assistant.
   ```

   Set `ENABLE_SIP=false` to run only the monitoring dashboard without
   registering to your PBX, or `ENABLE_AUDIO=false` to keep signalling active
   while disabling the media bridge.  Configuration is validated on startup;
   if any required variables are missing or malformed the agent exits with a
   detailed error that lists the offending keys in both the console output and
   the monitoring dashboard logs.

   You can validate your `.env` file at any time using the built-in helper:

   ```bash
   python -m app.config validate --path .env
   # or via make
   make env-validate
   ```

   To regenerate the example configuration with the latest defaults, run:

   ```bash
   python -m app.config sample --write --path env.example
   # or
   make env-sample
   ```

   When using realtime mode the agent sends a `session.update` message to
   OpenAI containing the model, voice, audio format (16‑bit PCM at 16 kHz)
   and system prompt【826943400076790†L230-L249】.  This ensures the session is
   configured correctly before audio streaming begins.

### Advanced SIP configuration

The `.env` file exposes optional knobs to tune realtime media handling, retry
behaviour and NAT traversal.  Each key maps to the strongly typed Pydantic
`Settings` model so invalid values fail fast during startup and the dashboard
can safely surface defaults when a field is cleared.

#### Feature toggles & realtime session

| Setting | Default | Description |
| --- | --- | --- |
| `ENABLE_SIP` | `true` | Disable to run only the dashboard without registering to the PBX. |
| `ENABLE_AUDIO` | `true` | Disable to keep SIP signalling active while muting the media bridge. |
| `OPENAI_MODE` | `legacy` | Choose between the legacy `/v1/audio/speech` WebSocket mode and `realtime`. |
| `OPENAI_MODEL` | `gpt-realtime` | Model requested in the initial `session.update` message. |
| `OPENAI_VOICE` | `alloy` | Voice to synthesise during realtime playback. |
| `OPENAI_TEMPERATURE` | `0.3` | Sampling temperature for OpenAI responses (0–2). |
| `SYSTEM_PROMPT` | `You are a helpful voice assistant.` | System instructions sent with each realtime session. |

#### Audio pipeline controls

| Setting | Default | Description |
| --- | --- | --- |
| `SIP_TRANSPORT_PORT` | `5060` | UDP port used for SIP signalling. Change if your PBX expects a non-standard port. |
| `SIP_PREFERRED_CODECS` | `PCMU,PCMA,opus` | Comma-separated codec priority list; unknown codecs are ignored. |
| `SIP_JB_MIN` | `0` | Minimum jitter buffer in milliseconds. Set >0 to pin a floor for bursty networks. |
| `SIP_JB_MAX` | `0` | Maximum jitter buffer size in milliseconds. Increase to smooth jitter at the cost of latency. |
| `SIP_JB_MAX_PRE` | `0` | Pre-echo jitter buffer limit in milliseconds. Useful when bridging to high-latency trunks. |

#### NAT traversal & media security

| Setting | Default | Description |
| --- | --- | --- |
| `SIP_ENABLE_ICE` | `false` | Toggle ICE negotiation; enable when endpoints sit behind symmetric NAT. |
| `SIP_ENABLE_TURN` | `false` | Enable TURN relaying. Requires TURN server credentials below. |
| `SIP_STUN_SERVER` | _blank_ | Optional STUN URI such as `stun:stun.l.google.com:19302`. |
| `SIP_TURN_SERVER` | _blank_ | TURN server URI (e.g. `turn:turn.example.com:3478`). Leave blank to disable. |
| `SIP_TURN_USER` | _blank_ | TURN username when relaying media. |
| `SIP_TURN_PASS` | _blank_ | TURN password when relaying media. |
| `SIP_ENABLE_SRTP` | `false` | Enable to negotiate Secure RTP for encrypted audio. |
| `SIP_SRTP_OPTIONAL` | `true` | When SRTP is on, allow RTP fallback (`true`) or enforce SRTP-only (`false`). |

#### Retry and backoff controls

| Setting | Default | Description |
| --- | --- | --- |
| `SIP_REG_RETRY_BASE` | `2.0` | Seconds before the first registration retry. Doubles until `SIP_REG_RETRY_MAX`. |
| `SIP_REG_RETRY_MAX` | `60.0` | Upper bound for registration retry delays. |
| `SIP_INVITE_RETRY_BASE` | `1.0` | Seconds before retrying an outbound INVITE after a 4xx/5xx failure. |
| `SIP_INVITE_RETRY_MAX` | `30.0` | Upper bound for INVITE retry delays. |
| `SIP_INVITE_MAX_ATTEMPTS` | `5` | Maximum number of INVITE attempts before the call is marked failed. |

Adjusting these values lets you tune the retry cadence for unreliable trunks,
increase jitter buffers for choppy links or prioritise wideband codecs.  The
monitoring dashboard exposes every field so you can experiment at runtime; when
a value is cleared the agent falls back to the safe defaults shown above.

3. **Install dependencies for local development (optional)**

   To run the agent directly on your machine (or in CI) install the Python
   requirements and then invoke the helper script that builds the PJSIP
   libraries and `pjsua2` bindings:

   ```bash
   pip install -r requirements.txt
   python scripts/install_pjsua2.py
   # or use the bundled make target
   make install
   ```

   The installer downloads `pjproject` 2.12, compiles it with
   `--enable-shared`, builds the `pjsua2` Python module and installs it into
   the active interpreter—the same sequence executed inside the Docker image.
   Ensure the required system packages (`build-essential`, `libpcap-dev`,
   `portaudio19-dev`, `python3-dev`, `swig`, etc.) are available on your host.

4. **Build and start the container**

   ```bash
   docker compose up --build
   ```

   This pulls the dependencies, runs the shared installer for PJSIP and starts
   the agent.  The container exposes the following ports:

   * `8080/tcp` — monitoring dashboard
   * `5060/udp` — SIP signalling
   * `16000–16100/udp` — RTP media

5. **Access the dashboard**

   Open your browser to `http://<docker-host>:8080`.  The home page shows the
   current registration state, active calls, token usage and a log view.
   Visit `/dashboard` for an advanced dashboard with a configuration form and
   call history.  Administrator authentication is required for the dashboard
   and API routes; log in with the credentials defined by
   `MONITOR_ADMIN_USERNAME` / `MONITOR_ADMIN_PASSWORD` (default: `admin` / `admin`).
   After editing and saving the configuration, restart the container for
   changes to take effect.

## Dashboard

The built‑in dashboard provides a convenient way to monitor and manage the
agent:

* **Status** — Shows whether the SIP account is registered, lists active
  calls and displays the total number of tokens used.
* **Logs** — Streams recent log entries via a WebSocket so you can watch events
  in real time.
* **Call history** — Lists each call’s start time, end time and duration,
  enabling you to visualise call flow.
* **Configuration editor** — Presents the contents of your `.env` file in a
  form.  Update values and click save to write them back to disk.  A container
  restart is required to apply changes.

### Frontend development

The dashboard UI lives in [`web/`](web/) and is implemented with React, Vite
and Tailwind CSS.  During development you can run the Vite dev server:

```bash
cd web
npm install
npm run dev
```

For production builds run `npm run build`.  The compiled assets are emitted to
`app/static/dashboard` and automatically served by the FastAPI application at
`/dashboard`.

Set `MONITOR_SESSION_TTL` (seconds) to adjust how long administrator sessions
remain valid.  The authentication cookie name defaults to `monitor_session` and
can be customised via `MONITOR_SESSION_COOKIE` if your deployment requires it.

## Operations and troubleshooting

### SIP failure modes

The agent surfaces common SIP registration and call failures in both the
dashboard log stream and the structured JSON logs emitted by the container.
Use the table below to map the most frequent responses to corrective action:

| Code | When it appears | Suggested action |
| --- | --- | --- |
| `401` / `407` | Registration challenge or INVITE authentication failure. | Verify `SIP_USER`/`SIP_PASS`, and watch the `register_retries` counter on `/metrics` to confirm retries are happening. |
| `403` | PBX rejected the credentials even after authentication. | Confirm the extension is allowed to register from the agent’s IP and not rate-limited. |
| `404` / `484` | PBX could not locate the requested extension. | Check the dialled target, trunk routing and any translation rules on the PBX. |
| `415` / `488` | Unsupported media type or codec mismatch. | Adjust `SIP_PREFERRED_CODECS` or enable SRTP to match the PBX media profile. |
| `480` / `503` | Destination temporarily unavailable or service unavailable. | Inspect NAT/firewall reachability and TURN/STUN configuration; `invite_retries` increments indicate the automatic backoff is active. |
| `500` / `502` | PBX internal error or bad gateway. | Review PBX logs for upstream issues and consider increasing `SIP_INVITE_RETRY_MAX` to give the remote server time to recover. |

When a call fails, the dashboard highlights the SIP status code and the
`metrics` endpoint exposes the associated retry counters so you can correlate
spikes with network events or PBX changes.

### Firewall and RTP port planning

Open UDP port `5060` (or the value configured via `SIP_TRANSPORT_PORT`) and the
media range `16000–16100/udp` between the PBX and the Docker host.  On
firewalls that inspect SIP ALG traffic, disable the ALG or pin static
forwarding rules to prevent rewritten SDP payloads.  For double-NAT or cloud
deployments, ensure the PBX can route media back to the agent—ICE or TURN (see
below) can relay audio when direct UDP paths fail.

### SRTP and NAT setup

Secure media and NAT traversal are toggled entirely through environment
variables.  Enable `SIP_ENABLE_SRTP=true` to negotiate encrypted audio and set
`SIP_SRTP_OPTIONAL=false` when the PBX mandates SRTP-only sessions.  For
networks behind symmetric NAT, enable `SIP_ENABLE_ICE=true` and provide a
`SIP_STUN_SERVER` such as `stun:stun.l.google.com:19302`.  If direct paths fail
or you need to hairpin through the public internet, configure TURN credentials
(`SIP_TURN_SERVER`, `SIP_TURN_USER`, `SIP_TURN_PASS`) and set
`SIP_ENABLE_TURN=true` so the agent relays RTP through your media proxy.

### Troubleshooting with metrics and logs

Structured logs include a `correlation_id`, making it easy to follow a single
call across SIP events, OpenAI websocket activity and audio bridge state
changes.  Access them via `docker compose logs` or the dashboard log pane.  The
monitor also exposes `/metrics`, returning JSON snapshots with call counts,
latency percentiles, token usage and the audio pipeline event counters (e.g.
`legacy_stream_started`, `realtime_ws_unhealthy`).  Use `curl` while a call is
active to inspect jitter, retry and websocket health in real time:

```bash
curl http://localhost:8080/metrics | jq
```

### Tuning retries and the audio pipeline

Retry timings and media buffering are governed by the Pydantic `Settings`
model.  Update values in `.env`, run `python -m app.config validate` to check
types and bounds, then restart the container.  Increasing
`SIP_INVITE_MAX_ATTEMPTS` helps stubborn trunks, while widening
`SIP_JB_MAX`/`SIP_JB_MAX_PRE` smooths jitter at the expense of latency.  When
optimising codec selection, reorder `SIP_PREFERRED_CODECS` to prioritise wideband
codecs such as `opus`—the agent will automatically ignore unknown names.

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

This project ships with a `Makefile` and pre-commit configuration to
standardise local workflows.  To get started run:

```bash
make dev       # install runtime + development dependencies and configure pre-commit
make lint      # ruff check .
make type      # mypy static type analysis
make test      # pytest -q
make format    # apply ruff's formatter
make env-validate  # validate .env against the pydantic schema
make env-sample    # regenerate env.example from the canonical template
```

The `tests/` directory now includes coverage for the realtime and legacy audio
pipelines (`tests/test_audio_pipeline.py`) alongside configuration validation.
Run `make test` (or `pytest -q`) after tweaking codecs, jitter buffers or retry
windows to ensure the new behaviour still streams audio as expected.

### Testing & CI

The `requirements-dev.txt` file extends the runtime dependencies with the
tooling used in CI.  GitHub Actions runs the same checks as the Makefile:

* `make lint` → `ruff check` for style and static analysis.
* `make type` → `mypy` against the `app/` package.
* `make test` → `pytest -q` exercising SIP call flows and audio buffering.
* `make pre-commit` → `pre-commit run --all-files` to mirror the aggregate CI job.

Running `make dev` once installs the hooks so `pre-commit` enforces formatting
before each commit.  You can still run `python app/agent.py` directly once your
environment variables are configured; the monitor listens on port 8080 by
default.

### Contributing

Contributions are welcome!  Please see `CONTRIBUTING.md` for guidelines on
submitting bug reports, feature requests and pull requests.

### Changelog

See `CHANGELOG.md` for a history of releases and notable changes.

---

Made with ❤️ to explore the future of real‑time AI voice interactions.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
