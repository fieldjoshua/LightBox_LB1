#!/usr/bin/env bash
set -euo pipefail

settings_dir="$HOME/Library/Application Support/Cursor/User"
settings_json="$settings_dir/settings.json"
ts="$(date +%Y%m%d-%H%M%S)"

if [[ ! -f "$settings_json" ]]; then
  echo "Cursor settings not found at: $settings_json"
  echo "Open Cursor once, then try again."
  exit 1
fi

cp -v "$settings_json" "$settings_json.bak.$ts"

python3 - "$settings_json" <<'PY'
import json, sys, pathlib
p = pathlib.Path(sys.argv[1])
data = {}
try:
    data = json.loads(p.read_text())
except Exception:
    # Keep original as backup; start fresh object if invalid
    data = {}

# Candidate keys (different Cursor builds may use different names)
updates = {
    "agent.allowTerminalCommands": True,
    "agent.allowFileSystemWrites": True,
    "agent.allowGitOperations": True,
    "agent.commandScope": "workspace",          # or "ask"
    "cursorAgent.allowTerminalCommands": True,
    "cursorAgent.allowFileSystemWrites": True,
    "cursorAgent.allowGitOperations": True,
    "cursorAgent.commandScope": "workspace",
    "cursor.agent.allowTerminalCommands": True,
    "cursor.agent.allowFileSystemWrites": True,
    "cursor.agent.allowGitOperations": True,
    "cursor.agent.commandScope": "workspace",
}

changed = []
for k, v in updates.items():
    if data.get(k) != v:
        data[k] = v
        changed.append(k)

p.write_text(json.dumps(data, indent=2, sort_keys=True))
print("Updated keys:" if changed else "No changes needed.")
for k in changed:
    print(" -", k)
PY

echo "Done. If Cursor is open, restart it to take effect."
