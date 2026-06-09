#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastmcp>=2.0.0"]
# ///
"""
MCP server for Splitflap Todo — lets Claude Desktop manage your daily task list with live sync to the physical split-flap UI.

Key feature: You no longer need to manually run `python3 server.py` first.
The MCP tools will automatically start the web backend when needed (via open_splitflap or any other tool call).

Usage from Claude:
  1. Call open_splitflap() when the user wants to see the flaps.
     → It starts the server (if necessary) + opens http://localhost:8787 in a new Chrome window.
  2. Then use set_tasks, set_tasks_markdown, add_tasks, complete_task, get_status, etc.
     The browser UI updates live.

Still supported: the static generator (generate_splitflap.py) for one-off beautiful views without any server/MCP.
"""

import json
import urllib.request
import urllib.error
import subprocess
import time
import socket
import sys
from pathlib import Path
from fastmcp import FastMCP

PROJECT_DIR = Path(__file__).parent
SERVER_SCRIPT = PROJECT_DIR / "server.py"
BASE_URL = "http://localhost:8787"


def is_server_running() -> bool:
    """Quick check if the splitflap web server is listening on 8787."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            return s.connect_ex(("127.0.0.1", 8787)) == 0
    except Exception:
        return False


def ensure_server_running() -> bool:
    """Start server.py in the background if it's not already running.
    Returns True if the server is (now) reachable.
    """
    if is_server_running():
        return True

    if not SERVER_SCRIPT.exists():
        return False

    try:
        # Launch detached so the web server keeps running independently
        subprocess.Popen(
            [sys.executable, str(SERVER_SCRIPT)],
            cwd=PROJECT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,   # detach from the MCP process group (Unix)
        )
    except Exception:
        return False

    # Wait for the port to come up (usually very fast)
    for _ in range(20):
        time.sleep(0.25)
        if is_server_running():
            return True
    return is_server_running()

mcp = FastMCP(
    "Splitflap Todo",
    instructions=(
        "Manage the user's daily todo list displayed in the Splitflap app (physical flap UI). "
        "Call open_splitflap() first when the user wants to view or interact with the flaps — it will start the server if needed and open a new Chrome window. "
        "Then use set_tasks / set_tasks_markdown to load the day's list, get_status to check progress, add_tasks, complete_task, etc. "
        "Non-negotiable tasks are must-do items — set nonNegotiable: true. "
        "The UI is at http://localhost:8787 and updates live."
    ),
)


def _api(method: str, path: str, body=None):
    """Call the splitflap server API. Automatically starts the backend server if needed."""
    ensure_server_running()
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        return {"error": f"Cannot reach splitflap server at {BASE_URL}. ({e})"}


@mcp.tool()
def get_status() -> dict:
    """Get the current todo list status: how many tasks done, remaining, non-negotiables left, session time."""
    return _api("GET", "/api/status")


@mcp.tool()
def get_tasks() -> list:
    """Get the full task list with done/pending status and non-negotiable flags."""
    return _api("GET", "/api/tasks")


@mcp.tool()
def set_tasks(tasks: list[dict]) -> dict:
    """
    Replace the entire todo list. Each task needs: text (str), nonNegotiable (bool).
    Example: [{"text": "Send report", "nonNegotiable": true}, {"text": "Water plants", "nonNegotiable": false}]
    The browser app will pick up the new list on next refresh or init.
    """
    return _api("POST", "/api/tasks", {"tasks": tasks})


@mcp.tool()
def set_tasks_markdown(markdown: str) -> dict:
    """
    Set the full todo list from a markdown string. Each line is a task.
    Prefix with **! to mark as non-negotiable (must-do).
    Example:
        **! Send quarterly report
        **! Call dentist
        Water plants
        Read chapter 5
    """
    return _api("POST", "/api/tasks", {"markdown": markdown})


@mcp.tool()
def add_tasks(tasks: list[str]) -> dict:
    """
    Add one or more tasks to the existing list. Pass plain strings.
    Prefix with **! for non-negotiable. Example: ["**! Send email", "Buy groceries"]
    """
    return _api("POST", "/api/tasks/add", tasks)


@mcp.tool()
def complete_task(text: str) -> dict:
    """Mark a task as done by its text (exact or partial match). Example: complete_task("Send report")"""
    return _api("POST", "/api/tasks/complete", {"text": text})


@mcp.tool()
def get_sessions() -> list:
    """Get historical session data (time spent per day, tasks completed) for productivity analysis."""
    return _api("GET", "/api/sessions")


@mcp.tool()
def open_splitflap() -> dict:
    """Start the Splitflap backend server (if not already running) and open the physical flap todo UI in a new Chrome window.
    Call this when the user asks to "open in splitflap", "show the flaps", "load into the mechanical display", etc.
    After this succeeds, the other MCP tools (set_tasks, get_status, etc.) will work against the live UI.
    """
    server_was_started = ensure_server_running()
    url = "http://localhost:8787"
    try:
        subprocess.run(
            ["open", "-na", "Google Chrome", "--args", "--new-window", url],
            check=False,
            timeout=8
        )
        return {
            "ok": True,
            "url": url,
            "server_started": server_was_started,
            "message": "Splitflap UI opened in a new Chrome window. The list is now live — use set_tasks / add_tasks / complete_task etc. to control it."
        }
    except Exception as e:
        return {
            "ok": False,
            "url": url,
            "server_started": server_was_started,
            "error": str(e)
        }


if __name__ == "__main__":
    mcp.run()
