#!/usr/bin/env python3
import os
import time
import threading
from flask import Flask, jsonify, render_template_string

class Monitor:
    def __init__(self):
        self.app = Flask(__name__)
        self.sip_registered = False
        self.active_calls = []
        self.api_tokens_used = 0
        self.logs = []
        self.max_logs = 100
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string('''
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
            ''', sip_registered=self.sip_registered, active_calls=self.active_calls, 
                 api_tokens_used=self.api_tokens_used, logs=self.logs)
        
        @self.app.route('/api/status')
        def api_status():
            return jsonify({
                'sip_registered': self.sip_registered,
                'active_calls': self.active_calls,
                'api_tokens_used': self.api_tokens_used
            })
        
        @self.app.route('/api/logs')
        def api_logs():
            return jsonify({
                'logs': self.logs
            })
    
    def update_registration(self, status):
        self.sip_registered = status
        self.add_log(f"SIP Registration: {'Registered' if status else 'Not Registered'}")
    
    def add_call(self, call_id):
        if call_id not in self.active_calls:
            self.active_calls.append(call_id)
            self.add_log(f"New call: {call_id}")
    
    def remove_call(self, call_id):
        if call_id in self.active_calls:
            self.active_calls.remove(call_id)
            self.add_log(f"Call ended: {call_id}")
    
    def update_tokens(self, tokens):
        self.api_tokens_used += tokens
        self.add_log(f"API tokens used: +{tokens} (Total: {self.api_tokens_used})")
    
    def add_log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)  # Also print to console
        
        # Keep logs at a reasonable size
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
    
    def start(self):
        # Start Flask in a separate thread
        threading.Thread(target=self._run_server, daemon=True).start()
        self.add_log("Monitoring server started on port 8080")
    
    def _run_server(self):
        self.app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

# Singleton instance
monitor = Monitor()
