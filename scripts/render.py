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


def deadlines_section(dl: dict, lang: str) -> str:
    """The README's table: each venue's next deadline as of the check date, with its rules."""
    checked = dt.datetime.fromisoformat(dl["checked"])
    if lang == "en":
        head = "| Venue | Next deadline | Time zone | Conference | Pages (camera-ready); required | Rules |\n|---|---|---|---|---|---|\n"
    else:
        head = "| 会议 | 下一个截稿日 | 时区 | 会议时间地点 | 页数（终稿）；必需 | 规则 |\n|---|---|---|---|---|---|\n"
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
        rows.append(f"| {name} | {md_cell(date)} | {ed['timezone']} | {conf} | {md_cell(_rules_text(v, lang))} | {rules} |")
    src = dl["sources"]["deadlines"]
    if lang == "en":
        note = (
            f"\nDeadlines as of {dl['checked']}, from [ccf-deadlines](https://github.com/{src['repo']}) (MIT, commit "
            f"`{src['commit'][:7]}`); always confirm on the venue's own page. Page limits and required sections are "
            "submit-check's rules, each with the official page it comes from (`--venue` checks a paper against them; a "
            "venue's rules are for the year in its id). The [site](https://zch6a.github.io/research-kit/#en-deadlines) "
            "counts the days left.\n"
        )
    else:
        note = (
            f"\n截稿日期截至 {dl['checked']}，取自 [ccf-deadlines](https://github.com/{src['repo']})（MIT，提交 "
            f"`{src['commit'][:7]}`），请以会议官网为准。页数和必需章节是 submit-check 的规则，每条都注明官方出处"
            "（`--venue` 按它检查论文；规则对应 id 里的年份）。[网站](https://zch6a.github.io/research-kit/#zh-deadlines)上会显示剩余天数。\n"
        )
    return head + "\n".join(rows) + "\n" + note


def site_deadlines(dl: dict, lang: str) -> tuple[str, str]:
    """(nav link, section) for the site: the same table, with each deadline's UTC time for deadlines.js."""
    e = html.escape
    checked = dt.datetime.fromisoformat(dl["checked"])
    title = "Deadlines and venue rules" if lang == "en" else "截稿日期与会议规则"
    w = {
        "en": ("Venue", "Next deadline", "Conference", "Pages (camera-ready); required", "Rules"),
        "zh": ("会议", "下一个截稿日", "会议时间地点", "页数（终稿）；必需", "规则"),
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
            f'<span class="left"></span></td><td>{conf}</td><td>{e(_rules_text(v, lang))}</td><td>{rules}</td></tr>'
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


def site(doc: dict, land: dict, dl: dict | None = None) -> str:
    e = html.escape
    n_ours, n_others = len(doc["tools"]), len(land["projects"])
    body: dict[str, list[str]] = {"en": [], "zh": []}
    nav: dict[str, list[str]] = {"en": [], "zh": []}
    for lang in ("en", "zh"):
        w = WORDS[lang]
        for stage, secs in by_section(doc, land):
            total = sum(len(o) + len(x) for _, o, x in secs)
            unit = " projects" if lang == "en" else " 个项目"
            nav[lang].append(f'<a href="#{lang}-{stage["key"]}">{e(stage[lang])} <span>{total}<span class="sr">{unit}</span></span></a>')
            parts = [f'<section id="{lang}-{stage["key"]}"><h2>{e(stage[lang])}</h2>']
            for sec, ours, others in secs:
                parts.append(f'<h3 id="{lang}-{stage["key"]}-{sec["key"]}">{e(sec[lang])}</h3>')
                if ours:
                    cards = []
                    for t in ours:
                        links = [f'<a href="https://github.com/{OWNER}/{t["name"]}">{w["code"]}</a>']
                        if t["site"]:
                            links.append(f'<a href="{e(t["site"])}">{w["site"]}</a>')
                        cards.append(
                            f'<article><h4>{e(t["name"])} <span class="ours">{w["ours"]}</span></h4><p>{e(t[lang])}</p>'
                            f'<pre><code>{e(t["command"])}</code></pre><p class="links">{" · ".join(links)}</p></article>'
                        )
                    parts.append(f'<div class="grid">{"".join(cards)}</div>')
                if others:
                    rows = []
                    for p in others:
                        tag = f' <span class="tag">{w["list"]}</span>' if p.get("list") else ""
                        lic = licence(p, lang)
                        lic_html = f'<span class="warn">{e(lic)}</span>' if p.get("license") is None else e(lic)
                        rows.append(
                            f'<tr><td><a href="https://github.com/{e(p["repo"])}">{e(short(p["repo"]))}</a>{tag}</td><td>{e(p[lang])}</td>'
                            f'<td class="num">{stars(p["stars"])}</td><td>{lic_html}</td><td class="num">{p["pushed_at"][:7]}</td></tr>'
                        )
                    parts.append(
                        f'<div class="table"><table><thead><tr><th>{w["project"]}</th><th>{w["what"]}</th><th class="num">{w["stars"]}</th>'
                        f'<th>{w["licence"]}</th><th class="num">{w["updated"]}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
                    )
            parts.append("</section>")
            body[lang].append("".join(parts))
        gap_items = []
        names = {s["key"]: s[lang] for s in land["sections"]}
        for g in land["gaps"]:
            closest = ", ".join(f'<a href="https://github.com/{e(c)}">{e(short(c))}</a>' for c in g["closest"])
            ours = (
                f' <span class="ours">{w["partly"]} <a href="https://github.com/{OWNER}/{g["ours"]}">{g["ours"]}</a></span>' if g.get("ours") else ""
            )
            gap_items.append(
                f'<li><strong>{e(g[lang])}</strong> <span class="where">{e(names[g["section"]])}</span>'
                f"<br>{e(g['missing_' + lang])} {w['closest']}: {closest}.{ours}</li>"
            )
        if dl is not None:
            dl_nav, dl_section = site_deadlines(dl, lang)
            nav[lang].append(dl_nav)
            body[lang].append(dl_section)
        gap_title = "What nothing covers yet" if lang == "en" else "还没有工具覆盖的需求"
        nav[lang].append(f'<a href="#{lang}-gaps">{gap_title} <span>{len(land["gaps"])}</span></a>')
        body[lang].append(f'<section id="{lang}-gaps"><h2>{gap_title}</h2><ul class="gaps">{"".join(gap_items)}</ul></section>')
    checked = land["checked"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'">
<title>research-kit</title>
<meta name="description" content="Open-source tools for every stage of research work: {n_ours} of ours and {n_others} more from GitHub, stage by stage, and what nothing covers yet.">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <h1>research-kit</h1>
  <p class="lead" data-lang="en">Open-source tools for every stage of research work, from following new papers to after publication: {n_ours} of ours (each a command and an agent skill) and {n_others} more from GitHub, chosen stage by stage, with what nothing covers yet.</p>
  <p class="lead" data-lang="zh" lang="zh-CN" hidden>科研每个阶段可用的开源工具，从跟踪新论文到论文发表之后：我们自己的 {n_ours} 个（每个都是一条命令和一个智能体技能），以及按阶段挑选的 GitHub 上另外 {n_others} 个项目，还有目前没有工具覆盖的需求。</p>
  <nav aria-label="Stages" data-lang="en" class="stages">{"".join(nav["en"])}</nav>
  <nav aria-label="阶段" data-lang="zh" lang="zh-CN" class="stages" hidden>{"".join(nav["zh"])}</nav>
  <p><button type="button" id="lang" lang="zh-CN" hidden>中文</button></p>
  <div class="install">
    <p data-lang="en">Our tools need <a href="https://docs.astral.sh/uv/">uv</a> (gpu-budget: Node 22+). As agent skills in Claude Code, add the marketplace once, then install the tools you want by name:</p>
    <p data-lang="zh" lang="zh-CN" hidden>我们的工具需要先装 <a href="https://docs.astral.sh/uv/">uv</a>（gpu-budget 需要 Node 22+）。作为 Claude Code 的技能使用时，先添加一次插件市场，再按名字安装需要的工具：</p>
    <pre><code>/plugin marketplace add {OWNER}/research-kit
/plugin install {EXAMPLE}@research-kit</code></pre>
    <p class="note" data-lang="en">Stars, licences and update months of the other projects are from the GitHub API on {checked}. A licence marked "none" means the repository has no licence file: ask before reusing it.</p>
    <p class="note" data-lang="zh" lang="zh-CN" hidden>其他项目的星数、许可证和更新月份取自 GitHub API（{checked}）。许可证为“无”表示仓库没有许可证文件，复用前请先询问作者。</p>
  </div>
</header>
<main>
<div data-lang="en">{"".join(body["en"])}</div>
<div data-lang="zh" lang="zh-CN" hidden>{"".join(body["zh"])}</div>
</main>
<footer><p>MIT · <a href="https://github.com/{OWNER}/research-kit">github.com/{OWNER}/research-kit</a> · <span data-lang="en">suggest a project in an issue</span><span data-lang="zh" lang="zh-CN" hidden>推荐项目请提 issue</span></p></footer>
<script src="lang.js"></script>
<script src="deadlines.js"></script>
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
