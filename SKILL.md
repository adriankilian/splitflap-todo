# splitflap (MCP + live UI version)

**Open the user's daily todo list in the physical split-flap mechanical display (live MCP-controlled version).**

The user wants the **MCP/live path** (not the static generator). This gives them a persistent UI at http://localhost:8787 that Claude can actively control in real time while the beautiful flap animations are visible.

## When to use this skill
- User says: "open this in the splitflap", "show my todos as flaps", "load today's list into the mechanical display", "open the splitflap", "I want to see it in the flaps", etc.
- They want the live, interactive version where you can keep updating the list via tools and the browser UI reflects changes immediately.

## How to use (seamless flow — no manual server launch required)
1. Collect / confirm the current day's todo list from the conversation (markdown or structured).
   - Mark must-dos with `**!` or `!` prefix.

2. **First action**: Call the MCP tool `open_splitflap()`.
   - This tool automatically starts the backend web server if it isn't running.
   - It then opens the physical split-flap UI in a **new Chrome window**.
   - You no longer need to tell the user (or run yourself) `python3 server.py`.

3. Load the list:
   - Preferred: `set_tasks_markdown("...")` with the full markdown list (supports `**!` for non-negotiables).
   - Or `set_tasks([...])` with array of objects.

4. You can now freely use the other tools:
   - `get_status()` — quick overview + non-negotiables left
   - `add_tasks([...])`
   - `complete_task("partial text")`
   - `get_tasks()`, `get_sessions()`, etc.

The UI in the browser will react live to your tool calls (the flaps will re-render on refresh or when the frontend polls).

3. Tell the user something like: "Opening your tasks in the splitflap display now..." or "The mechanical board is up — I've loaded today's list."

## Important notes
- The first time you call any tool (especially `open_splitflap`), the MCP server will start the web backend for you in the background. The user never has to launch `server.py` manually in a terminal.
- Once `open_splitflap()` has succeeded, the other tools work against the live UI.
- The browser window can stay open all day. Claude can keep managing the list through the MCP tools.
- Non-negotiable tasks are specially highlighted in the UI.

## Tool cheat sheet (for the model)
- `open_splitflap()` — the one to call when the user wants to "see the flaps". Handles server start + Chrome launch.
- `set_tasks_markdown(markdown)` — easiest way to load a full day's list.
- `set_tasks(list_of_dicts)`
- `add_tasks(list_of_strings)`
- `complete_task(text)`
- `get_status()`
- `get_tasks()`

## Example conversation flow the user expects
User: "Here's my list for today: - **! Ship the PR - Review the design doc - Water plants"
You (in your head): Call open_splitflap(), then set_tasks_markdown with the list.
User sees: New Chrome window pops up with the gorgeous split-flap board already showing their tasks.

This is the seamless experience: user sets/refines the list in chat → asks to open in splitflap → one tool call later the physical display is live and under your control. No extra steps for the human.

(The static `generate_splitflap.py` still exists as a nice fallback for one-off pretty views or when you don't want any background processes, but the user specifically wants the MCP live path.)
