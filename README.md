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

## Quick Start (Recommended — Zero Server)

```bash
cd splitflap-todo

# Generate a beautiful standalone split-flap display from your list and open it
python generate_splitflap.py --input todos.md --open
# or
python generate_splitflap.py --markdown "
- **! Finish the report
- Call dentist
- Review PRs
" --open
```

This creates a fully self-contained `splitflap-YYYY-MM-DD.html` and opens it in a fresh Chrome window.  
**No server, no ports, nothing else to launch.** Perfect for daily use.

See [SKILL.md](./SKILL.md) for the exact instructions an AI assistant should follow when you say "open this in the splitflap".

---

## Live MCP Mode (recommended when you want Claude to actively control the list)

This is the path that gives you a persistent, live-updating physical flap UI that Claude can read and write in real time.

**You no longer have to manually run `python3 server.py`.**

- The Splitflap Todo MCP server (when loaded in Claude Desktop or via the `claude` CLI) will automatically start the web backend the first time you use any of its tools.
- Call the `open_splitflap()` tool (exposed by the MCP) when the user says "open in splitflap", "show the flaps", etc. It will:
  1. Start the server in the background if needed.
  2. Open http://localhost:8787 in a new Chrome window.

See [SKILL.md](./SKILL.md) for the exact instructions to give your AI assistant.

Once the UI is open, you (via Claude) can continue using:
- `set_tasks_markdown(...)`
- `add_tasks(...)`
- `complete_task(...)`
- `get_status()`, etc.

The browser flaps will reflect changes live.

(The static generator is still available as a nice no-process alternative for one-off beautiful views.)

## Quick manual start (if you want the UI without Claude)

```bash
python3 server.py
# then open http://localhost:8787 in your browser
```

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
