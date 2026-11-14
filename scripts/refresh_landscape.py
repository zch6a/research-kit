"""Refresh the GitHub facts in landscape.json: stars, last push, licence, archived, and the current name
of a repository that has moved. Run by hand (it rewrites the file; review the diff before committing):

    GITHUB_TOKEN=... python scripts/refresh_landscape.py           # update landscape.json
    GITHUB_TOKEN=... python scripts/refresh_landscape.py --check   # only report: archived, moved, gone

Every number on the page comes from this script, with the date it was run ("checked"). It sends nothing
but the repository names it asks about, with a generic User-Agent; the token (optional, read-only) only
raises GitHub's rate limit.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "landscape.json"


def fetch(repo: str) -> dict | None:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}", headers={"User-Agent": "research-kit-landscape", "Accept": "application/vnd.github+json"}
    )
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def facts(info: dict) -> dict:
    spdx = (info.get("license") or {}).get("spdx_id")
    return {
        "repo": info["full_name"],
        "stars": info["stargazers_count"],
        "pushed_at": info["pushed_at"][:10],
        "license": None if spdx in (None, "") else spdx,
        "archived": bool(info["archived"]),
    }


def main() -> int:
    check = "--check" in sys.argv[1:]
    doc = json.loads(FILE.read_text(encoding="utf-8"))
    problems = []
    for p in doc["projects"]:
        info = fetch(p["repo"])
        if info is None:
            problems.append(f"{p['repo']}: gone (404)")
            continue
        new = facts(info)
        if new["repo"].lower() != p["repo"].lower():
            problems.append(f"{p['repo']}: moved to {new['repo']}")
        if new["archived"] and not p.get("archived"):
            problems.append(f"{p['repo']}: archived")
        if not check:
            p.update(new)
    for x in problems:
        print(x, file=sys.stderr)
    if not check:
        doc["checked"] = dt.date.today().isoformat()
        FILE.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(f"refreshed {len(doc['projects'])} projects; {len(problems)} to look at")
    return 1 if check and problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
