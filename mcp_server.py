#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastmcp>=2.0.0"]
# ///
"""
MCP server for Splitflap Todo — lets Claude Desktop manage your daily task list.

Start the web server first:  python3 server.py
Then add this to Claude Desktop's MCP config.
"""

import json
import urllib.request
import urllib.error
from fastmcp import FastMCP

BASE_URL = "http://localhost:8787"

mcp = FastMCP(
    "Splitflap Todo",
    instructions=(
        "Manage the user's daily todo list displayed in the Splitflap app. "
        "Use set_tasks to load a full day's todo list. "
        "Use get_status to check progress. "
        "Use add_tasks to append tasks. "
        "Use complete_task to mark one done. "
        "Non-negotiable tasks are must-do items for the day — set nonNegotiable: true. "
        "The app runs at http://localhost:8787"
    ),
)


def _api(method: str, path: str, body=None):
    """Call the splitflap server API."""
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        return {"error": f"Cannot reach splitflap server at {BASE_URL}. Is server.py running? ({e})"}


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


if __name__ == "__main__":
    mcp.run()
