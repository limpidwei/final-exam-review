#!/usr/bin/env python3
"""
Multi-agent install script for law-import skill.

Detects which AI coding agents are installed and deploys the skill
to the correct directories. Reads agents.json for path mappings.

Usage:
    python install.py                  # Auto-detect all agents, install for each
    python install.py --list           # List supported agents and their status
    python install.py --agent claude-code  # Install for specific agent only
    python install.py --all            # Install for all agents (even if not detected)
    python install.py --dry-run        # Show what would be installed, don't write

Supported agents (16):
    Claude Code, Claude Code IDE, Cursor, Windsurf, Cline,
    Codex, GitHub Copilot, Gemini CLI, OpenCode, Kimi Code,
    OpenCalw, Hermes (Obsidian), Augment, Continue.dev
"""

import argparse
import json
import os
import platform as pf
import re
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()
SKILL_NAME = "law-import"

def load_config():
    with open(SCRIPT_DIR / "agents.json", "r", encoding="utf-8") as f:
        return json.load(f)

def expand_path(path_str: str) -> str:
    """Expand ~ and %VAR% in paths."""
    if path_str is None:
        return None
    path_str = os.path.expanduser(path_str)
    path_str = path_str.replace("{skill_name}", SKILL_NAME)
    if pf.system() == "Windows":
        def repl(match):
            return os.environ.get(match.group(1), match.group(0))
        path_str = re.sub(r'%(\w+)%', repl, path_str)
    return os.path.abspath(path_str) if path_str else None

def get_platform_key() -> str:
    system = pf.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "macos"
    else:
        return "linux"

def check_agent(config: dict, agent_key: str) -> dict:
    """Check if an agent appears to be installed."""
    agent = config["agents"][agent_key]
    plat_key = get_platform_key()
    checks = agent.get("checks", [])
    found = []

    home = os.path.expanduser("~")
    for check in checks:
        check_expanded = expand_path(check) if check else None
        if check_expanded and os.path.exists(check_expanded):
            found.append(check_expanded)

    # Also check if target path already has law-import
    paths = agent.get("paths", {})
    target_base = paths.get(plat_key)
    if target_base:
        target = expand_path(target_base)
        already_installed = target and os.path.exists(os.path.join(target, "SKILL.md"))
    else:
        already_installed = False

    return {
        "key": agent_key,
        "name": agent["name"],
        "type": agent["type"],
        "detected": len(found) > 0,
        "evidence": found,
        "already_installed": already_installed,
        "target": target_base,
        "vault_path": agent.get("vault_path"),
        "note": agent.get("note", ""),
    }

def install_agent(config: dict, agent_key: str, dry_run: bool = False) -> dict:
    """Install the skill for a specific agent. Returns status dict."""
    agent = config["agents"][agent_key]
    plat_key = get_platform_key()
    paths = agent.get("paths", {})
    target_base = paths.get(plat_key)
    files = agent.get("files", {})
    agent_type = agent["type"]

    result = {"agent": agent_key, "status": "unknown", "actions": []}

    # Hermes deprecated in v2: treat as standard skill_md agent
    if agent_type == "hermes_note":
        # Fall through to standard handling below
        agent_type = "skill_md"

    # Standard file-copy agents
    if not target_base:
        result["status"] = "skipped"
        result["actions"].append(f"No path configured for {plat_key}")
        return result

    target_dir = expand_path(target_base)
    if not target_dir:
        result["status"] = "error"
        result["actions"].append("Could not resolve target path")
        return result

    for dest_name, source_name in files.items():
        source_file = SCRIPT_DIR / source_name
        dest_file = Path(target_dir) / dest_name

        if not source_file.exists():
            result["actions"].append(f"WARNING: Source {source_file} not found, skipping")
            continue

        if not dry_run:
            os.makedirs(str(dest_file.parent), exist_ok=True)
            # Copy content (symlinks can be fragile cross-platform, so copy)
            shutil.copy2(str(source_file), str(dest_file))

        result["actions"].append(f"Copied {source_name} → {dest_file}")
        result["status"] = "installed"

    if not result["actions"]:
        result["status"] = "skipped"
        result["actions"].append("No files to install")

    return result

def list_agents(config: dict) -> None:
    """Print status of all supported agents."""
    print(f"\n{'='*70}")
    print(f"  law-import — Multi-Agent Installation Status")
    print(f"  Platform: {pf.system()} ({get_platform_key()})")
    print(f"{'='*70}\n")

    for agent_key in config["agents"]:
        status = check_agent(config, agent_key)
        icon = "✅" if status["detected"] else "⬜"
        installed = " (already installed)" if status["already_installed"] else ""
        print(f"  {icon} {status['name']:<30} {status['type']:<15}{installed}")
        if status["evidence"]:
            for ev in status["evidence"]:
                print(f"     └─ found: {ev}")
        if status["note"]:
            print(f"     └─ note: {status['note']}")

    print(f"\n  Run: python install.py           to install for all detected agents")
    print(f"  Run: python install.py --all      to install for all agents (force)")
    print(f"  Run: python install.py --dry-run  to preview without writing\n")

def main():
    parser = argparse.ArgumentParser(
        description="Install law-import skill for AI coding agents"
    )
    parser.add_argument("--list", action="store_true", help="List supported agents and exit")
    parser.add_argument("--agent", type=str, help="Install for a specific agent only")
    parser.add_argument("--all", action="store_true", help="Install for all agents (even if not detected)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't write files")
    args = parser.parse_args()

    config = load_config()

    if args.list:
        list_agents(config)
        return

    # Determine which agents to install
    if args.agent:
        if args.agent not in config["agents"]:
            print(f"Unknown agent: {args.agent}")
            print(f"Supported: {', '.join(config['agents'].keys())}")
            sys.exit(1)
        targets = [args.agent]
    elif args.all:
        targets = list(config["agents"].keys())
    else:
        # Auto-detect: install only for detected agents
        targets = []
        for key in config["agents"]:
            status = check_agent(config, key)
            if status["detected"]:
                targets.append(key)

    if not targets:
        print("No agents detected. Use --all to force install for all.")
        print("Or run with --list to see what's supported.")
        sys.exit(0)

    print(f"\n{' Installing law-import for ' + str(len(targets)) + ' agent(s) ':=^60}\n")

    results = []
    for agent_key in targets:
        agent = config["agents"][agent_key]
        if args.dry_run:
            status = check_agent(config, agent_key)
            print(f"  [DRY RUN] {agent['name']}: would install to {status.get('target', 'N/A')}")
            results.append({"agent": agent_key, "status": "dry_run"})
        else:
            result = install_agent(config, agent_key, dry_run=False)
            icon = "✅" if result["status"] == "installed" else "⬜"
            print(f"  {icon} {agent['name']}")
            for action in result["actions"]:
                print(f"     └─ {action}")
            results.append(result)

    # Summary
    installed = sum(1 for r in results if r["status"] == "installed")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")

    print(f"\n{' Summary ':=^60}")
    print(f"  Installed: {installed}  |  Skipped: {skipped}  |  Errors: {errors}")
    print(f"  Source: {SCRIPT_DIR / 'SKILL.md'}")
    print(f"  Canonical file. All agents read from here.\n")

if __name__ == "__main__":
    main()
