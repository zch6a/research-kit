"""Everything generated from tools.json: the plugin marketplace (.claude-plugin/marketplace.json), the tool sections
of README.md and README.zh-CN.md (between their markers) and the site (site/index.html).

    python scripts/render.py           # write them
    python scripts/render.py --check   # exit 1 if any is out of date, or tools.json is incomplete (CI runs this)
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = "zch6a"
START, END = "<!-- tools:start -->", "<!-- tools:end -->"
EXAMPLE = "table-trace"  # the plugin installed as an example on the site and in the READMEs: it must be in the list


SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")


def load(path: Path | None = None) -> dict:
    """tools.json, checked: SystemExit naming every problem when an entry is incomplete or wrong."""
    doc = json.loads((path or ROOT / "tools.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    keys = []
    for s in doc.get("stages", []):
        for field in ("key", "en", "zh"):
            if not isinstance(s.get(field), str) or not s.get(field):
                problems.append(f"stage {s.get('key', '?')}: no {field}")
        keys.append(s.get("key"))
        # the key and the names go into ids, links and the marketplace as they are
        if isinstance(s.get("key"), str) and not SLUG.fullmatch(s["key"]):
            problems.append(f"stage {s['key']!r}: not lowercase letters, digits and hyphens")
    problems += [f"stage {k}: listed twice" for k in set(keys) if keys.count(k) > 1]
    stages = set(keys)
    tools = doc.setdefault("tools", [])
    names = [t.get("name", "?") for t in tools]
    problems += [f"{n}: listed twice" for n in set(names) if names.count(n) > 1]
    for t in tools:
        for field in ("name", "stage", "en", "zh", "command", "tags"):
            if not t.get(field):
                problems.append(f"{t.get('name', '?')}: no {field}")
        name, command = t.get("name", "?"), t.get("command", "")
        if not SLUG.fullmatch(str(name)):
            problems.append(f"{name!r}: the name is not lowercase letters, digits and hyphens")
        if not isinstance(t.get("tags", []), list) or not all(isinstance(x, str) for x in t.get("tags", [])):
            problems.append(f"{name}: tags are not a list of words")
        if t.get("stage") not in stages:
            problems.append(f"{name}: unknown stage {t.get('stage')!r}")
        # the command runs the release the marketplace installs, the v0 tag: uvx from git+https://github.com/...@v0,
        # npx from github:...#v0 (as the program run, not in a comment)
        runs = [line.split("#  ")[0].split("  #")[0] for line in command.splitlines()]
        if not any(f"github.com/{OWNER}/{name}@v0 " in r or f"github:{OWNER}/{name}#v0 " in r for r in runs):
            problems.append(f"{name}: the command does not run {OWNER}/{name} at v0")
        if "```" in command:
            problems.append(f"{name}: the command would end the README's code block")
        for lang in ("en", "zh"):
            if "\n" in t.get(lang, ""):
                problems.append(f"{name}: the {lang} text has a line break")
        t.setdefault("site", "")
        if t.get("site") and not t["site"].startswith("https://"):
            problems.append(f"{name}: the site is not an https link")
    if EXAMPLE not in names:
        problems.append(f"{EXAMPLE} (the install example): not in the list")
    if problems:
        raise SystemExit("tools.json: " + "; ".join(problems))
    return doc


def marketplace(doc: dict) -> str:
    plugins = []
    for t in doc["tools"]:
        plugins.append({
            "name": t["name"],
            # the plugin folder of the tool's own repository, at its latest release (the v0 tag)
            "source": {"source": "git-subdir", "url": f"{OWNER}/{t['name']}", "path": "plugin", "ref": "v0"},
            "description": t["en"],
            "category": "research",
            "tags": t["tags"],
            "homepage": t["site"] or f"https://github.com/{OWNER}/{t['name']}",
            "repository": f"https://github.com/{OWNER}/{t['name']}",
            "license": "MIT",
            "author": {"name": OWNER},
        })  # fmt: skip
    out = {
        "name": "research-kit",
        "description": "Tools for research work, from reading papers to after publication: one skill each, so that an agent runs the tool and quotes what it found.",
        "owner": {"name": OWNER},
        "plugins": plugins,
    }
    return json.dumps(out, indent=2, ensure_ascii=False) + "\n"


def readme_section(doc: dict, lang: str) -> str:
    lines = []
    for s in doc["stages"]:
        tools = [t for t in doc["tools"] if t["stage"] == s["key"]]
        if not tools:
            continue
        lines += [f"### {s[lang]}", ""]
        for t in tools:
            site = f" · [{'site' if lang == 'en' else '网站'}]({t['site']})" if t["site"] else ""
            lines += [f"**[{t['name']}](https://github.com/{OWNER}/{t['name']})**{site} — {t[lang]}", "", "```bash", t["command"], "```", ""]
    return "\n".join(lines).rstrip() + "\n"


def fill(path: Path, section: str) -> str:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        raise SystemExit(f"{path.name}: no {START} ... {END} markers")
    return pattern.sub(lambda _: f"{START}\n{section}{END}", text)


def site(doc: dict) -> str:
    e = html.escape
    cards: dict[str, list[str]] = {"en": [], "zh": []}
    nav: dict[str, list[str]] = {"en": [], "zh": []}
    for lang in ("en", "zh"):
        for s in doc["stages"]:
            here = [t for t in doc["tools"] if t["stage"] == s["key"]]
            if not here:
                continue
            unit = " tools" if lang == "en" else " 个工具"
            nav[lang].append(f'<a href="#{lang}-{s["key"]}">{e(s[lang])} <span>{len(here)}<span class="sr">{unit}</span></span></a>')
            items = []
            for t in [t for t in doc["tools"] if t["stage"] == s["key"]]:
                links = [f'<a href="https://github.com/{OWNER}/{t["name"]}">{"code" if lang == "en" else "代码"}</a>']
                if t["site"]:
                    links.append(f'<a href="{e(t["site"])}">{"site" if lang == "en" else "网站"}</a>')
                items.append(
                    f"<article><h3>{e(t['name'])}</h3><p>{e(t[lang])}</p><pre><code>{e(t['command'])}</code></pre>"
                    f'<p class="links">{" · ".join(links)}</p></article>'
                )
            cards[lang].append(f'<section id="{lang}-{s["key"]}"><h2>{e(s[lang])}</h2><div class="grid">{"".join(items)}</div></section>')
    n = len(doc["tools"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'">
<title>research-kit</title>
<meta name="description" content="{n} open tools for research work, from reading papers to after publication: each a command, an agent skill, and some a site.">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <h1>research-kit</h1>
  <p class="lead" data-lang="en">{n} open tools for research work, from reading papers to after publication. Each is a command (no account; no API key, though paper-impact goes faster with a free one), an agent skill, and some a site. Rules and published data, no large language model (venue-atlas places papers with a small embedding model): what they report says where it comes from.</p>
  <p class="lead" data-lang="zh" lang="zh-CN" hidden>{n} 个开源科研工具，从读论文到论文发表之后。每个都是一条命令（不用注册；也不用 API key，只是 paper-impact 有免费 key 会快很多）和一个智能体技能，有的还有网站。靠规则和公开数据，不用大语言模型（venue-atlas 用一个小型嵌入模型给论文定位）：给出的每个结果都标明出处。</p>
  <nav aria-label="Stages" data-lang="en" class="stages">{"".join(nav["en"])}</nav>
  <nav aria-label="阶段" data-lang="zh" lang="zh-CN" class="stages" hidden>{"".join(nav["zh"])}</nav>
  <p><button type="button" id="lang" lang="zh-CN" hidden>中文</button></p>
  <div class="install">
    <p data-lang="en">The commands need <a href="https://docs.astral.sh/uv/">uv</a> (gpu-budget: Node 22+). As agent skills in Claude Code, add the marketplace once, then install the tools you want by name:</p>
    <p data-lang="zh" lang="zh-CN" hidden>命令需要先装 <a href="https://docs.astral.sh/uv/">uv</a>（gpu-budget 需要 Node 22+）。作为 Claude Code 的技能使用时，先添加一次插件市场，再按名字安装需要的工具：</p>
    <pre><code>/plugin marketplace add {OWNER}/research-kit
/plugin install {EXAMPLE}@research-kit</code></pre>
  </div>
</header>
<main>
<div data-lang="en">{"".join(cards["en"])}</div>
<div data-lang="zh" lang="zh-CN" hidden>{"".join(cards["zh"])}</div>
</main>
<footer><p>MIT · <a href="https://github.com/{OWNER}/research-kit">github.com/{OWNER}/research-kit</a></p></footer>
<script src="lang.js"></script>
</body>
</html>
"""


def count(text: str, n: int) -> str:
    """The README's badge with how many tools there are (the one place outside the markers that says it)."""
    return re.sub(
        r'<img alt="\d+ tools" src="https://img.shields.io/badge/tools-\d+-',
        f'<img alt="{n} tools" src="https://img.shields.io/badge/tools-{n}-',
        text,
    )


def outputs(doc: dict) -> dict[Path, str]:
    n = len(doc["tools"])
    return {
        ROOT / ".claude-plugin" / "marketplace.json": marketplace(doc),
        ROOT / "README.md": count(fill(ROOT / "README.md", readme_section(doc, "en")), n),
        ROOT / "README.zh-CN.md": count(fill(ROOT / "README.zh-CN.md", readme_section(doc, "zh")), n),
        ROOT / "site" / "index.html": site(doc),
    }


def main() -> int:
    check = "--check" in sys.argv[1:]
    stale = []
    files = outputs(load())
    for path, text in files.items():
        old = path.read_text(encoding="utf-8") if path.is_file() else None
        if old != text:
            stale.append(path.relative_to(ROOT).as_posix())
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="\n")
    if check and stale:
        print(f"out of date: {', '.join(stale)}; run python scripts/render.py", file=sys.stderr)
        return 1
    print(("checked" if check else "written") + f": {len(files)} files" + (f" ({', '.join(stale)} changed)" if stale and not check else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
