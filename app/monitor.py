#!/usr/bin/env python3
"""Monitoring server powered by FastAPI with websocket streaming."""

from __future__ import annotations

import asyncio
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, cast

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

try:
    from .config import (
        ConfigurationError,
        get_settings,
        merge_env,
        read_env_file,
        validate_env_map,
        write_env_file,
    )
except ImportError as exc:  # pragma: no cover - script execution fallback
    if "attempted relative import" in str(exc) or getattr(exc, "name", "") in {
        "config",
        "app.config",
    }:
        from config import (  # type: ignore
            ConfigurationError,
            get_settings,
            merge_env,
            read_env_file,
            validate_env_map,
            write_env_file,
        )
    else:  # pragma: no cover - surface configuration import issues
        raise

try:
    from .observability import (
        correlation_scope,
        generate_correlation_id,
        get_logger,
        metrics,
    )
except ImportError:  # pragma: no cover - script execution fallback
    from observability import (  # type: ignore
        correlation_scope,
        generate_correlation_id,
        get_logger,
        metrics,
    )


def load_config() -> dict:
    """Return the current configuration as a mapping of strings."""

    try:
        return get_settings().as_env()
    except ConfigurationError:
        return read_env_file()


def save_config(new_config: dict) -> None:
    """Validate and persist configuration updates to the ``.env`` file."""

    existing = read_env_file()
    merged = merge_env(existing, new_config)
    validate_env_map(merged, include_os_environ=False)
    write_env_file(merged)
    get_settings.cache_clear()


class Monitor:
    """Expose agent state over HTTP, JSON and websocket APIs."""

    CONFIG_KEYS = [
        "SIP_DOMAIN",
        "SIP_USER",
        "SIP_PASS",
        "OPENAI_API_KEY",
        "AGENT_ID",
        "ENABLE_SIP",
        "ENABLE_AUDIO",
        "OPENAI_MODE",
        "OPENAI_MODEL",
        "OPENAI_VOICE",
        "OPENAI_TEMPERATURE",
        "SYSTEM_PROMPT",
        "SIP_TRANSPORT_PORT",
        "SIP_JB_MIN",
        "SIP_JB_MAX",
        "SIP_JB_MAX_PRE",
        "SIP_ENABLE_ICE",
        "SIP_ENABLE_TURN",
        "SIP_STUN_SERVER",
        "SIP_TURN_SERVER",
        "SIP_TURN_USER",
        "SIP_TURN_PASS",
        "SIP_ENABLE_SRTP",
        "SIP_SRTP_OPTIONAL",
        "SIP_PREFERRED_CODECS",
        "SIP_REG_RETRY_BASE",
        "SIP_REG_RETRY_MAX",
        "SIP_INVITE_RETRY_BASE",
        "SIP_INVITE_RETRY_MAX",
        "SIP_INVITE_MAX_ATTEMPTS",
    ]

    def __init__(self) -> None:
        self.app = FastAPI(title="SIP AI Agent Monitor")
        self.logger = get_logger(__name__)

        dashboard_dir_env = os.getenv("MONITOR_DASHBOARD_DIR")
        self.dashboard_dir: Path
        if dashboard_dir_env:
            self.dashboard_dir = Path(dashboard_dir_env).expanduser().resolve()
        else:
            default_candidates = [
                Path(__file__).resolve().parent / "static" / "dashboard",
                Path(__file__).resolve().parent.parent / "web" / "dist",
            ]
            for candidate in default_candidates:
                if candidate.exists():
                    self.dashboard_dir = candidate.resolve()
                    break
            else:
                self.dashboard_dir = default_candidates[0].resolve()

        # Agent state
        self.sip_registered = False
        self.active_calls: List[str] = []
        self.call_history: List[Dict[str, Any]] = []
        self.api_tokens_used = 0
        self.logs: List[str] = []
        self.max_logs = 100
        self._call_context: Dict[str, Dict[str, Any]] = {}
        self.realtime_ws_state: str = "unknown"
        self.realtime_ws_detail: Optional[str] = None
        self.realtime_ws_last_event: Optional[float] = None

        # Authentication/session management
        self.admin_username = os.getenv("MONITOR_ADMIN_USERNAME", "admin")
        self.admin_password = os.getenv("MONITOR_ADMIN_PASSWORD", "admin")
        self.session_cookie = os.getenv("MONITOR_SESSION_COOKIE", "monitor_session")
        self.session_ttl = int(os.getenv("MONITOR_SESSION_TTL", "86400"))
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_lock = threading.Lock()

        # Websocket broadcasting
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._event_subscribers: Set[asyncio.Queue[Dict[str, Any]]] = set()
        self._event_lock = threading.Lock()

        self._server_thread: Optional[threading.Thread] = None

        self.setup_routes()

    # ------------------------------------------------------------------
    # Session helpers

    def _verify_credentials(self, username: str, password: str) -> bool:
        return bool(
            hmac.compare_digest(username.strip(), self.admin_username)
            and hmac.compare_digest(password, self.admin_password)
        )

    def _create_session(self, username: str) -> str:
        session_id = secrets.token_urlsafe(32)
        expires_at = time.time() + self.session_ttl
        with self._session_lock:
            self._sessions[session_id] = {"username": username, "expires_at": expires_at}
        return session_id

    def _get_session(self, session_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not session_id:
            return None
        with self._session_lock:
            data = self._sessions.get(session_id)
            if not data:
                return None
            if data["expires_at"] < time.time():
                self._sessions.pop(session_id, None)
                return None
            data["expires_at"] = time.time() + self.session_ttl
            return data

    def _clear_session(self, session_id: Optional[str]) -> None:
        if not session_id:
            return
        with self._session_lock:
            self._sessions.pop(session_id, None)

    # ------------------------------------------------------------------
    # Broadcasting helpers

    def _status_payload(self) -> Dict[str, Any]:
        return {
            "sip_registered": self.sip_registered,
            "active_calls": list(self.active_calls),
            "api_tokens_used": self.api_tokens_used,
            "realtime_ws_state": self.realtime_ws_state,
            "realtime_ws_detail": self.realtime_ws_detail,
        }

    def _call_history_payload(self) -> List[Dict[str, Any]]:
        return [dict(item) for item in self.call_history]

    def _push_event(self, event: Dict[str, Any]) -> None:
        loop = self._loop
        if loop is None:
            return

        async def _broadcast() -> None:
            stale: List[asyncio.Queue[Dict[str, Any]]] = []
            with self._event_lock:
                subscribers = list(self._event_subscribers)
            for queue in subscribers:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    stale.append(queue)
            if stale:
                with self._event_lock:
                    for queue in stale:
                        self._event_subscribers.discard(queue)

        asyncio.run_coroutine_threadsafe(_broadcast(), loop)

    def _emit_status_event(self) -> None:
        self._push_event({"type": "status", "payload": self._status_payload()})
        self._push_event({"type": "call_history", "payload": self._call_history_payload()})

    def _emit_metrics_event(self) -> None:
        self._push_event({"type": "metrics", "payload": metrics.snapshot()})

    # ------------------------------------------------------------------
    # Routes

    def setup_routes(self) -> None:
        @self.app.on_event("startup")
        async def _on_startup() -> None:  # pragma: no cover - async event loop binding
            self._loop = asyncio.get_event_loop()

        def _admin_dependency(request: Request) -> Dict[str, Any]:
            session = self._get_session(request.cookies.get(self.session_cookie))
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            return session

        def _render_login(message: str = "", next_path: str = "/dashboard") -> HTMLResponse:
            alert = f"<p style='color:#F44336;'>{message}</p>" if message else ""
            return HTMLResponse(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Monitor Login</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 0; padding: 40px; background: #f5f5f5; }}
                        .card {{ max-width: 400px; margin: auto; background: #fff; padding: 30px; border-radius: 6px;
                                 box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                        label {{ display: block; margin-bottom: 6px; font-weight: bold; }}
                        input[type="text"], input[type="password"] {{ width: 100%; padding: 10px; margin-bottom: 15px;
                            border: 1px solid #ccc; border-radius: 4px; }}
                        button {{ width: 100%; padding: 10px; background-color: #4CAF50; color: white;
                            border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
                        button:hover {{ background-color: #45a049; }}
                        .footer {{ text-align: center; margin-top: 20px; color: #666; }}
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h1>Admin Login</h1>
                        {alert}
                        <form method="post" action="/login">
                            <input type="hidden" name="next" value="{next_path}">
                            <label for="username">Username</label>
                            <input type="text" id="username" name="username" required>
                            <label for="password">Password</label>
                            <input type="password" id="password" name="password" required>
                            <button type="submit">Sign in</button>
                        </form>
                    </div>
                    <div class="footer">SIP AI Agent Monitor</div>
                </body>
                </html>
                """,
            )

        @self.app.get("/", response_class=HTMLResponse)
        async def index() -> str:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>SIP AI Agent Monitor</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
                    .container { max-width: 960px; margin: 0 auto; }
                    .card { background: #f9f9f9; border-radius: 5px; padding: 15px; margin-bottom: 20px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .status { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
                    .status.green { background-color: #4CAF50; }
                    .status.red { background-color: #F44336; }
                    .logs { background: #272822; color: #f8f8f2; padding: 10px; border-radius: 5px; height: 300px;
                            overflow-y: auto; font-family: monospace; }
                    h1, h2 { color: #333; }
                    .actions { margin-bottom: 20px; }
                    a.button { padding: 10px 20px; background: #4CAF50; color: #fff; border-radius: 3px;
                               text-decoration: none; }
                    a.button:hover { background: #45a049; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>SIP AI Agent Monitor</h1>
                    <div class="actions">
                        <a class="button" href="/dashboard">Open Dashboard</a>
                        <a class="button" href="/login">Admin Login</a>
                    </div>
                    <div class="card">
                        <h2>About</h2>
                        <p>The monitoring dashboard requires administrator authentication. Use the login link above to
                           access configuration and live updates.</p>
                    </div>
                </div>
            </body>
            </html>
            """

        @self.app.get("/login", response_class=HTMLResponse)
        async def login_page(request: Request) -> HTMLResponse:
            next_path = request.query_params.get("next", "/dashboard")
            return _render_login(next_path=next_path)

        @self.app.post("/login")
        async def login(request: Request) -> Response:
            content_type = request.headers.get("content-type", "")
            next_path = "/dashboard"
            if content_type.startswith("application/json"):
                payload = await request.json()
                username = str(payload.get("username", ""))
                password = str(payload.get("password", ""))
                next_path = str(payload.get("next", next_path)) or "/dashboard"
            else:
                form = await request.form()
                username = str(form.get("username", ""))
                password = str(form.get("password", ""))
                next_path = str(form.get("next", next_path)) or "/dashboard"

            if self._verify_credentials(username, password):
                session_id = self._create_session(username)
                response: Response
                if content_type.startswith("application/json"):
                    response = JSONResponse({"success": True, "redirect": next_path})
                else:
                    response = RedirectResponse(next_path, status_code=status.HTTP_303_SEE_OTHER)
                response.set_cookie(
                    self.session_cookie,
                    session_id,
                    httponly=True,
                    max_age=self.session_ttl,
                    samesite="lax",
                )
                self.add_log("Administrator logged in", event="admin_login", username=username)
                return response

            if content_type.startswith("application/json"):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            self.add_log(
                "Failed login attempt",
                level="warning",
                event="admin_login_failed",
                username=username,
            )
            return _render_login("Invalid username or password", next_path=next_path)

        @self.app.post("/logout")
        async def logout(request: Request) -> Response:
            session_id = request.cookies.get(self.session_cookie)
            username = None
            if session_id:
                session = self._get_session(session_id)
                if session:
                    username = session.get("username")
            self._clear_session(session_id)
            response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
            response.delete_cookie(self.session_cookie)
            if username:
                self.add_log("Administrator logged out", event="admin_logout", username=username)
            return response

        @self.app.get("/dashboard", response_class=HTMLResponse)
        @self.app.get("/dashboard/", response_class=HTMLResponse)
        async def dashboard(request: Request) -> Response:
            if not self._get_session(request.cookies.get(self.session_cookie)):
                return RedirectResponse(
                    f"/login?next={request.url.path}",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            index_file = self.dashboard_dir / "index.html"
            if index_file.exists():
                try:
                    html = index_file.read_text(encoding="utf-8")
                except OSError as exc:  # pragma: no cover - filesystem failure
                    self.logger.error("Unable to read dashboard index", extra={"error": str(exc)})
                else:
                    return HTMLResponse(html)

            message = """<!DOCTYPE html>
<html>
<head><title>Dashboard assets missing</title></head>
<body>
<h1>Dashboard assets unavailable</h1>
<p>The React dashboard has not been built. Run <code>npm run build</code> inside the <code>web/</code> directory to generate static assets.</p>
</body>
</html>"""
            return HTMLResponse(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

        @self.app.get("/dashboard/{asset_path:path}")
        async def dashboard_assets(asset_path: str, request: Request) -> Response:
            if not self._get_session(request.cookies.get(self.session_cookie)):
                return RedirectResponse(
                    f"/login?next={request.url.path}",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            safe_root = self.dashboard_dir
            file_path = (safe_root / asset_path).resolve()
            try:
                file_path.relative_to(safe_root)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

            if not file_path.is_file():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

            return FileResponse(file_path)

        @self.app.post("/api/update_config")
        async def api_update_config(
            request: Request,
            session: Dict[str, Any] = Depends(_admin_dependency),
        ) -> JSONResponse:
            del session
            try:
                new_config: Dict[str, str] = {}
                content_type = request.headers.get("content-type", "")
                if content_type.startswith("application/json"):
                    incoming = await request.json()
                    for key in Monitor.CONFIG_KEYS:
                        if key in incoming:
                            new_config[key] = str(incoming[key])
                else:
                    form = await request.form()
                    for key in Monitor.CONFIG_KEYS:
                        value = form.get(key)
                        if value is not None:
                            new_config[key] = str(value)
                if new_config:
                    save_config(new_config)
                    self.add_log(
                        "Configuration updated",
                        event="configuration_updated",
                        keys=list(new_config.keys()),
                    )
                return JSONResponse({"success": True})
            except ConfigurationError as err:
                self.add_log(
                    f"Configuration validation error: {err}",
                    level="error",
                    event="configuration_error",
                )
                return JSONResponse(
                    {
                        "success": False,
                        "error": str(err),
                        "details": err.details,
                    },
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                self.add_log(f"Error updating config: {exc}")
                return JSONResponse(
                    {"success": False, "error": str(exc)},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        @self.app.get("/api/call_history")
        async def api_call_history(
            session: Dict[str, Any] = Depends(_admin_dependency),
        ) -> List[Dict[str, Any]]:
            del session
            return self._call_history_payload()

        @self.app.get("/api/status")
        async def api_status(
            session: Dict[str, Any] = Depends(_admin_dependency),
        ) -> Dict[str, Any]:
            del session
            return self._status_payload()

        @self.app.get("/api/logs")
        async def api_logs(
            session: Dict[str, Any] = Depends(_admin_dependency),
        ) -> Dict[str, Any]:
            del session
            return {"logs": list(self.logs)}

        @self.app.get("/api/config")
        async def api_config(
            session: Dict[str, Any] = Depends(_admin_dependency),
        ) -> Dict[str, str]:
            del session
            config_map = load_config()
            response: Dict[str, str] = {}
            for key in Monitor.CONFIG_KEYS:
                value = config_map.get(key)
                response[key] = "" if value is None else str(value)
            return response

        @self.app.websocket("/ws/events")
        async def events_websocket(websocket: WebSocket) -> None:
            session = self._get_session(websocket.cookies.get(self.session_cookie))
            if not session:
                await websocket.close(code=4401)
                return
            await websocket.accept()

            queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=200)
            with self._event_lock:
                self._event_subscribers.add(queue)

            try:
                await websocket.send_json({"type": "status", "payload": self._status_payload()})
                await websocket.send_json({"type": "call_history", "payload": self._call_history_payload()})
                await websocket.send_json({"type": "metrics", "payload": metrics.snapshot()})
                await websocket.send_json({"type": "logs", "entries": list(self.logs)})
                while True:
                    event = await queue.get()
                    await websocket.send_json(event)
            except WebSocketDisconnect:  # pragma: no cover - lifecycle behaviour
                pass
            finally:
                with self._event_lock:
                    self._event_subscribers.discard(queue)

        @self.app.get("/metrics")
        async def api_metrics() -> Dict[str, Any]:
            return metrics.snapshot()

        @self.app.get("/healthz")
        async def healthz() -> JSONResponse:
            status_payload = self.health_status()
            code = 200 if status_payload["status"] == "ok" else 503
            return JSONResponse(status_payload, status_code=code)

    # ------------------------------------------------------------------
    # Agent integration

    def update_registration(self, status: bool) -> None:
        self.sip_registered = bool(status)
        event = "Registered" if self.sip_registered else "Not Registered"
        self.add_log(
            f"SIP registration state changed: {event}",
            event="sip_registration",
            registered=self.sip_registered,
        )
        self._emit_status_event()
        self._emit_metrics_event()

    def add_call(self, call_id: str, correlation_id: Optional[str] = None) -> str:
        correlation_id = correlation_id or generate_correlation_id()
        with correlation_scope(correlation_id):
            if call_id not in self.active_calls:
                self.active_calls.append(call_id)
            start_ts = time.time()
            self._call_context[call_id] = {
                "correlation_id": correlation_id,
                "start": start_ts,
            }
            self.call_history.append(
                {
                    "call_id": call_id,
                    "start": start_ts,
                    "end": None,
                    "correlation_id": correlation_id,
                }
            )
            metrics.call_started(call_id, correlation_id)
            self.add_log(
                f"New call: {call_id}",
                event="call_started",
                call_id=call_id,
            )
        self._emit_status_event()
        self._emit_metrics_event()
        return correlation_id

    def remove_call(self, call_id: str) -> None:
        context = self._call_context.get(call_id, {})
        correlation_id = cast(Optional[str], context.get("correlation_id"))
        with correlation_scope(correlation_id):
            if call_id in self.active_calls:
                self.active_calls.remove(call_id)

            duration = None
            for item in reversed(self.call_history):
                if item["call_id"] == call_id and item["end"] is None:
                    item["end"] = time.time()
                    duration = item["end"] - item["start"]
                    break

            metrics_duration = metrics.call_ended(call_id)
            if duration is None:
                duration = metrics_duration

            if call_id in self._call_context:
                self._call_context.pop(call_id, None)

            log_fields: Dict[str, Any] = {"event": "call_ended", "call_id": call_id}
            if duration is not None:
                log_fields["duration_seconds"] = duration
            self.add_log(f"Call ended: {call_id}", **log_fields)
        self._emit_status_event()
        self._emit_metrics_event()

    def update_tokens(self, tokens: int, call_id: Optional[str] = None) -> None:
        context = self._call_context.get(call_id) if call_id else None
        correlation_id = cast(Optional[str], context.get("correlation_id")) if context else None
        with correlation_scope(correlation_id):
            self.api_tokens_used += tokens
            metrics.record_token_usage(tokens)
            log_fields: Dict[str, Any] = {
                "event": "token_usage",
                "tokens": tokens,
                "total_tokens": self.api_tokens_used,
            }
            if call_id:
                log_fields["call_id"] = call_id
            self.add_log(
                f"API tokens used: +{tokens} (Total: {self.api_tokens_used})",
                **log_fields,
            )
        self._emit_status_event()
        self._emit_metrics_event()

    def update_realtime_ws(
        self,
        healthy: bool,
        detail: Optional[str] = None,
        call_id: Optional[str] = None,
    ) -> None:
        context = self._call_context.get(call_id) if call_id else None
        correlation_id = cast(Optional[str], context.get("correlation_id")) if context else None
        with correlation_scope(correlation_id):
            self.realtime_ws_state = "healthy" if healthy else "unhealthy"
            self.realtime_ws_detail = detail
            self.realtime_ws_last_event = time.time()
            metrics.record_audio_event("realtime_ws_healthy" if healthy else "realtime_ws_unhealthy")
            log_fields: Dict[str, Any] = {
                "event": "realtime_ws",
                "healthy": healthy,
            }
            if call_id:
                log_fields["call_id"] = call_id
            if detail:
                log_fields["detail"] = detail
            self.add_log("Realtime WebSocket status updated", **log_fields)
        self._emit_status_event()
        self._emit_metrics_event()

    def record_audio_event(self, name: str, call_id: Optional[str] = None, **fields: Any) -> None:
        context = self._call_context.get(call_id) if call_id else None
        correlation_id = cast(Optional[str], context.get("correlation_id")) if context else None
        with correlation_scope(correlation_id):
            metrics.record_audio_event(name)
            log_fields: Dict[str, Any] = {
                "event": "audio_pipeline",
                "audio_event": name,
            }
            if call_id:
                log_fields["call_id"] = call_id
            log_fields.update(fields)
            self.add_log(f"Audio pipeline event: {name}", **log_fields)
        self._emit_metrics_event()

    def add_log(self, message: str, level: str = "info", **fields: Any) -> None:
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message, extra=fields)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        level_upper = level.upper()
        log_entry = f"[{timestamp}] [{level_upper}] {message}"
        if fields:
            try:
                context_json = json.dumps(fields, default=str, sort_keys=True)
            except TypeError:
                context_json = json.dumps({k: str(v) for k, v in fields.items()}, sort_keys=True)
            log_entry = f"{log_entry} {context_json}"
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs :]
        self._push_event({"type": "log", "entry": log_entry})

    def health_status(self) -> Dict[str, Optional[object]]:
        healthy = self.sip_registered and self.realtime_ws_state != "unhealthy"
        return {
            "status": "ok" if healthy else "degraded",
            "sip_registered": self.sip_registered,
            "realtime_ws_state": self.realtime_ws_state,
            "realtime_ws_detail": self.realtime_ws_detail,
            "active_calls": len(self.active_calls),
            "last_ws_event_ts": self.realtime_ws_last_event,
        }

    def start(self) -> None:
        if self._server_thread and self._server_thread.is_alive():
            return
        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()
        self.add_log("Monitoring server started on port 8080", event="monitor_started")

    def _run_server(self) -> None:  # pragma: no cover - network server loop
        import logging

        import uvicorn

        logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
        logging.getLogger("uvicorn.access").setLevel(logging.ERROR)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=8080,
            log_level="error",
            lifespan="on",
        )
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())


monitor = Monitor()
