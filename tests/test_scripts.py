"""The two scripts, without the network: render.py on made-up lists, check_skills.py with a made-up GitHub."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


render = script("render")
check_skills = script("check_skills")

TOOL = {"name": "table-trace", "stage": "read", "en": "Reads <b>things</b> & more.", "zh": "读东西。",
        "command": "uvx --from git+https://github.com/zch6a/table-trace@v0 table-trace x", "tags": ["a"]}  # fmt: skip
STAGES = [{"key": "read", "en": "Read", "zh": "读"}, {"key": "write", "en": "Write", "zh": "写"}]


def write_list(tmp: Path, tools: list[dict]) -> Path:
    p = tmp / "tools.json"
    p.write_text(json.dumps({"stages": STAGES, "tools": tools}), encoding="utf-8")
    return p


def test_the_list_is_checked(tmp_path: Path) -> None:
    doc = render.load(write_list(tmp_path, [dict(TOOL)]))
    assert doc["tools"][0]["site"] == ""
    for broken, why in [
        ({**TOOL, "command": "uvx --from git+https://github.com/zch6a/table-trace table-trace"}, "at v0"),  # not the release the marketplace installs
        ({**TOOL, "stage": "nowhere"}, "unknown stage"),
        ({k: v for k, v in TOOL.items() if k != "zh"}, "no zh"),
        ({**TOOL, "site": "http://x"}, "https link"),
        ({**TOOL, "command": "table-trace x  # see github.com/zch6a/table-trace@v0 x"}, "at v0"),  # only in a comment
        ({**TOOL, "name": "Demo Tool"}, "lowercase"),
        ({**TOOL, "tags": "papers"}, "list of words"),
        ({**TOOL, "command": TOOL["command"] + " ```"}, "code block"),
    ]:
        with pytest.raises(SystemExit, match=why):
            render.load(write_list(tmp_path, [broken]))
    with pytest.raises(SystemExit, match="listed twice"):
        render.load(write_list(tmp_path, [dict(TOOL), dict(TOOL)]))
    assert render.load(write_list(tmp_path, [{**TOOL, "command": "npx github:zch6a/table-trace#v0 run"}]))  # npx at the tag
    with pytest.raises(SystemExit, match="at v0"):
        render.load(write_list(tmp_path, [{**TOOL, "command": "npx github:zch6a/table-trace run"}]))  # the default branch
    bad_stage = tmp_path / "stages.json"
    bad_stage.write_text(json.dumps({"stages": STAGES + [{"key": "read"}], "tools": [TOOL]}), encoding="utf-8")
    with pytest.raises(SystemExit, match="stage read: no en.*stage read: listed twice"):
        render.load(bad_stage)


def test_what_is_generated(tmp_path: Path) -> None:
    doc = render.load(write_list(tmp_path, [dict(TOOL)]))
    market = json.loads(render.marketplace(doc))
    (plugin,) = market["plugins"]
    assert plugin["source"] == {"source": "git-subdir", "url": "zch6a/table-trace", "path": "plugin", "ref": "v0"}
    assert market["name"] == "research-kit" and plugin["homepage"] == "https://github.com/zch6a/table-trace"
    section = render.readme_section(doc, "en")
    assert "### Read" in section and "### Write" not in section  # a stage without tools is left out
    site = render.site(doc)
    assert "Reads &lt;b&gt;things&lt;/b&gt; &amp; more." in site and "<b>things" not in site  # text is escaped
    assert 'id="en-read"' in site and 'href="#en-read"' in site and 'id="en-write"' not in site
    assert "/plugin install table-trace@research-kit" in site and '<div data-lang="zh" lang="zh-CN" hidden>' in site
    assert render.count('<img alt="12 tools" src="https://img.shields.io/badge/tools-12-2ea44f">', 13) == (
        '<img alt="13 tools" src="https://img.shields.io/badge/tools-13-2ea44f">'
    )
    readme = tmp_path / "README.md"
    readme.write_text("x\n<!-- tools:start -->\nold\n<!-- tools:end -->\ny\n", encoding="utf-8")
    assert render.fill(readme, "new\n") == "x\n<!-- tools:start -->\nnew\n<!-- tools:end -->\ny\n"
    readme.write_text("no markers\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="markers"):
        render.fill(readme, "new\n")


def test_the_repository_is_up_to_date() -> None:
    for path, text in render.outputs(render.load()).items():
        assert path.read_text(encoding="utf-8") == text, f"run python scripts/render.py ({path.name} is out of date)"


def fake_github(skills: dict[str, str], plugin_name: str = "table-trace"):
    def fetch(url: str) -> bytes:
        if url.endswith("/.claude-plugin/plugin.json"):
            return json.dumps({"name": plugin_name}).encode()
        if "api.github.com" in url:
            return json.dumps([{"name": n, "type": "dir"} for n in skills]).encode()
        for n, text in skills.items():
            if url.endswith(f"/skills/{n}/SKILL.md"):
                if text is None:
                    raise OSError("404")
                return text.encode()
        raise OSError("404")

    return fetch


MARKET = {"plugins": [{"name": "table-trace", "source": {"source": "git-subdir", "url": "zch6a/table-trace", "path": "plugin", "ref": "v0"}}]}
GOOD = '---\nname: table-trace\ndescription: "Reads things from papers and says where they are. Use when the user asks for things: any of them."\n---\n# x\n'


def test_skills_that_parse_and_skills_that_do_not() -> None:
    lines: list[str] = []
    assert check_skills.check(MARKET, fake_github({"table-trace": GOOD}), lines.append) == []
    assert lines == ["table-trace: table-trace ok"]
    assert check_skills.check(MARKET, fake_github({"table-trace": GOOD.replace("\n", "\r\n")}), lambda _: None) == []  # CRLF
    # a plain value with ": " inside: YAML reads a new key, so the whole frontmatter fails (the bug of six tools' 0.1.0)
    plain = GOOD.replace('description: "Reads', "description: Reads").replace('them."', "them.")
    (problem,) = check_skills.check(MARKET, fake_github({"table-trace": plain}), lambda _: None)
    assert "not YAML" in problem
    short = "---\nname: table-trace\ndescription: Reads things.\n---\n"
    assert "does not say when" in check_skills.check(MARKET, fake_github({"table-trace": short}), lambda _: None)[0]
    other = GOOD.replace("name: table-trace", "name: other")
    assert "name is 'other'" in check_skills.check(MARKET, fake_github({"table-trace": other}), lambda _: None)[0]
    assert "plugin.json names 'x'" in check_skills.check(MARKET, fake_github({"table-trace": GOOD}, "x"), lambda _: None)[0]
    bom = "\ufeff" + GOOD.rstrip("\n").removesuffix("# x").rstrip("\n")  # a BOM, and nothing after the frontmatter
    assert check_skills.check(MARKET, fake_github({"table-trace": bom}), lambda _: None) == []
    missing = check_skills.check(MARKET, fake_github({"table-trace": None}), lambda _: None)  # one unreadable file: said, not a crash
    assert missing and "could not read its SKILL.md" in missing[0]
