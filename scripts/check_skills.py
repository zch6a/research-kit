"""Each tool's skill as the marketplace installs it: plugin/skills/*/SKILL.md and plugin/.claude-plugin/plugin.json at
the v0 tag of its repository, fetched from GitHub. The frontmatter must parse as YAML (a plain value with ": " inside
does not, and Claude Code then loads the skill with no description), with the plugin's name and a description that
says when to use it. Needs PyYAML and the network:

    uv run --with pyyaml python scripts/check_skills.py
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "research-kit (skill check)"}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return bytes(r.read())


def main() -> int:
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    problems = []
    for p in market["plugins"]:
        src = p["source"]
        repo, path, ref = src["url"], src["path"], src["ref"]
        raw = f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"
        try:
            manifest = json.loads(get(f"{raw}/.claude-plugin/plugin.json"))
            listing = json.loads(get(f"https://api.github.com/repos/{repo}/contents/{path}/skills?ref={ref}"))
        except Exception as e:  # noqa: BLE001
            problems.append(f"{p['name']}: could not read {repo}@{ref}/{path} ({e})")
            continue
        if manifest.get("name") != p["name"]:
            problems.append(f"{p['name']}: plugin.json names {manifest.get('name')!r}")
        skills = [x["name"] for x in listing if x.get("type") == "dir"]
        if not skills:
            problems.append(f"{p['name']}: no skill in {path}/skills")
        for skill in skills:
            text = get(f"{raw}/skills/{skill}/SKILL.md").decode("utf-8")
            m = re.match(r"---\n(.*?)\n---\n", text, re.S)
            try:
                front = yaml.safe_load(m.group(1)) if m else None
            except yaml.YAMLError as e:
                problems.append(f"{p['name']}/{skill}: the frontmatter is not YAML ({str(e).splitlines()[0]})")
                continue
            if not isinstance(front, dict):
                problems.append(f"{p['name']}/{skill}: no frontmatter")
                continue
            if front.get("name") != skill:
                problems.append(f"{p['name']}/{skill}: name is {front.get('name')!r}")
            desc = str(front.get("description") or "")
            if len(desc) < 80 or "use when" not in desc.lower():
                problems.append(f"{p['name']}/{skill}: the description does not say when to use it")
        print(f"{p['name']}: {', '.join(skills)} ok" if not any(x.startswith(p["name"]) for x in problems) else f"{p['name']}: problems")
    for x in problems:
        print("  " + x, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
