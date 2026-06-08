#!/usr/bin/env python3
"""Local server for splitflap-todo with REST API for Claude Desktop integration."""

import http.server
import json
import os
from datetime import datetime

PORT = 8787
DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_FILE = os.path.join(DIR, "sessions.json")
TASKS_FILE = os.path.join(DIR, "tasks.json")


def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return []


def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return []


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        # ── API: Get all tasks ──
        if self.path == "/api/tasks":
            self._json_response(load_tasks())

        # ── API: Get status summary ──
        elif self.path == "/api/status":
            tasks = load_tasks()
            total = len(tasks)
            done = [t for t in tasks if t.get("done")]
            pending = [t for t in tasks if not t.get("done")]
            nonneg_left = [t for t in pending if t.get("nonNegotiable")]
            sessions = load_sessions()
            today = datetime.now().strftime("%Y-%m-%d")
            today_session = next((s for s in sessions if s.get("date") == today), None)

            self._json_response({
                "date": today,
                "totalTasks": total,
                "completed": len(done),
                "remaining": len(pending),
                "nonNegotiablesLeft": len(nonneg_left),
                "completedTasks": [t["text"] for t in done],
                "remainingTasks": [
                    {"text": t["text"], "nonNegotiable": t.get("nonNegotiable", False)}
                    for t in pending
                ],
                "sessionSeconds": today_session.get("sessionSeconds", 0) if today_session else 0,
            })

        # ── API: Get session history ──
        elif self.path == "/api/sessions":
            self._json_response(load_sessions())

        # ── Static files (fallback) ──
        else:
            super().do_GET()

    def do_POST(self):
        # ── API: Set full task list (from markdown or JSON array) ──
        if self.path == "/api/tasks":
            body = self._read_body()

            # Accept markdown string
            if isinstance(body, dict) and "markdown" in body:
                tasks = self._parse_markdown(body["markdown"])
            # Accept JSON array of tasks
            elif isinstance(body, list):
                tasks = body
            elif isinstance(body, dict) and "tasks" in body:
                tasks = body["tasks"]
            else:
                self._json_response({"error": "Send {markdown: '...'} or {tasks: [...]}"}, 400)
                return

            # Normalize tasks
            normalized = []
            for t in tasks:
                if isinstance(t, str):
                    normalized.append({"text": t, "nonNegotiable": False, "done": False})
                elif isinstance(t, dict):
                    normalized.append({
                        "text": t.get("text", ""),
                        "nonNegotiable": t.get("nonNegotiable", False),
                        "done": t.get("done", False),
                    })
            save_tasks(normalized)
            self._json_response({"ok": True, "count": len(normalized)})

        # ── API: Add task(s) ──
        elif self.path == "/api/tasks/add":
            body = self._read_body()
            tasks = load_tasks()

            new_tasks = body if isinstance(body, list) else [body]
            for t in new_tasks:
                if isinstance(t, str):
                    text, nn = self._parse_task_line(t)
                    tasks.append({"text": text, "nonNegotiable": nn, "done": False})
                elif isinstance(t, dict):
                    tasks.append({
                        "text": t.get("text", ""),
                        "nonNegotiable": t.get("nonNegotiable", False),
                        "done": False,
                    })

            save_tasks(tasks)
            self._json_response({"ok": True, "totalTasks": len(tasks)})

        # ── API: Complete a task by text match ──
        elif self.path == "/api/tasks/complete":
            body = self._read_body()
            text = body.get("text", "").lower()
            tasks = load_tasks()
            matched = False
            for t in tasks:
                if t["text"].lower() == text and not t.get("done"):
                    t["done"] = True
                    matched = True
                    break
            if not matched:
                # Fuzzy: partial match
                for t in tasks:
                    if text in t["text"].lower() and not t.get("done"):
                        t["done"] = True
                        matched = True
                        break
            save_tasks(tasks)
            self._json_response({"ok": matched, "matched": matched})

        # ── Save session (existing endpoint) ──
        elif self.path == "/save-session":
            try:
                data = self._read_body()
                self._save_session(data)
                self._json_response({"ok": True})
            except Exception as e:
                self._json_response({"error": str(e)}, 500)

        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        # ── API: Sync tasks from browser (save current state) ──
        if self.path == "/api/tasks":
            body = self._read_body()
            tasks = body if isinstance(body, list) else body.get("tasks", [])
            save_tasks(tasks)
            self._json_response({"ok": True})
        else:
            self.send_response(404)
            self.end_headers()

    def _parse_task_line(self, raw):
        val = raw.strip()
        if val.startswith("- "):
            val = val[2:].strip()
        nn = False
        if val.startswith("**!"):
            nn = True
            val = val[3:].lstrip()
            if val.endswith("**"):
                val = val[:-2].strip()
        elif val.startswith("!"):
            nn = True
            val = val[1:].lstrip()
        return val, nn

    def _parse_markdown(self, text):
        tasks = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("- "):
                line = line[2:].strip()
            if not line:
                continue
            text_val, nn = self._parse_task_line(line)
            if text_val:
                tasks.append({"text": text_val, "nonNegotiable": nn, "done": False})
        return tasks

    def _save_session(self, data):
        sessions = load_sessions()
        date = data.get("date")
        updated = False
        for i, s in enumerate(sessions):
            if s.get("date") == date:
                sessions[i] = data
                updated = True
                break
        if not updated:
            sessions.append(data)
        sessions.sort(key=lambda s: s.get("date", ""))
        with open(SESSIONS_FILE, "w") as f:
            json.dump(sessions, f, indent=2)


if __name__ == "__main__":
    print(f"Splitflap server running at http://localhost:{PORT}")
    print(f"Tasks file: {TASKS_FILE}")
    print(f"Sessions file: {SESSIONS_FILE}")
    print()
    print("API endpoints:")
    print("  GET  /api/tasks          - Get all tasks")
    print("  GET  /api/status         - Get status summary")
    print("  GET  /api/sessions       - Get session history")
    print("  POST /api/tasks          - Set full task list")
    print("  POST /api/tasks/add      - Add task(s)")
    print("  POST /api/tasks/complete - Complete a task")
    print("  PUT  /api/tasks          - Sync task state")
    print()
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
