#!/usr/bin/env python3
# import asyncio  # unused
import os
import threading
import time

from flask import Flask, jsonify, render_template_string, request

from config import get_settings
from health import HealthStatus, get_health_monitor
from logging_config import generate_correlation_id, get_logger
from metrics import get_metrics


def _env_path():
    """
    Return the absolute path to the .env file located two directories above
    this monitor module. This function assumes the project structure of
    /project/sip-ai-agent-main/app/monitor.py and returns
    /project/sip-ai-agent-main/.env. Modify this logic if the repository
    layout changes.
    """
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
    )


def load_config() -> dict:
    """
    Load key/value pairs from the project's .env file.

    The .env file stores configuration values used by the SIP agent. Lines
    starting with '#' are treated as comments and ignored. Values are
    returned as strings. If the file does not exist, an empty dict is
    returned. Unknown whitespace around keys/values is stripped.
    """
    config = {}
    env_path = _env_path()
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
        except Exception:  # nosec B110
            # Silently ignore read errors; caller can handle missing keys
            pass
    return config


def save_config(new_config: dict) -> None:
    """
    Persist updated configuration values to the project's .env file.

    Any keys provided in ``new_config`` will override existing values. Keys
    not present in ``new_config`` are preserved. The resulting file is
    written back to disk as simple ``KEY=value`` lines. Comments and
    ordering from the original file are not preserved.

    :param new_config: mapping of environment variable names to new values
    """
    env_path = _env_path()
    # Start with existing config
    config = load_config()
    # Override with new values (cast everything to string)
    for k, v in new_config.items():
        config[k] = str(v)
    # Write back
    lines = [f"{key}={value}" for key, value in config.items()]
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception:
        # If we cannot write the env file, surface an error to the caller
        raise


class Monitor:
    """
    Enhanced monitor with comprehensive observability, health checks, and metrics.

    This monitor tracks SIP registration state, active calls, token usage, logs,
    and provides health monitoring with structured logging and Prometheus metrics.
    """

    # Keys presented on the configuration dashboard. Order matters for
    # rendering. Feel free to extend this list with additional environment
    # variables that should be editable through the UI.
    CONFIG_KEYS = [
        "SIP_DOMAIN",
        "SIP_USER",
        "SIP_PASS",
        "OPENAI_API_KEY",
        "AGENT_ID",
        "OPENAI_MODE",
        "OPENAI_MODEL",
        "OPENAI_VOICE",
        "OPENAI_TEMPERATURE",
        "SYSTEM_PROMPT",
        "SIP_SRTP_ENABLED",
        "SIP_JITTER_BUFFER_SIZE",
        "AUDIO_BACKPRESSURE_THRESHOLD",
        "SIP_REGISTRATION_RETRY_MAX",
        "SIP_REGISTRATION_RETRY_BACKOFF",
    ]

    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("monitor")
        self.metrics = get_metrics()
        self.health_monitor = get_health_monitor()

        self.app = Flask(__name__)
        self.sip_registered = False
        self.active_calls = []
        self.call_history = []  # list of dicts with call_id, start, end
        self.api_tokens_used = 0
        self.logs = []
        self.max_logs = self.settings.monitor_max_logs
        self.setup_routes()

    def setup_routes(self):
        @self.app.route("/")
        def index():
            return render_template_string(
                """
            <!DOCTYPE html>
            <html>
            <head>
                <title>SIP AI Agent Monitor</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .card { background: #f9f9f9; border-radius: 5px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .status { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
                    .status.green { background-color: #4CAF50; }
                    .status.red { background-color: #F44336; }
                    .logs { background: #272822; color: #f8f8f2; padding: 10px; border-radius: 5px; height: 300px; overflow-y: auto; font-family: monospace; }
                    h1, h2 { color: #333; }
                    .refresh { margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>SIP AI Agent Monitor</h1>
                    <button class="refresh" onclick="location.reload()">Refresh</button>

                    <div class="card">
                        <h2>SIP Registration</h2>
                        <p>
                            <span class="status {{ 'green' if sip_registered else 'red' }}"></span>
                            {{ 'Registered' if sip_registered else 'Not Registered' }}
                        </p>
                    </div>

                    <div class="card">
                        <h2>Active Calls</h2>
                        {% if active_calls %}
                            <ul>
                            {% for call in active_calls %}
                                <li>{{ call }}</li>
                            {% endfor %}
                            </ul>
                        {% else %}
                            <p>No active calls</p>
                        {% endif %}
                    </div>

                    <div class="card">
                        <h2>API Usage</h2>
                        <p>Tokens used: {{ api_tokens_used }}</p>
                    </div>

                    <div class="card">
                        <h2>Logs</h2>
                        <div class="logs">
                            {% for log in logs %}
                                <div>{{ log }}</div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """,
                sip_registered=self.sip_registered,
                active_calls=self.active_calls,
                api_tokens_used=self.api_tokens_used,
                logs=self.logs,
            )

        @self.app.route("/dashboard", methods=["GET"])
        def dashboard():
            """
            Serve a dashboard page with real‑time status and a configuration form.

            The dashboard uses JavaScript to periodically fetch status, logs and
            call history via the API endpoints. When the user submits the form
            the configuration is saved to `.env` and the page reloads. Note that
            a restart of the container may be required for changes to take
            effect.
            """
            config = load_config()
            # build HTML form inputs for each config key
            config_fields = []
            for key in Monitor.CONFIG_KEYS:
                value = config.get(key, "")
                # Escape HTML special characters
                safe_value = (
                    str(value)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                )
                config_fields.append(
                    f'<label for="{key}">{key}</label><input type="text" id="{key}" name="{key}" value="{safe_value}" style="width:100%"/><br/>'
                )
            config_form = "\n".join(config_fields)
            return render_template_string(
                """
            <!DOCTYPE html>
            <html>
            <head>
                <title>AI Agent Dashboard</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.5; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .card { background: #f9f9f9; border-radius: 5px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                    .logs { background: #272822; color: #f8f8f2; padding: 10px; border-radius: 5px; height: 300px; overflow-y: auto; font-family: monospace; }
                    input[type="text"] { padding: 8px; margin-bottom: 10px; border-radius: 3px; border: 1px solid #ccc; }
                    button { padding: 10px 20px; background-color: #4CAF50; color: #fff; border: none; border-radius: 3px; cursor: pointer; }
                    button:hover { background-color: #45a049; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>AI Agent Dashboard</h1>
                    <div class="card">
                        <h2>Configuration</h2>
                        <form id="configForm" method="post" action="/api/update_config">
                            """
                + config_form
                + """
                            <button type="submit">Save</button>
                        </form>
                        <p><small>After saving, restart the container to apply changes.</small></p>
                    </div>
                    <div class="card">
                        <h2>Status</h2>
                        <p id="registrationStatus">Loading...</p>
                        <p id="activeCalls">Loading...</p>
                        <p id="tokenUsage">Loading...</p>
                    </div>
                    <div class="card">
                        <h2>Call History</h2>
                        <table id="callHistoryTable">
                            <thead><tr><th>Call ID</th><th>Start</th><th>End</th><th>Duration</th></tr></thead>
                            <tbody></tbody>
                        </table>
                    </div>
                    <div class="card">
                        <h2>Logs</h2>
                        <div class="logs" id="logContainer"></div>
                    </div>
                </div>
                <script>
                async function fetchData() {
                    try {
                        const [statusRes, logsRes, historyRes] = await Promise.all([
                            fetch('/api/status'),
                            fetch('/api/logs'),
                            fetch('/api/call_history')
                        ]);
                        const status = await statusRes.json();
                        const logsData = await logsRes.json();
                        const history = await historyRes.json();
                        // Update status
                        document.getElementById('registrationStatus').textContent = status.sip_registered ? 'SIP Registered' : 'SIP Not Registered';
                        document.getElementById('activeCalls').textContent = 'Active calls: ' + (status.active_calls.length > 0 ? status.active_calls.join(', ') : 'None');
                        document.getElementById('tokenUsage').textContent = 'Tokens used: ' + status.api_tokens_used;
                        // Update logs
                        const logContainer = document.getElementById('logContainer');
                        logContainer.innerHTML = logsData.logs.map(l => '<div>' + l + '</div>').join('');
                        logContainer.scrollTop = logContainer.scrollHeight;
                        // Update call history
                        const tbody = document.querySelector('#callHistoryTable tbody');
                        tbody.innerHTML = '';
                        history.forEach(item => {
                            const start = new Date(item.start * 1000).toLocaleString();
                            const end = item.end ? new Date(item.end * 1000).toLocaleString() : '-';
                            const duration = item.end ? ((item.end - item.start).toFixed(1) + 's') : '-';
                            const row = '<tr><td>' + item.call_id + '</td><td>' + start + '</td><td>' + end + '</td><td>' + duration + '</td></tr>';
                            tbody.innerHTML += row;
                        });
                    } catch (e) {
                        console.error('Error fetching data', e);
                    }
                }
                setInterval(fetchData, 3000);
                window.onload = fetchData;
                </script>
            </body>
            </html>
            """
            )

        @self.app.route("/api/update_config", methods=["POST"])
        def api_update_config():
            """
            Update the configuration file with values submitted from the dashboard.

            Only keys defined in CONFIG_KEYS are considered. Unknown keys are
            ignored. Returns a JSON object with a success flag.
            """
            try:
                # Prefer JSON body if sent via fetch(). Fallback to form data.
                new_config = {}
                if request.is_json:
                    incoming = request.get_json() or {}
                    for key in Monitor.CONFIG_KEYS:
                        if key in incoming:
                            new_config[key] = str(incoming[key])
                else:
                    for key in Monitor.CONFIG_KEYS:
                        val = request.form.get(key)
                        if val is not None:
                            new_config[key] = val
                if new_config:
                    save_config(new_config)
                    self.add_log(
                        f"Configuration updated: {', '.join(new_config.keys())}"
                    )
                return jsonify({"success": True})
            except Exception as e:
                self.add_log(f"Error updating config: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/call_history")
        def api_call_history():
            """
            Return the call history as JSON. Each item has call_id, start, end.
            """
            return jsonify(self.call_history)

        @self.app.route("/api/status")
        def api_status():
            return jsonify(
                {
                    "sip_registered": self.sip_registered,
                    "active_calls": self.active_calls,
                    "api_tokens_used": self.api_tokens_used,
                }
            )

        @self.app.route("/api/logs")
        def api_logs():
            return jsonify({"logs": self.logs})

        @self.app.route("/healthz")
        async def health_check():
            """Health check endpoint for Kubernetes and monitoring systems."""
            try:
                report = await self.health_monitor.run_health_checks()

                # Return appropriate HTTP status code based on health
                status_code = 200
                if report.overall_status == HealthStatus.CRITICAL:
                    status_code = 503
                elif report.overall_status == HealthStatus.UNHEALTHY:
                    status_code = 503
                elif report.overall_status == HealthStatus.DEGRADED:
                    status_code = 200  # Degraded but still operational

                return (
                    jsonify(
                        {
                            "status": report.overall_status.value,
                            "timestamp": report.timestamp,
                            "uptime_seconds": report.uptime_seconds,
                            "checks": [
                                {
                                    "name": check.name,
                                    "status": check.status.value,
                                    "message": check.message,
                                    "duration_ms": check.duration_ms,
                                }
                                for check in report.checks
                            ],
                        }
                    ),
                    status_code,
                )

            except Exception as e:
                self.logger.error("Health check failed", error=str(e))
                return (
                    jsonify(
                        {
                            "status": "critical",
                            "error": str(e),
                            "timestamp": time.time(),
                        }
                    ),
                    503,
                )

        @self.app.route("/metrics")
        def metrics_endpoint():
            """Prometheus metrics endpoint."""
            if not self.settings.metrics_enabled:
                return "Metrics disabled", 404

            from flask import Response
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

            data = generate_latest()
            return Response(data, mimetype=CONTENT_TYPE_LATEST)

        @self.app.route("/api/metrics/summary")
        def metrics_summary():
            """Get a summary of key metrics."""
            return jsonify(
                {
                    "active_calls": self.metrics.get_active_calls_count(),
                    "sip_registered": self.sip_registered,
                    "api_tokens_used": self.api_tokens_used,
                    "uptime_seconds": self.health_monitor.get_uptime(),
                    "system_metrics": self.health_monitor.get_system_metrics(),
                }
            )

    def update_registration(self, status):
        self.sip_registered = status
        self.metrics.update_sip_registration_status(
            self.settings.sip_domain, self.settings.sip_user, status
        )
        self.add_log(
            f"SIP Registration: {'Registered' if status else 'Not Registered'}"
        )
        self.logger.info("SIP registration status updated", registered=status)

    def add_call(self, call_id):
        correlation_id = generate_correlation_id()
        if call_id not in self.active_calls:
            self.active_calls.append(call_id)
            # Record call start time
            self.call_history.append(
                {"call_id": call_id, "start": time.time(), "end": None}
            )
            self.add_log(f"New call: {call_id}")
            self.logger.info(
                "New call added", call_id=call_id, correlation_id=correlation_id
            )
            self.metrics.record_call_start(str(call_id))

    def remove_call(self, call_id):
        if call_id in self.active_calls:
            self.active_calls.remove(call_id)
            # Record call end time
            for item in self.call_history:
                if item["call_id"] == call_id and item["end"] is None:
                    item["end"] = time.time()
                    break
            self.add_log(f"Call ended: {call_id}")
            self.logger.info("Call removed", call_id=call_id)
            self.metrics.record_call_end(str(call_id))

    def update_tokens(self, tokens):
        self.api_tokens_used += tokens
        self.add_log(f"API tokens used: +{tokens} (Total: {self.api_tokens_used})")
        self.logger.info(
            "Token usage updated",
            tokens_added=tokens,
            total_tokens=self.api_tokens_used,
        )

    def add_log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)  # Also print to console

        # Keep logs at a reasonable size
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs :]

    def start(self):
        # Start metrics server if enabled
        if self.settings.metrics_enabled:
            self.metrics.start_metrics_server()

        # Start Flask in a separate thread
        threading.Thread(target=self._run_server, daemon=True).start()
        self.add_log(f"Monitoring server started on port {self.settings.monitor_port}")
        self.logger.info(
            "Monitor started",
            port=self.settings.monitor_port,
            metrics_enabled=self.settings.metrics_enabled,
            metrics_port=(
                self.settings.metrics_port if self.settings.metrics_enabled else None
            ),
        )

    def _run_server(self):
        # Explicitly disable Flask's logging to keep console output clean
        import logging as _logging

        log = _logging.getLogger("werkzeug")
        log.setLevel(_logging.ERROR)
        self.app.run(
            host=self.settings.monitor_host,
            port=self.settings.monitor_port,
            debug=self.settings.debug,
            use_reloader=False,
        )


# Singleton instance
monitor = Monitor()
