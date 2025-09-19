[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# OpenAI SIP Voice Agent

## Table of contents
- [Overview](#overview)
- [Architecture at a glance](#architecture-at-a-glance)
- [Call flow](#call-flow)
- [Project layout](#project-layout)
- [Quick start](#quick-start)
  - [Requirements](#requirements)
  - [Configure the environment](#configure-the-environment)
  - [Validate and regenerate configs](#validate-and-regenerate-configs)
  - [Run with Docker Compose](#run-with-docker-compose)
  - [Run locally (optional)](#run-locally-optional)
  - [Access the dashboard](#access-the-dashboard)
- [Monitoring & observability](#monitoring--observability)
- [Configuration reference](#configuration-reference)
  - [Core credentials & AI session](#core-credentials--ai-session)
  - [Audio pipeline](#audio-pipeline)
  - [NAT traversal & media security](#nat-traversal--media-security)
  - [Retry & resilience](#retry--resilience)
  - [Monitor authentication](#monitor-authentication)
- [Integration guides](#integration-guides)
- [Operations & troubleshooting](#operations--troubleshooting)
- [Development workflow](#development-workflow)
- [CLI utilities & helper scripts](#cli-utilities--helper-scripts)
- [Ports & deployment topology](#ports--deployment-topology)
- [License](#license)

## Overview
OpenAI SIP Voice Agent registers as a SIP endpoint via PJSIP, bridges audio between your PBX and OpenAI’s realtime or legacy voice APIs, and streams responses back to callers without leaving your telephony domain.

A built-in FastAPI monitor and React/Tailwind dashboard authenticate administrators, stream live call status, logs, and metrics over WebSockets, and surface runtime health while configuration stays in the `.env` file.

Structured JSON logging with correlation IDs, safe reload tooling, and a strongly typed environment schema make the agent production-friendly from day one.

## Architecture at a glance
- **sip-agent** – Asyncio PJSIP client that answers calls, bridges RTP frames into OpenAI’s realtime or legacy WebSocket APIs, and tracks token usage for observability.
- **Monitor service** – FastAPI app that validates `.env` updates, streams status, exposes metrics, and coordinates safe reloads once active calls drain.
- **Dashboard** – React + Tailwind UI served by Nginx, connected to the monitor via an authenticated WebSocket for status and logs while configuration lives in `.env`.
- **Observability layer** – Structured logging with correlation IDs and an in-memory metrics collector that publishes JSON snapshots on `/metrics`.
- **Container packaging** – Multi-stage Docker build compiles the dashboard, installs PJSIP bindings, and is orchestrated via `docker-compose` for both development and production deployments.

```
PBX / SIP phones ──(SIP/RTP)──► sip-agent (PJSIP + asyncio)
                               │
                               ├── WebSocket ─► OpenAI realtime / legacy APIs
                               │
                               └── FastAPI monitor ──(REST + WebSocket)──► React dash (Nginx)
```

## Call flow
1. **Startup & configuration** – The monitor boots first; if environment validation fails the agent exits with detailed errors. Setting `ENABLE_SIP=false` leaves the dashboard running without touching the PBX.
2. **Registration** – PJSIP is initialised with jitter-buffer preferences, STUN/TURN/SRTP knobs, codec priorities, and authenticates to your registrar with digest credentials.
3. **Call handling** – Incoming and outbound calls create an `AudioCallback` bridge that feeds PCM frames into asyncio queues while retaining correlation IDs for monitoring.
4. **Realtime streaming** – When `OPENAI_MODE=realtime`, the agent opens a WebSocket to OpenAI, issues a `session.update` with model/voice/audio parameters, base64-encodes audio deltas, and commits the buffer once a turn completes.
5. **Legacy streaming** – In legacy mode the agent forwards raw PCM frames to `/v1/audio/speech` and queues returned audio directly to the SIP leg.
6. **Metrics & logs** – The monitor records call lifecycle events, retry counters, and aggregated token usage while structured logs carry correlation IDs end-to-end.
7. **Dashboard updates** – Authenticated WebSocket subscribers receive status snapshots, call history, metrics, and log lines with automatic reconnect/backoff logic in the browser hook.
8. **Edge serving** – Nginx serves the built dashboard assets and proxies `/api`, `/ws`, `/metrics`, `/healthz`, `/login`, and `/logout` back to the monitor for a cohesive admin surface.

## Project layout
- `app/` – Backend agent, configuration loader, monitor API, and static dashboard assets.
- `web/` – React/Vite/Tailwind dashboard with hooks, components, tests, and build tooling.
- `scripts/` – Utilities such as `install_pjsua2.py` that compile pjproject and Python bindings.
- `deploy/` – Deployment assets including the Nginx reverse-proxy configuration used in container builds.
- `tests/` – Pytest suite covering audio pipelines, monitor routes, configuration validation, and timers.
- `Makefile` – One-liner targets for installing dependencies, linting, typing, testing, formatting, and environment validation.

## Quick start

### Requirements
- Asterisk-based PBX (e.g., FreePBX or VICIdial) with an extension dedicated to the agent.
- Docker and Docker Compose.
- OpenAI API key with access to the `gpt-realtime` model for realtime mode.

### Configure the environment
Clone the repo and copy the sample configuration:

```bash
git clone https://github.com/vaheed/sip-ai-agent.git
cd sip-ai-agent
cp env.example .env
```

Populate SIP credentials, OpenAI keys, and session preferences:

```env
# PBX
SIP_DOMAIN=pbx.example.com
SIP_USER=1001
SIP_PASS=secret

# OpenAI
OPENAI_API_KEY=sk-...
AGENT_ID=va_123456789

# Feature toggles & realtime session
ENABLE_SIP=true
ENABLE_AUDIO=true
OPENAI_MODE=realtime
OPENAI_MODEL=gpt-realtime
OPENAI_VOICE=alloy
OPENAI_TEMPERATURE=0.3
SYSTEM_PROMPT=You are a helpful voice assistant.
```

Core settings are validated on startup through a Pydantic schema, so missing or malformed values surface immediately in logs and the dashboard.

### Validate and regenerate configs
Check any `.env` file and regenerate `env.example` without touching your secrets:

```bash
python -m app.config validate --path .env
python -m app.config sample --write --path env.example
make env-validate    # wraps the same validator
make env-sample
```

The CLI accepts `--include-os` to merge process environment values during validation and prints detailed field-level errors on failure.

### Run with Docker Compose
Build and run both containers locally:

```bash
docker compose up --build
```

Or pull the published images:

```bash
docker compose -f docker-compose.production.yml up -d
```

`sip-agent` exposes UDP 5060 for SIP and 16000–16100 for RTP, while `web` serves the dashboard on TCP 8080 and proxies control-plane endpoints back to the agent.

### Run locally (optional)
For direct execution or CI, install dependencies and compile PJSIP bindings:

```bash
pip install -r requirements.txt
python scripts/install_pjsua2.py
# or
make install
```

The helper downloads pjproject 2.12, builds shared libraries, and installs the `pjsua2` module—mirroring the container build sequence.

### Access the dashboard
Browse to `http://<docker-host>:8080` and log in with `MONITOR_ADMIN_USERNAME` / `MONITOR_ADMIN_PASSWORD` (defaults to `admin` / `admin`). Update SIP, OpenAI, and feature settings directly in the `.env` file and restart the containers to apply changes.

## Monitoring & observability
The dashboard summarises SIP registration state, active calls, token usage, realtime channel health, and live logs, with dark/light theme support and auto-refreshing WebSocket data feeds.

The browser hook handles authentication failures, reconnect backoff, and incremental log streaming so operators can keep a single page open during deployments.

Configuration validation runs on startup and via the CLI helpers so invalid `.env` values surface immediately in logs and the dashboard health summaries.

Structured JSON logs (with correlation IDs) and the metrics endpoint expose retry counters, call durations, token usage, and realtime WebSocket health. Pull `/metrics` in JSON for dashboards or quick `curl | jq` inspection during incidents.

## Configuration reference

### Core credentials & AI session
| Key(s) | Default | Notes |
| --- | --- | --- |
| `SIP_DOMAIN`, `SIP_USER`, `SIP_PASS` | *(required)* | PBX account details; empty values fail validation. |
| `OPENAI_API_KEY`, `AGENT_ID` | *(required)* | API key and assistant ID used for all conversations. |
| `ENABLE_SIP` | `true` | Disable to run only the dashboard/monitor. |
| `ENABLE_AUDIO` | `true` | Disable to keep SIP signalling without bridging RTP. |
| `OPENAI_MODE` | `legacy` | Set `realtime` to enable ultra-low-latency streaming. |
| `OPENAI_MODEL` | `gpt-realtime` | Model advertised in the realtime session update. |
| `OPENAI_VOICE` | `alloy` | Voice name for realtime synthesis. |
| `OPENAI_TEMPERATURE` | `0.3` | Sampling temperature (0–2). |
| `SYSTEM_PROMPT` | `You are a helpful voice assistant.` | Sent in each realtime session update. |

Defaults originate from `env.example` and are enforced via the `Settings` dataclass.

### Audio pipeline
| Key | Default | Description |
| --- | --- | --- |
| `SIP_TRANSPORT_PORT` | `5060` | Local UDP port for SIP signalling. |
| `SIP_PREFERRED_CODECS` | `PCMU,PCMA,opus` | Priority-ordered codec list; unavailable codecs are ignored. |
| `SIP_JB_MIN` / `SIP_JB_MAX` / `SIP_JB_MAX_PRE` | `0` | Jitter buffer bounds to trade latency for resilience. |

These values adjust PJSIP media configuration before registration.

### NAT traversal & media security
| Key | Default | Description |
| --- | --- | --- |
| `SIP_ENABLE_ICE` | `false` | Enable ICE negotiation for symmetric NAT environments. |
| `SIP_ENABLE_TURN` | `false` | Relay RTP via TURN when direct paths fail. |
| `SIP_STUN_SERVER` | *(blank)* | Optional STUN URI (e.g., `stun:stun.l.google.com:19302`). |
| `SIP_TURN_SERVER`, `SIP_TURN_USER`, `SIP_TURN_PASS` | *(blank)* | TURN relay credentials. |
| `SIP_ENABLE_SRTP` | `false` | Negotiate SRTP; combine with `SIP_SRTP_OPTIONAL=false` to enforce encrypted media only. |

The agent applies these during account creation, mapping to PJSIP NAT and SRTP configuration structures.

### Retry & resilience
| Key | Default | Description |
| --- | --- | --- |
| `SIP_REG_RETRY_BASE` / `SIP_REG_RETRY_MAX` | `2.0` / `60.0` | Exponential backoff window for registration retries. |
| `SIP_INVITE_RETRY_BASE` / `SIP_INVITE_RETRY_MAX` | `1.0` / `30.0` | Retry cadence for outbound INVITEs on 4xx/5xx. |
| `SIP_INVITE_MAX_ATTEMPTS` | `5` | Maximum INVITE attempts before marking the call failed. |

Retry scheduling emits log events and increments metrics counters for visibility.

### Monitor authentication
Monitor defaults can be overridden via environment variables:

- `MONITOR_ADMIN_USERNAME` / `MONITOR_ADMIN_PASSWORD` – Admin credentials (default `admin` / `admin`).
- `MONITOR_SESSION_COOKIE` – Cookie name for sessions (default `monitor_session`).
- `MONITOR_SESSION_TTL` – Session lifetime in seconds (default 86400).

## Integration guides

### FreePBX
1. Create a PJSIP extension matching `SIP_USER` / `SIP_PASS`.
2. Open UDP 16000–16100 on your firewall for RTP media.
3. Add a dialplan entry (e.g., extension `5000`) that dials `PJSIP/${SIP_USER}@${SIP_DOMAIN}` and reload the dialplan. Dial `5000` from any internal phone to reach the assistant.

### VICIdial
1. Create a campaign or in-group that dials an internal extension (e.g., `5000`).
2. Add a matching dialplan stanza that calls `PJSIP/${SIP_USER}@${SIP_DOMAIN}`.
3. Route transfers or manual dials to that extension; the agent behaves like any SIP endpoint registered to the PBX.

## Operations & troubleshooting
- **SIP failure codes** – Map common responses (401, 403, 404/484, 415/488, 480/503, 500/502) to corrective actions using the dashboard log stream and metrics counters such as `register_retries` and `invite_retries`.
- **Firewall planning** – Open UDP 5060 (or your configured port) plus 16000–16100 for RTP; disable SIP ALG where possible to avoid SDP rewriting.
- **NAT & SRTP** – Toggle ICE, TURN, STUN, and SRTP entirely through environment variables—no code changes required.
- **Metrics & logs** – Use `/metrics` for machine-readable health snapshots and rely on correlation IDs to trace a call across SIP events, WebSocket activity, and audio bridge state changes.

## Development workflow
- Run `make dev`, `make lint`, `make type`, `make test`, and `make format` to install toolchains, run Ruff, MyPy, Pytest, and formatting respectively; CI mirrors these commands.
- The Python test suite covers realtime/legacy audio loops, monitor routes, configuration validation, and timer utilities—extend it when introducing new behaviours.
- Frontend development lives under `web/`: `npm install`, `npm run dev`, and `npm run build` leverage Vite, Tailwind, ESLint, Vitest, and Playwright tooling defined in `package.json`.
- Contribution guidelines, coding standards, and review expectations are documented in `CONTRIBUTING.md`.

## CLI utilities & helper scripts
- `python -m app.config validate --path .env [--include-os]` – Validate environment files against the schema with detailed field errors.
- `python -m app.config sample --write --path env.example` – Regenerate the canonical sample file (printable to stdout).
- `make env-validate` / `make env-sample` – Convenience wrappers around the same CLI.
- `python scripts/install_pjsua2.py [--prefix PATH] [--force]` – Download and build pjproject with shared libs and the `pjsua2` Python module (skips rebuilding if already installed unless `--force` is provided).

## Ports & deployment topology
- `sip-agent` container: UDP 5060 for SIP, UDP 16000–16100 for RTP, TCP 8080 for the monitor API/WebSocket.
- `web` container: TCP 8080 (host) serving the compiled dashboard via Nginx, proxying control-plane traffic to `sip-agent`. Production compose files pull the published images by default but respect `SIP_AGENT_IMAGE` / `SIP_DASHBOARD_IMAGE` overrides.
- Nginx forwards `/api/`, `/ws/`, `/metrics`, `/healthz`, `/login`, `/logout`, and `/dashboard` routes to the monitor while serving static assets from `/usr/share/nginx/html`.

## License
Released under the GNU General Public License v3.0.

```

_Source notes:_ Key behaviours—such as SIP registration, realtime bridging, environment validation, monitor routes, dashboard streaming, and deployment topology—are documented directly from `app/agent.py`, `app/config.py`, `app/monitor.py`, the React dashboard (`web/src`), the helper scripts, and deployment manifests cited above.
