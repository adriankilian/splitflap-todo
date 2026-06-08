# SPLITFLAP — Todo

A todo list app with a beautiful, highly realistic simulation of **physical split-flap displays** (the classic mechanical Solari boards you see in old airports and train stations).

The entire frontend is a single self-contained `index.html` with detailed CSS and JavaScript that recreates the physical flipping mechanics, textures, lighting, and sound of real split-flap units.

<!-- Add a real screenshot of the flap display here later -->
<!-- ![Splitflap Todo](screenshot.png) -->

## Features

- **Physical flap simulation** — each character is an independent mechanical unit that flips with realistic timing and easing
- **Non-negotiable tasks** — mark critical items with `!` or `**!` (they get special treatment in the UI and APIs)
- **Local-first** — everything runs on your machine
- **REST API** — full control from scripts, automation, or AI agents
- **MCP server** — integrate directly with Claude Desktop (or any MCP client)
- **Session tracking** — records time spent and daily progress
- Dark, tactile industrial aesthetic with paper-like flap textures

## Quick Start

```bash
cd splitflap-todo

# Start the server (Python 3)
python3 server.py
```

Then open **http://localhost:8787** in your browser.

The server also watches/serves `tasks.json` and provides live API endpoints.

## API

The server runs on port **8787** and exposes:

| Method | Endpoint                | Description |
|--------|-------------------------|-------------|
| GET    | `/api/tasks`            | Get full task list |
| GET    | `/api/status`           | Summary (counts, non-negotiables left, session time) |
| GET    | `/api/sessions`         | Historical productivity data |
| POST   | `/api/tasks`            | Replace entire list (accepts JSON array or `{ "markdown": "..." }`) |
| POST   | `/api/tasks/add`        | Append one or more tasks |
| POST   | `/api/tasks/complete`   | Mark a task done by text (exact or fuzzy match) |
| PUT    | `/api/tasks`            | Sync current browser state back to server |

Example:

```bash
curl -X POST http://localhost:8787/api/tasks/add \
  -H "Content-Type: application/json" \
  -d '["**! Review the new PR", "Water the plants"]'
```

## MCP / Claude Desktop Integration

There's also an MCP server (`mcp_server.py`) so Claude can directly manage your splitflap todo list.

1. Make sure the web server is running (`python3 server.py`)
2. The MCP script uses `uv` (https://docs.astral.sh/uv/):

```bash
# Run directly (uv will handle deps)
uv run mcp_server.py
```

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "splitflap-todo": {
      "command": "uv",
      "args": ["run", "/absolute/path/to/splitflap-todo/mcp_server.py"]
    }
  }
}
```

Available tools in Claude:
- `get_status`
- `get_tasks`
- `set_tasks`
- `set_tasks_markdown`
- `add_tasks`
- `complete_task`
- `get_sessions`

## Data Files

- `tasks.json` — current todo list (committed as example/default)
- `todos.md` — markdown version of the same list (used for easy editing)
- `sessions.json` — **gitignored** (your local history)

## Tech

- Pure static frontend (one HTML file, ~55k)
- Vanilla JS + CSS for the flap physics
- Minimal Python `http.server` backend with CORS for local tooling / AI agents
- MCP via FastMCP

## Why?

Because regular todo apps are boring. Physical split-flap displays have soul.

---

Built as a fun experiment in mechanical UI simulation + local-first tooling + agent integration.

PRs, issues, and weird flap animation improvements welcome.
