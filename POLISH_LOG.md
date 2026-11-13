# Polish log

### 2026-11-14 — development

**What it is**: the front door of the toolkit: thirteen tools in the order of the work (find and read, run experiments,
write, submit, after it is out), each with a sentence in both languages, one command and its site; one Claude Code
plugin marketplace for all their skills; a small bilingual site. `tools.json` is the list, and `scripts/render.py`
writes the marketplace, the tool sections of both READMEs and the site from it (`--check` in CI).

**The marketplace**, in the format the Claude Code docs give (checked with the documentation agent: marketplace
reference, plugin sources, install, CLI): each plugin is a `git-subdir` source, the `plugin/` folder of the tool's own
repository at its `v0` tag, so nothing is copied and each skill follows its tool's latest release.
`claude plugin validate .` passes. No `marketplace add` was run here.

**What putting them together found**: `claude plugin validate` on each tool's plugin failed for six of the thirteen
(submit-check, scholar-cards, paper-impact, paper-page, fig-check, repro-score): their SKILL.md frontmatter had a plain
YAML value with `: ` inside, which starts a new key, so the whole frontmatter failed to parse and Claude Code would load
the skill with no description — an agent would never pick it. The values are quoted in each, and each was released as
0.1.1 (tests, CI, the release workflow, `v0` moved) so that the marketplace installs the fix. `scripts/check_skills.py`
now fetches every skill at `v0` and parses it as YAML (name, a description that says when to use it); CI runs it on
every push and weekly.

**Checked**: every command installs from `v0` and runs (`--version` from a fresh uv cache for the twelve Python tools;
gpu-budget's `npx` at its release); the site in the browser (the language follows the browser and the toggle, kept in
the address; no console errors; no horizontal scroll at 390 px; long commands wrap instead of being cut after
“github.com/zch6a”). On the way, the repositories' own descriptions were brought up to date (venue-atlas named four
venues of seven; paper-impact two of five) and the two with live sites got them as their homepage.

Next: the site published; a social card; a read-through of every tool's README for the same claims as here.

### 2026-11-14 — polishing round 1

**Each tool's sentence against its own README**: all thirteen say what their READMEs say; repro-score's now says the
score is out of 100 and that each item has the file and line behind it. The claims under “How they are made” checked in
all thirteen repositories' workflows: CI on Linux, macOS and Windows in every one, every action pinned to a commit
(repro-score's one `@v0` is its own released Action, tested on purpose), and `contents: write` only in the job that makes
a release — so the README now says “read-only tokens but for the job that makes a release”, in both languages.

**The social card** (`docs/social-preview.png`, from `scripts/social-card.html`): the thirteen tools by stage.

**A launch kit**, kept outside the repository with the others (`launch/research-kit.md`): an angle, a checklist before
posting (the fourteen social previews, trying the marketplace once in Claude Code), and drafts for Hacker News
(table-trace), r/MachineLearning (iclr-scores), a thread, a Chinese post and awesome-list lines; every number in them
comes from a tool's own run. Posting is the owner's.

Next: polishing round 2 (the site and READMEs read by someone else; the marketplace tried end to end if the owner adds it).
