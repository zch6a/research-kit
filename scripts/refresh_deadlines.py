"""Refresh deadlines.json: the submission deadlines of machine-learning venues, from ccf-deadlines (MIT; the dates its
community keeps, with each venue's link), next to the rules submit-check keeps for the same venue (page limits,
required sections, each with the official page it comes from). Run by hand, like refresh_landscape.py; review the diff:

    GITHUB_TOKEN=... python scripts/refresh_deadlines.py     (the token is optional; it raises GitHub's rate limit)

It reads public files only (raw.githubusercontent.com: ccf-deadlines at its current commit, submit-check's rules at
its v0 tag), sends nothing else, with a generic User-Agent, and stores dates, places and links, never more.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

import tomllib
import yaml

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "deadlines.json"
CCF = "ccfddl/ccf-deadlines"
RULES = "https://raw.githubusercontent.com/zch6a/submit-check/v0/src/submit_check/rules/{}.toml"
# Our name for the venue, its file in ccf-deadlines, and the submit-check rules that apply ("" when it has none).
VENUES = [
    ("NeurIPS", "AI/nips.yml", "neurips2025"),
    ("ICML", "AI/icml.yml", "icml2025"),
    ("ICLR", "AI/iclr.yml", "iclr2026"),
    ("CVPR", "AI/cvpr.yml", "cvpr2026"),
    ("ICCV", "AI/iccv.yml", ""),
    ("ECCV", "AI/eccv.yml", "eccv2026"),
    ("ACL", "AI/acl.yml", "acl-arr"),
    ("EMNLP", "AI/emnlp.yml", "acl-arr"),
    ("NAACL", "AI/naacl.yml", "acl-arr"),
    ("AAAI", "AI/aaai.yml", "aaai2026"),
    ("IJCAI", "AI/ijcai.yml", "ijcai2026"),
    ("KDD", "DB/sigkdd.yml", "kdd2026"),
    ("COLM", "AI/colm.yml", ""),
    ("AISTATS", "AI/aistats.yml", ""),
    ("COLT", "AI/colt.yml", ""),
    ("CoRL", "AI/corl.yml", ""),
]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "research-kit-deadlines"})
    if url.startswith("https://api.github.com/") and os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")  # optional, read-only: only the rate limit
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(2_000_000)


def head_commit() -> str:
    data = json.loads(get(f"https://api.github.com/repos/{CCF}/commits/main"))
    return data["sha"]


def venue(name: str, data: list[dict], rules_id: str, rules: dict, today: dt.date) -> dict:
    """The venue's editions from last year on, each with its deadlines, and the rules."""
    entry = data[0]
    editions = []
    for c in entry.get("confs", []):
        if int(c.get("year", 0)) < today.year - 1:
            continue
        timeline = []
        for t in c.get("timeline", []):
            item = {k: str(t[k]) for k in ("abstract_deadline", "deadline") if t.get(k) and str(t[k]).upper() != "TBD"}
            if "deadline" not in item:
                continue
            if t.get("comment"):
                item["comment"] = str(t["comment"])
            timeline.append(item)
        if timeline:
            editions.append(
                {"year": int(c["year"]), "link": str(c.get("link", "")), "timezone": str(c.get("timezone", "")),
                 "date": str(c.get("date", "")), "place": str(c.get("place", "")), "timeline": timeline}
            )  # fmt: skip
    out = {"name": name, "description": str(entry.get("description", "")), "editions": editions, "rules": None}
    if rules_id:
        v, pages = rules["venue"], rules.get("pages", {})
        out["rules"] = {
            "id": rules_id,
            "name": v["name"],
            "pages": pages.get("submission"),
            "camera_ready": pages.get("camera_ready"),
            "not_counted": pages.get("not_counted", []),
            "required": [r["what"] for r in rules.get("required", [])],
            "source": v["source"],
            "verified": v["verified"],
            "policy": {k: str(x) for k, x in rules.get("policy", {}).items() if str(x)},  # LLM use, supplementary, author response
        }
    return out


def main() -> int:
    today = dt.date.today()
    commit = head_commit()
    venues = []
    cache: dict[str, dict] = {}
    for name, path, rules_id in VENUES:
        data = yaml.safe_load(get(f"https://raw.githubusercontent.com/{CCF}/{commit}/conference/{path}"))
        if rules_id and rules_id not in cache:
            cache[rules_id] = tomllib.loads(get(RULES.format(rules_id)).decode("utf-8"))
        venues.append(venue(name, data, rules_id, cache.get(rules_id, {}), today))
    doc = {
        "checked": today.isoformat(),
        "sources": {
            "deadlines": {"repo": CCF, "commit": commit, "licence": "MIT"},
            "rules": {"repo": "zch6a/submit-check", "ref": "v0"},
        },
        "venues": venues,
    }
    FILE.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(venues)} venues, {sum(len(v['editions']) for v in venues)} editions (ccf-deadlines {commit[:7]})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
