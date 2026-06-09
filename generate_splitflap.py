#!/usr/bin/env python3
"""
generate_splitflap.py

Turn a todo list (markdown or JSON) into a beautiful, self-contained
static HTML file that simulates physical split-flap displays.

No web server required. Just open the generated .html file.

Usage examples:
  python generate_splitflap.py --input todos.md --open
  python generate_splitflap.py --markdown "- **! Finish report\n- Call dentist" --output my-flaps.html
  cat tasks.json | python generate_splitflap.py --stdin-json --open
  python generate_splitflap.py   # uses tasks.json or todos.md if present

This is the recommended way to get the splitflap experience from Claude or scripts.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def parse_task_line(line: str):
    """Parse a single line into (text, non_negotiable). Matches JS parseMD + server logic."""
    val = line.strip()
    if val.startswith("- "):
        val = val[2:].strip()
    if not val:
        return None, False

    non_negotiable = False
    text = val

    # **!text** or **! text **
    m = re.match(r'^\*\*!(.+?)\*\*$', text)
    if m:
        non_negotiable = True
        text = m.group(1).strip()
    elif text.startswith("**!"):
        non_negotiable = True
        text = text[3:].strip()
        if text.endswith("**"):
            text = text[:-2].strip()
    elif text.startswith("!"):
        non_negotiable = True
        text = text[1:].strip()

    if text:
        return text, non_negotiable
    return None, False


def parse_markdown(text: str):
    """Parse markdown todo list into task objects (only lines starting with - )."""
    tasks = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped.startswith("- "):
            continue
        text_val, nn = parse_task_line(raw)
        if text_val:
            tasks.append({
                "text": text_val,
                "nonNegotiable": nn,
                "done": False
            })
    return tasks


def load_tasks_from_input(args) -> list:
    """Load and normalize tasks from CLI arguments."""
    if args.stdin_json:
        data = sys.stdin.read()
        try:
            parsed = json.loads(data)
            if isinstance(parsed, list):
                return normalize_tasks(parsed)
        except Exception:
            pass
        # fallback: treat as markdown
        return parse_markdown(data)

    if args.tasks_json:
        try:
            parsed = json.loads(args.tasks_json)
            if isinstance(parsed, list):
                return normalize_tasks(parsed)
        except Exception as e:
            print(f"Error parsing --tasks-json: {e}", file=sys.stderr)
            sys.exit(1)

    if args.markdown:
        return parse_markdown(args.markdown)

    # --input file or auto-detect
    input_path = args.input
    if not input_path:
        # sensible defaults
        for candidate in ("tasks.json", "todos.md", "tasks.md"):
            if Path(candidate).exists():
                input_path = candidate
                break

    if not input_path:
        print("No tasks provided. Use --input, --markdown, or have tasks.json/todos.md in the directory.", file=sys.stderr)
        sys.exit(1)

    path = Path(input_path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8")

    if path.suffix.lower() == ".json":
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return normalize_tasks(data)
            if isinstance(data, dict) and "tasks" in data:
                return normalize_tasks(data["tasks"])
        except Exception as e:
            print(f"Failed to parse JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # treat as markdown
        return parse_markdown(content)

    print("Could not understand input format.", file=sys.stderr)
    sys.exit(1)


def normalize_tasks(raw_tasks):
    """Ensure every task has the expected shape."""
    normalized = []
    for t in raw_tasks:
        if isinstance(t, str):
            text, nn = parse_task_line(t)
            if text:
                normalized.append({"text": text, "nonNegotiable": nn, "done": False})
        elif isinstance(t, dict):
            text = t.get("text") or t.get("title") or ""
            if not text:
                continue
            normalized.append({
                "text": text,
                "nonNegotiable": bool(t.get("nonNegotiable") or t.get("non_negotiable")),
                "done": bool(t.get("done"))
            })
    return normalized


def inject_initial_data(html: str, tasks: list, generated_date: str) -> str:
    """Inject window.INITIAL_TASKS and a small generated marker into the HTML."""
    tasks_json = json.dumps(tasks, ensure_ascii=False, indent=2)

    data_script = f"""<script>
/* === SPLITFLAP STATIC DATA (injected by generate_splitflap.py) === */
window.INITIAL_TASKS = {tasks_json};
window.GENERATED_DATE = "{generated_date}";
window.IS_SPLITFLAP_STATIC = true;
</script>
"""

    # Insert the data script right before the main application script block.
    # This is reliable because the big <script> with STATE comment is unique.
    marker = '<script>\n// ═══════════════════════════════════════════\n// STATE'
    if marker in html:
        html = html.replace(marker, data_script + marker, 1)
    else:
        # Fallback: inject near the end of <body>, before the last big script if possible
        html = html.replace('</body>', data_script + '</body>', 1)

    # Make the title nicer for static files
    today = generated_date
    html = re.sub(
        r'<title>.*?</title>',
        f'<title>SPLITFLAP — {today}</title>',
        html,
        flags=re.IGNORECASE,
        count=1
    )

    # Optional: add a tiny static badge in the CSS/after housing if we want (skipped for minimal change)
    return html


def generate(args):
    tasks = load_tasks_from_input(args)
    if not tasks:
        print("No tasks to display.", file=sys.stderr)
        sys.exit(1)

    generated_date = datetime.now().strftime("%Y-%m-%d")
    template_path = Path(args.template) if args.template else Path(__file__).parent / "index.html"

    if not template_path.exists():
        print(f"Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(tasks)} task(s)")

    html = template_path.read_text(encoding="utf-8")
    html = inject_initial_data(html, tasks, generated_date)

    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path(f"splitflap-{generated_date}.html")

    out_path.write_text(html, encoding="utf-8")
    print(f"Generated: {out_path.resolve()}")

    if args.open or args.open_chrome:
        abs_path = out_path.resolve().as_uri()  # file:///...
        try:
            # macOS: open in a fresh Chrome window
            subprocess.run([
                "open", "-na", "Google Chrome",
                "--args", "--new-window", abs_path
            ], check=False)
            print("Opened in new Chrome window.")
        except Exception as e:
            print(f"Could not auto-open Chrome: {e}")
            print(f"You can open it manually: {abs_path}")

    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate a standalone physical split-flap todo display (no server needed)."
    )
    parser.add_argument("--input", "-i", help="Path to todos.md, tasks.json, or similar")
    parser.add_argument("--markdown", "-m", help="Raw markdown string of tasks (lines starting with - )")
    parser.add_argument("--tasks-json", help="JSON array of task objects")
    parser.add_argument("--stdin-json", action="store_true", help="Read tasks as JSON from stdin")
    parser.add_argument("--output", "-o", help="Output HTML file (default: splitflap-YYYY-MM-DD.html)")
    parser.add_argument("--template", help="Path to index.html template (default: ./index.html)")
    parser.add_argument("--open", action="store_true", help="Open the result in a new Chrome window after generating")
    parser.add_argument("--open-chrome", action="store_true", help="Alias for --open")

    args = parser.parse_args()

    if args.open_chrome:
        args.open = True

    generate(args)


if __name__ == "__main__":
    main()
