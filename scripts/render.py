"""Everything generated from tools.json (our tools) and landscape.json (the best of the rest on GitHub, and what
nothing covers yet): the plugin marketplace (.claude-plugin/marketplace.json), the sections of README.md and
README.zh-CN.md between their markers, and the site (site/index.html).

    python scripts/render.py           # write them
    python scripts/render.py --check   # exit 1 if any is out of date, or a list is incomplete (CI runs this)

The GitHub facts in landscape.json (stars, last push, licence) come from scripts/refresh_landscape.py.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = "zch6a"
MARKERS = {
    "tools": ("<!-- tools:start -->", "<!-- tools:end -->"),
    "gaps": ("<!-- gaps:start -->", "<!-- gaps:end -->"),
    "deadlines": ("<!-- deadlines:start -->", "<!-- deadlines:end -->"),
}
START, END = MARKERS["tools"]
EXAMPLE = "table-trace"  # the plugin installed as an example on the site and in the READMEs: it must be in the list

SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


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


def load_landscape(doc: dict, path: Path | None = None) -> dict:
    """landscape.json, checked against itself and against tools.json (every tool of ours in a section of the
    stage it is listed under)."""
    land = json.loads((path or ROOT / "landscape.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    try:
        dt.date.fromisoformat(land.get("checked", ""))
    except ValueError:
        problems.append("checked: not a date")
    stages = {s["key"] for s in doc["stages"]}
    sections: dict[str, str] = {}
    for s in land.get("sections", []):
        key = s.get("key", "?")
        if not SLUG.fullmatch(str(key)) or key in sections:
            problems.append(f"section {key!r}: not a slug, or listed twice")
        if not s.get("en") or not s.get("zh"):
            problems.append(f"section {key}: no en or zh")
        if s.get("stage") not in stages:
            problems.append(f"section {key}: unknown stage {s.get('stage')!r}")
        sections[key] = s.get("stage")
    for t in doc["tools"]:
        if t.get("section") not in sections:
            problems.append(f"{t['name']}: unknown section {t.get('section')!r}")
        elif sections[t["section"]] != t["stage"]:
            problems.append(f"{t['name']}: section {t['section']} belongs to stage {sections[t['section']]}, not {t['stage']}")
    seen: set[str] = set()
    for p in land.get("projects", []):
        repo = str(p.get("repo", "?"))
        if not REPO.fullmatch(repo):
            problems.append(f"{repo!r}: not owner/name")
        if repo.lower() in seen:
            problems.append(f"{repo}: listed twice")
        seen.add(repo.lower())
        if repo.lower().startswith(f"{OWNER}/"):
            problems.append(f"{repo}: ours, so it belongs in tools.json")
        if p.get("section") not in sections:
            problems.append(f"{repo}: unknown section {p.get('section')!r}")
        for lang in ("en", "zh"):
            if not p.get(lang) or "\n" in p[lang]:
                problems.append(f"{repo}: no {lang} text, or a line break in it")
        if not isinstance(p.get("stars"), int) or p["stars"] < 0:
            problems.append(f"{repo}: stars is not a count")
        try:
            dt.date.fromisoformat(p.get("pushed_at", ""))
        except (ValueError, TypeError):
            problems.append(f"{repo}: pushed_at is not a date")
        if p.get("archived"):
            problems.append(f"{repo}: archived (drop it, or list what replaced it)")
    for g in land.get("gaps", []):
        label = str(g.get("en", "?"))[:40]
        if g.get("section") not in sections:
            problems.append(f"gap {label!r}: unknown section")
        for field in ("en", "zh", "missing_en", "missing_zh"):
            if not g.get(field):
                problems.append(f"gap {label!r}: no {field}")
        for c in g.get("closest", []):
            if c.lower() not in seen:
                problems.append(f"gap {label!r}: {c} is not in the list")
        if g.get("ours") and g["ours"] not in {t["name"] for t in doc["tools"]}:
            problems.append(f"gap {label!r}: {g['ours']} is not one of our tools")
    if problems:
        raise SystemExit("landscape.json: " + "; ".join(problems))
    return land


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


# ---- shared wording ---------------------------------------------------------------------------------------------
WORDS = {
    "en": {
        "site": "site",
        "code": "code",
        "ours": "ours",
        "project": "Project",
        "what": "What it does",
        "stars": "Stars",
        "licence": "Licence",
        "updated": "Updated",
        "list": "a list",
        "none": "none",
        "other": "other",
        "closest": "Closest",
        "partly": "Partly covered by our",
        "missing": "What they miss",
    },
    "zh": {
        "site": "网站",
        "code": "代码",
        "ours": "我们的",
        "project": "项目",
        "what": "用途",
        "stars": "星数",
        "licence": "许可证",
        "updated": "更新",
        "list": "清单",
        "none": "无",
        "other": "其他",
        "closest": "最接近的",
        "partly": "部分已由我们的工具覆盖：",
        "missing": "不足之处",
    },
}


def stars(n: int) -> str:
    return str(n) if n < 1000 else f"{n / 1000:.1f}k".replace(".0k", "k") if n < 100_000 else f"{n // 1000}k"


def licence(p: dict, lang: str) -> str:
    lic = p.get("license")
    return WORDS[lang]["none"] if lic is None else WORDS[lang]["other"] if lic == "NOASSERTION" else lic


def short(repo: str) -> str:
    return repo.split("/", 1)[1]


def by_section(doc: dict, land: dict) -> list[tuple[dict, list[tuple[dict, list[dict], list[dict]]]]]:
    """[(stage, [(section, our tools, other projects)])], in the order of the work; empty sections left out."""
    out = []
    for s in doc["stages"]:
        secs = []
        for sec in (x for x in land["sections"] if x["stage"] == s["key"]):
            ours = [t for t in doc["tools"] if t["section"] == sec["key"]]
            others = sorted((p for p in land["projects"] if p["section"] == sec["key"]), key=lambda p: -p["stars"])
            if ours or others:
                secs.append((sec, ours, others))
        if secs:
            out.append((s, secs))
    return out


def md_cell(text: str) -> str:
    return text.replace("|", "\\|")


def readme_section(doc: dict, land: dict, lang: str) -> str:
    w = WORDS[lang]
    lines = [
        (
            f'Stars, licences and update months of the other projects: GitHub API, {land["checked"]}. A licence of "none" means '
            "the repository has no licence file: ask before reusing it."
            if lang == "en"
            else f"其他项目的星数、许可证和更新月份取自 GitHub API（{land['checked']}）。许可证为“无”表示仓库没有许可证文件，复用前请先询问作者。"
        ),
        "",
    ]
    for stage, secs in by_section(doc, land):
        lines += [f"### {stage[lang]}", ""]
        for sec, ours, others in secs:
            lines += [f"#### {sec[lang]}", ""]
            for t in ours:
                site = f" · [{w['site']}]({t['site']})" if t["site"] else ""
                lines += [
                    f"**[{t['name']}](https://github.com/{OWNER}/{t['name']})** ({w['ours']}){site} — {t[lang]}",
                    "",
                    "```bash",
                    t["command"],
                    "```",
                    "",
                ]
            if others:
                lines += [f"| {w['project']} | {w['what']} | {w['stars']} | {w['licence']} | {w['updated']} |", "|---|---|--:|---|---|"]
                for p in others:
                    tag = f" ({w['list']})" if lang == "en" and p.get("list") else f"（{w['list']}）" if p.get("list") else ""
                    lines.append(
                        f"| [{short(p['repo'])}](https://github.com/{p['repo']}){tag} | {md_cell(p[lang])} | {stars(p['stars'])} | {licence(p, lang)} | {p['pushed_at'][:7]} |"
                    )
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def gaps_section(doc: dict, land: dict, lang: str) -> str:
    w = WORDS[lang]
    names = {s["key"]: s[lang] for s in land["sections"]}
    lines = []
    for g in land["gaps"]:
        closest = ", ".join(f"[{short(c)}](https://github.com/{c})" for c in g["closest"])
        ours = ""
        if g.get("ours"):
            ours = (
                f" {w['partly']} [{g['ours']}](https://github.com/{OWNER}/{g['ours']})."
                if lang == "en"
                else f"{w['partly']}[{g['ours']}](https://github.com/{OWNER}/{g['ours']})。"
            )
        sep = ": " if lang == "en" else "："
        end = "." if lang == "en" else "。"
        lines.append(
            f"- **{g[lang]}** ({names[g['section']]}) {w['missing']}{sep}{g['missing_' + lang]} {w['closest']}{sep}{closest}{end}{ours}"
            if lang == "en"
            else f"- **{g[lang]}**（{names[g['section']]}）{w['missing']}{sep}{g['missing_' + lang]}{w['closest']}{sep}{closest}{end}{ours}"
        )
    return "\n".join(lines) + "\n"


TZ = re.compile(r"^(?:AoE|UTC([+-]\d{1,2})(?::?(\d{2}))?)$")


def load_deadlines(path: Path | None = None) -> dict:
    """deadlines.json (from scripts/refresh_deadlines.py), checked: dates that parse, time zones it knows."""
    doc = json.loads((path or ROOT / "deadlines.json").read_text(encoding="utf-8"))
    dt.date.fromisoformat(doc["checked"])
    for v in doc["venues"]:
        if not v.get("name"):
            raise SystemExit("deadlines.json: a venue without a name")
        for ed in v["editions"]:
            if not TZ.match(ed["timezone"]):
                raise SystemExit(f"deadlines.json: {v['name']} {ed['year']}: time zone {ed['timezone']!r}")
            for t in ed["timeline"]:
                for k in ("abstract_deadline", "deadline"):
                    if k in t:
                        utc(t[k], ed["timezone"])
    return doc


def utc(when: str, tz: str) -> dt.datetime:
    """A deadline in its time zone ("AoE" is UTC-12), as UTC.

    >>> utc("2026-05-07 23:59:59", "AoE").isoformat(), utc("2026-01-29 11:59:59", "UTC+0").isoformat()
    ('2026-05-08T11:59:59', '2026-01-29T11:59:59')
    """
    m = TZ.match(tz)
    if not m:
        raise ValueError(tz)
    hours = -12 if tz == "AoE" else int(m.group(1))
    minutes = int(m.group(2) or 0) * (1 if hours >= 0 else -1)
    local = dt.datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
    return local - dt.timedelta(hours=hours, minutes=minutes)


def upcoming(dl: dict) -> list[tuple[dict, dict, dict, dt.datetime]]:
    """(venue, edition, deadline, its time in UTC) for each venue's next deadline after the check date (or its last one,
    when none is announced yet), soonest first; venues with nothing ahead come last."""
    checked = dt.datetime.fromisoformat(dl["checked"])
    rows = []
    for v in dl["venues"]:
        items = [(ed, t, utc(t["deadline"], ed["timezone"])) for ed in v["editions"] for t in ed["timeline"]]
        if not items:
            continue
        ahead = sorted((x for x in items if x[2] >= checked), key=lambda x: x[2])
        ed, t, when = ahead[0] if ahead else max(items, key=lambda x: x[2])
        rows.append((v, ed, t, when))
    return sorted(rows, key=lambda r: (r[3] < checked, abs((r[3] - checked).total_seconds())))


def _rules_text(v: dict, lang: str) -> str:
    r = v.get("rules")
    if not r:
        return "—"
    pages = f"{r['pages']}" + (f" ({r['camera_ready']})" if r.get("camera_ready") else "")
    req = ("; " + ("requires " if lang == "en" else "必需：") + ", ".join(r["required"])) if r["required"] else ""
    unit = " pages" if lang == "en" else " 页"
    return f"{pages}{unit}{req}"


def _policy_text(v: dict, lang: str) -> str:
    """LLM use, supplementary material, author response: what the venue's page says (English, as quoted)."""
    pol = (v.get("rules") or {}).get("policy") or {}
    labels = {"llm": ("LLMs", "大模型"), "supplementary": ("supplementary", "补充材料"), "rebuttal": ("response", "回复")}
    parts = [f"{labels[k][0 if lang == 'en' else 1]}: {pol[k]}" for k in ("llm", "supplementary", "rebuttal") if pol.get(k)]
    return "; ".join(parts) or "—"


def deadlines_section(dl: dict, lang: str) -> str:
    """The README's table: each venue's next deadline as of the check date, with its rules."""
    checked = dt.datetime.fromisoformat(dl["checked"])
    if lang == "en":
        head = "| Venue | Next deadline | Time zone | Conference | Pages (camera-ready); required | LLM use, supplementary, response | Rules |\n|---|---|---|---|---|---|---|\n"
    else:
        head = "| 会议 | 下一个截稿日 | 时区 | 会议时间地点 | 页数（终稿）；必需 | 大模型、补充材料、回复 | 规则 |\n|---|---|---|---|---|---|---|\n"
    rows = []
    for v, ed, t, when in upcoming(dl):
        date = t["deadline"][:16] + (f" ({t['comment']})" if t.get("comment") else "")
        if "abstract_deadline" in t:
            date = (f"abstract {t['abstract_deadline'][:10]}, paper " if lang == "en" else f"摘要 {t['abstract_deadline'][:10]}，全文 ") + date
        if when < checked:
            date = ("last: " if lang == "en" else "上一届：") + date
        name = f"[{v['name']} {ed['year']}]({ed['link']})" if ed["link"] else f"{v['name']} {ed['year']}"
        conf = md_cell(", ".join(x for x in (ed["date"], ed["place"]) if x))
        r = v.get("rules")
        rules = f"[`--venue {r['id']}`]({r['source']})" if r else "—"
        rows.append(
            f"| {name} | {md_cell(date)} | {ed['timezone']} | {conf} | {md_cell(_rules_text(v, lang))} | {md_cell(_policy_text(v, lang))} | {rules} |"
        )
    src = dl["sources"]["deadlines"]
    if lang == "en":
        note = (
            f"\nDeadlines as of {dl['checked']}, from [ccf-deadlines](https://github.com/{src['repo']}) (MIT, commit "
            f"`{src['commit'][:7]}`); always confirm on the venue's own page. Page limits and required sections are "
            "submit-check's rules, each with the official page it comes from, as are the LLM policies, supplementary material and author "
            "response (`--venue` checks a paper against them; a "
            "venue's rules are for the year in its id). The [site](https://zch6a.github.io/research-kit/#en-deadlines) "
            "counts the days left.\n"
        )
    else:
        note = (
            f"\n截稿日期截至 {dl['checked']}，取自 [ccf-deadlines](https://github.com/{src['repo']})（MIT，提交 "
            f"`{src['commit'][:7]}`），请以会议官网为准。页数、必需章节、大模型政策、补充材料和作者回复来自 submit-check 的规则，每条都注明官方出处"
            "（`--venue` 按它检查论文；规则对应 id 里的年份）。[网站](https://zch6a.github.io/research-kit/#zh-deadlines)上会显示剩余天数。\n"
        )
    return head + "\n".join(rows) + "\n" + note


def site_deadlines(dl: dict, lang: str) -> tuple[str, str]:
    """(nav link, section) for the site: the same table, with each deadline's UTC time for deadlines.js."""
    e = html.escape
    checked = dt.datetime.fromisoformat(dl["checked"])
    title = "Deadlines and venue rules" if lang == "en" else "截稿日期与会议规则"
    w = {
        "en": ("Venue", "Next deadline", "Conference", "Pages (camera-ready); required", "LLM use, supplementary, response", "Rules"),
        "zh": ("会议", "下一个截稿日", "会议时间地点", "页数（终稿）；必需", "大模型、补充材料、回复", "规则"),
    }[lang]
    rows = []
    items = upcoming(dl)
    for v, ed, t, when in items:
        date = e(t["deadline"][:16]) + f" {e(ed['timezone'])}"
        if t.get("comment"):
            date += f" <span class='where'>{e(t['comment'])}</span>"
        if "abstract_deadline" in t:
            date = (("abstract " if lang == "en" else "摘要 ") + e(t["abstract_deadline"][:10]) + "<br>") + date
        past = when < checked
        name = f'<a href="{e(ed["link"])}">{e(v["name"])} {ed["year"]}</a>' if ed["link"] else f"{e(v['name'])} {ed['year']}"
        r = v.get("rules")
        rules = f'<a href="{e(r["source"])}"><code>--venue {e(r["id"])}</code></a>' if r else "—"
        conf = e(", ".join(x for x in (ed["date"], ed["place"]) if x))
        rows.append(
            f'<tr{" class=past" if past else ""}><td>{name}</td><td><time data-utc="{when.isoformat()}Z">{date}</time>'
            f'<span class="left"></span></td><td>{conf}</td><td>{e(_rules_text(v, lang))}</td><td>{e(_policy_text(v, lang))}</td><td>{rules}</td></tr>'
        )
    src = dl["sources"]["deadlines"]
    note = (
        f"Deadlines as of {dl['checked']} from <a href='https://github.com/{src['repo']}'>ccf-deadlines</a> (MIT); always confirm on the venue's page. "
        "Page limits and required sections: submit-check's rules, with their official sources."
        if lang == "en"
        else f"截稿日期截至 {dl['checked']}，取自 <a href='https://github.com/{src['repo']}'>ccf-deadlines</a>（MIT），请以会议官网为准。页数和必需章节来自 submit-check 的规则，均注明官方出处。"
    )
    section = (
        f'<section id="{lang}-deadlines"><h2>{title}</h2><p class="note">{note}</p><div class="table"><table><thead><tr>'
        + "".join(f"<th>{x}</th>" for x in w)
        + f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>"
    )
    nav = f'<a href="#{lang}-deadlines">{title} <span>{len(items)}</span></a>'
    return nav, section


def fill(path: Path, section: str, which: str = "tools", text: str | None = None) -> str:
    start, end = MARKERS[which]
    text = path.read_text(encoding="utf-8") if text is None else text
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        raise SystemExit(f"{path.name}: no {start} ... {end} markers")
    return pattern.sub(lambda _: f"{start}\n{section}{end}", text)


TEASER = {
    # real output from the tools' READMEs, for those without a screenshot
    "table-trace": "$ table-trace compare 1512.03385 2201.03545 ...\n     20.74 (lower is better)  ResNet-50 | top-1 err.\n     76.13  2201.03545 Table 10: ResNet-50 (PyTorch)\n     78.82 ± 0.07  ResNet-50 (enhanced recipe)",
    "repro-score": "$ repro-score path/to/repo\nrepro-score: paper-code: 65/100\nDependencies  11/20\n  ~ versions pinned (2 of 5)   4/7\n      requirements.txt:4: pyyaml",
    "rebuttal-board": "$ rebuttal status\nRebuttal: SMA: 8 points, 1 done, 2 doing, 4 todo\nScores changed: Qm2t 6 -> 7 (+1)\nxK9p  rating 5  2/5 answered  reply 208 / 5,000",
}
STAGE_ICON = {  # 24x24 outline icons, drawn here (no icon font)
    "read": '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5zM4 20.5A2.5 2.5 0 0 0 6.5 23H20v-5"/>',
    "experiment": '<path d="M9 3h6M10 3v6l-5.5 9.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-2.5L14 9V3"/><path d="M7.5 15h9"/>',
    "write": '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
    "submit": '<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/>',
    "after": '<path d="M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.6 6.6 19.5l1.2-6-4.5-4.2 6.1-.7z"/>',
}
UI = {
    "en": {
        "tagline": "Open tools for every step of research",
        "lead": "From following new papers to after publication: {n} tools of ours, each a command and an agent skill, and {m} of the best open projects on GitHub, chosen stage by stage. Rules and public data; no language model reads your paper.",
        "browse": "Browse the tools",
        "install": "Add to Claude Code",
        "github": "GitHub",
        "copy": "Copy",
        "copied": "Copied",
        "stat_tools": "tools of ours",
        "stat_projects": "projects from GitHub",
        "stat_venues": "venues with deadlines",
        "stat_needs": "open needs",
        "ours_title": "Our tools",
        "ours_sub": "Each runs from one command with uv, needs no account, and comes with a skill for Claude Code and other agents.",
        "all": "All",
        "landscape": "The best of the rest",
        "landscape_sub": "Open projects for each stage, with stars, licence and last update from the GitHub API on {checked}. A licence marked “none” means the repository has none: ask before reusing it.",
        "search": "Filter projects…",
        "nav_tools": "Tools",
        "nav_landscape": "Landscape",
        "nav_deadlines": "Deadlines",
        "nav_needs": "Open needs",
        "install_title": "Install as agent skills",
        "install_body": "Our tools need uv (gpu-budget: Node 22+). In Claude Code, add the marketplace once, then install the tools you want by name:",
        "needs_sub": "Needs that came up while surveying each stage, with the closest projects and what they miss. A badge marks those our tools partly cover.",
        "footer": "MIT · suggest a project in an issue",
        "noresults": "No project matches.",
        "site": "Site",
        "code": "Code",
    },
    "zh": {
        "tagline": "科研每一步的开源工具",
        "lead": "从跟踪新论文到论文发表之后：我们自己的 {n} 个工具（每个都是一条命令和一个智能体技能），以及按阶段挑选的 GitHub 上最好的 {m} 个开源项目。只用规则和公开数据，不让大模型读你的论文。",
        "browse": "看看这些工具",
        "install": "装进 Claude Code",
        "github": "GitHub",
        "copy": "复制",
        "copied": "已复制",
        "stat_tools": "个我们的工具",
        "stat_projects": "个 GitHub 项目",
        "stat_venues": "个会议的截稿日",
        "stat_needs": "个待满足的需求",
        "ours_title": "我们的工具",
        "ours_sub": "每个工具都用 uv 一条命令运行，不需要注册账号，并附带给 Claude Code 等智能体用的技能。",
        "all": "全部",
        "landscape": "其他优秀项目",
        "landscape_sub": "每个阶段可用的开源项目，星数、许可证和最近更新取自 GitHub API（{checked}）。许可证为“无”表示仓库没有许可证文件，复用前请先询问作者。",
        "search": "筛选项目…",
        "nav_tools": "工具",
        "nav_landscape": "项目全景",
        "nav_deadlines": "截稿日",
        "nav_needs": "待满足的需求",
        "install_title": "作为智能体技能安装",
        "install_body": "我们的工具需要先装 uv（gpu-budget 需要 Node 22+）。在 Claude Code 里先添加一次插件市场，再按名字安装需要的工具：",
        "needs_sub": "按阶段调研时发现、目前没有工具完全满足的需求，附最接近的项目和它们缺少的部分。带标记的是我们的工具已部分覆盖的。",
        "footer": "MIT · 推荐项目请提 issue",
        "noresults": "没有匹配的项目。",
        "site": "网站",
        "code": "代码",
    },
}


def _icon(stage: str, size: int = 18) -> str:
    return (f'<svg class="icon" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{STAGE_ICON.get(stage, "")}</svg>')  # fmt: skip


def _picture(name: str) -> str:
    """The tool's picture in site/img (made by scripts/thumbs.py), or a terminal card with real output."""
    e = html.escape
    for ext in ("webp", "svg", "png"):
        if (ROOT / "site" / "img" / f"{name}.{ext}").is_file():
            return f'<div class="shot"><img src="img/{name}.{ext}" alt="" loading="lazy" decoding="async"></div>'
    if name in TEASER:
        return f'<div class="shot term"><pre>{e(TEASER[name])}</pre></div>'
    return '<div class="shot term"><pre></pre></div>'


def _blurb(text: str) -> str:
    """The description's first sentence (the card shows it whole; the rest is on the repository)."""
    m = re.match(r"(.+?[.!?。])(?:\s|$)", text)
    return m.group(1) if m and len(m.group(1)) > 40 else text


def site(doc: dict, land: dict, dl: dict | None = None) -> str:
    e = html.escape
    n_ours, n_others = len(doc["tools"]), len(land["projects"])
    n_venues = len(dl["venues"]) if dl else 0
    stage_of = {s["key"]: s for s in doc["stages"]}
    body: dict[str, list[str]] = {"en": [], "zh": []}
    for lang in ("en", "zh"):
        w, u = WORDS[lang], UI[lang]
        # hero
        stats = [(n_ours, u["stat_tools"]), (n_others, u["stat_projects"]), (n_venues, u["stat_venues"]), (len(land["gaps"]), u["stat_needs"])]
        flow = "".join(
            f'<button type="button" class="step" data-stage="{st["key"]}" data-s="{st["key"]}">{_icon(st["key"], 22)}'
            f"<span>{e(st[lang])}</span><b>{sum(t['stage'] == st['key'] for t in doc['tools'])}</b></button>"
            for st in doc["stages"]
        )
        body[lang].append(
            f'<section class="hero"><p class="kicker">research-kit</p><h1>{e(u["tagline"])}</h1>'
            f'<p class="lead">{e(u["lead"].format(n=n_ours, m=n_others))}</p>'
            f'<div class="cta"><a class="btn primary" href="#{lang}-tools">{e(u["browse"])}</a>'
            f'<button type="button" class="btn copy" data-copy="/plugin marketplace add {OWNER}/research-kit" data-done="{e(u["copied"])}">{e(u["install"])}</button>'
            f'<a class="btn ghost" href="https://github.com/{OWNER}/research-kit">{e(u["github"])} ↗</a></div>'
            f'<ul class="stats">{"".join(f"<li><b>{n}</b><span>{e(t)}</span></li>" for n, t in stats)}</ul>'
            f'<div class="flow" role="group" aria-label="stages">{flow}</div></section>'
        )
        # our tools
        cards = []
        for t in doc["tools"]:
            st = stage_of[t["stage"]]
            links = [f'<a href="https://github.com/{OWNER}/{t["name"]}">{e(u["code"])}</a>']
            if t["site"]:
                links.append(f'<a href="{e(t["site"])}">{e(u["site"])} ↗</a>')
            first = t["command"].split("\n")[0]
            cards.append(
                f'<article class="tool" data-stage="{t["stage"]}" data-s="{t["stage"]}">{_picture(t["name"])}'
                f'<div class="body"><p class="stage">{_icon(t["stage"], 14)}{e(st[lang])}</p><h3>{e(t["name"])}</h3>'
                f'<p class="desc">{e(t[lang])}</p>'
                f'<div class="cmd"><code>{e(first)}</code><button type="button" class="mini copy" data-copy="{e(t["command"])}" '
                f'data-done="{e(u["copied"])}" aria-label="{e(u["copy"])}">{e(u["copy"])}</button></div>'
                f'<p class="links">{" · ".join(links)}</p></div></article>'
            )
        body[lang].append(
            f'<section id="{lang}-tools" class="block"><div class="head"><h2>{e(u["ours_title"])}</h2><p>{e(u["ours_sub"])}</p></div>'
            f'<div class="filters" role="tablist"><button type="button" class="chip on" data-filter="all">{e(u["all"])}</button>'
            + "".join(
                f'<button type="button" class="chip" data-filter="{st["key"]}" data-s="{st["key"]}">{e(st[lang])}</button>' for st in doc["stages"]
            )
            + f'</div><div class="tools">{"".join(cards)}</div>'
            f'<div class="install"><h3>{e(u["install_title"])}</h3><p>{e(u["install_body"])}</p>'
            f'<div class="cmd big"><code>/plugin marketplace add {OWNER}/research-kit<br>/plugin install {EXAMPLE}@research-kit</code>'
            f'<button type="button" class="mini copy" data-copy="/plugin marketplace add {OWNER}/research-kit&#10;/plugin install {EXAMPLE}@research-kit" '
            f'data-done="{e(u["copied"])}">{e(u["copy"])}</button></div></div></section>'
        )
        # the landscape
        parts = []
        for stage, secs in by_section(doc, land):
            rows = []
            for sec, _ours, others in secs:
                for p in others:
                    tag = f' <span class="tag">{w["list"]}</span>' if p.get("list") else ""
                    lic = licence(p, lang)
                    lic_html = f'<span class="warn">{e(lic)}</span>' if p.get("license") is None else e(lic)
                    rows.append(
                        f'<tr data-stage="{stage["key"]}"><td><a href="https://github.com/{e(p["repo"])}">{e(short(p["repo"]))}</a>{tag}'
                        f'<span class="sec">{e(sec[lang])}</span></td><td>{e(p[lang])}</td><td class="num">{stars(p["stars"])}</td>'
                        f'<td>{lic_html}</td><td class="num">{p["pushed_at"][:7]}</td></tr>'
                    )
            parts.append(
                f'<section id="{lang}-{stage["key"]}" class="stagebox" data-stage="{stage["key"]}" data-s="{stage["key"]}">'
                f'<h3>{_icon(stage["key"], 18)}{e(stage[lang])}</h3><div class="table"><table><thead><tr><th>{w["project"]}</th><th>{w["what"]}</th>'
                f'<th class="num">{w["stars"]}</th><th>{w["licence"]}</th><th class="num">{w["updated"]}</th></tr></thead>'
                f"<tbody>{''.join(rows)}</tbody></table></div></section>"
            )
        body[lang].append(
            f'<section id="{lang}-landscape" class="block"><div class="head"><h2>{e(u["landscape"])}</h2>'
            f"<p>{e(u['landscape_sub'].format(checked=land['checked']))}</p></div>"
            f'<div class="toolbar"><input type="search" class="search" placeholder="{e(u["search"])}" aria-label="{e(u["search"])}">'
            f'<div class="filters">'
            + f'<button type="button" class="chip on" data-filter="all">{e(u["all"])}</button>'
            + "".join(
                f'<button type="button" class="chip" data-filter="{st["key"]}" data-s="{st["key"]}">{e(st[lang])}</button>' for st in doc["stages"]
            )
            + f'</div></div>{"".join(parts)}<p class="empty" hidden>{e(u["noresults"])}</p></section>'
        )
        # deadlines
        if dl is not None:
            _, dl_section = site_deadlines(dl, lang)
            body[lang].append(dl_section.replace(f'<section id="{lang}-deadlines">', f'<section id="{lang}-deadlines" class="block">', 1))
        # open needs
        names = {sec["key"]: sec[lang] for sec in land["sections"]}
        items = []
        for g in land["gaps"]:
            closest = ", ".join(f'<a href="https://github.com/{e(c)}">{e(short(c))}</a>' for c in g["closest"])
            ours = (
                f'<span class="ours">{w["partly"]} <a href="https://github.com/{OWNER}/{g["ours"]}">{g["ours"]}</a></span>' if g.get("ours") else ""
            )
            items.append(
                f'<li><p class="where">{e(names[g["section"]])}</p><h4>{e(g[lang])}</h4><p>{e(g["missing_" + lang])}</p>'
                f'<p class="small">{w["closest"]}: {closest}</p>{ours}</li>'
            )
        gap_title = "What nothing covers yet" if lang == "en" else "还没有工具覆盖的需求"
        body[lang].append(
            f'<section id="{lang}-gaps" class="block"><div class="head"><h2>{gap_title}</h2><p>{e(u["needs_sub"])}</p></div>'
            f'<ul class="gaps">{"".join(items)}</ul></section>'
        )
    nav = {lang: " ".join(f'<a href="#{lang}-{k}">{e(UI[lang]["nav_" + n])}</a>' for k, n in (("tools", "tools"), ("landscape", "landscape"), ("deadlines", "deadlines"), ("gaps", "needs")))
           for lang in ("en", "zh")}  # fmt: skip
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'">
<title>research-kit · open tools for every step of research</title>
<meta name="description" content="Open-source tools for every stage of research work: {n_ours} of ours and {n_others} more from GitHub, stage by stage, with deadlines and what nothing covers yet.">
<meta property="og:title" content="research-kit: open tools for every step of research">
<meta property="og:description" content="{n_ours} open tools of ours and {n_others} of the best projects on GitHub, from following new papers to after publication.">
<meta property="og:image" content="https://{OWNER}.github.io/research-kit/img/social.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%232563eb'/%3E%3Cpath d='M9 22V10h6a4 4 0 0 1 0 8h-6m6 0 5 4' stroke='white' stroke-width='3' fill='none' stroke-linecap='round'/%3E%3C/svg%3E">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="bar"><div class="inner"><a class="brand" href="#">research-kit</a>
<nav data-lang="en">{nav["en"]}</nav><nav data-lang="zh" lang="zh-CN" hidden>{nav["zh"]}</nav>
<button type="button" id="lang" lang="zh-CN" hidden>中文</button></div></header>
<main>
<div data-lang="en">{"".join(body["en"])}</div>
<div data-lang="zh" lang="zh-CN" hidden>{"".join(body["zh"])}</div>
</main>
<footer><p>MIT · <a href="https://github.com/{OWNER}/research-kit">github.com/{OWNER}/research-kit</a> · <span data-lang="en">{e(UI["en"]["footer"].split(" · ")[1])}</span><span data-lang="zh" lang="zh-CN" hidden>{e(UI["zh"]["footer"].split(" · ")[1])}</span></p></footer>
<script src="lang.js"></script>
<script src="deadlines.js"></script>
<script src="app.js"></script>
</body>
</html>
"""


def count(text: str, n: int, others: int | None = None) -> str:
    """The README's badges with how many tools and projects there are (outside the markers)."""
    text = re.sub(
        r'<img alt="\d+ tools" src="https://img.shields.io/badge/tools-\d+-',
        f'<img alt="{n} tools" src="https://img.shields.io/badge/tools-{n}-',
        text,
    )
    if others is not None:
        text = re.sub(
            r'<img alt="\d+ projects" src="https://img.shields.io/badge/projects-\d+-',
            f'<img alt="{others} projects" src="https://img.shields.io/badge/projects-{others}-',
            text,
        )
    return text


def readme(path: Path, doc: dict, land: dict, lang: str, dl: dict | None = None) -> str:
    text = fill(path, readme_section(doc, land, lang), "tools")
    text = fill(path, gaps_section(doc, land, lang), "gaps", text)
    if dl is not None:
        text = fill(path, deadlines_section(dl, lang), "deadlines", text)
    return count(text, len(doc["tools"]), len(land["projects"]))


def outputs(doc: dict, land: dict | None = None, dl: dict | None = None) -> dict[Path, str]:
    land = land or load_landscape(doc)
    return {
        ROOT / ".claude-plugin" / "marketplace.json": marketplace(doc),
        ROOT / "README.md": readme(ROOT / "README.md", doc, land, "en", dl),
        ROOT / "README.zh-CN.md": readme(ROOT / "README.zh-CN.md", doc, land, "zh", dl),
        ROOT / "site" / "index.html": site(doc, land, dl),
    }


def main() -> int:
    check = "--check" in sys.argv[1:]
    stale = []
    doc = load()
    files = outputs(doc, load_landscape(doc), load_deadlines())
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
