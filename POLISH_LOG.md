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

### 2026-11-14 — polishing round 2

**Read by someone else** (an independent review of the READMEs, the site and the scripts against the tools' own
READMEs), and every link checked (35, all answering). Fixed:
- **Commands that did not work as written**: venue-atlas's `build` needs `venue-atlas model` once first (its error says
  so), now the first line of its command; paper-impact's `build venues.json` needs a file a newcomer does not have,
  now fetched first from the tool's `v0` (`curl -LO …/v0/venues.json`), with one year, and its sentence says a free
  OpenAlex key makes a full build days, not months.
- **Claims a little too large**: “not a language model” → no large language model (venue-atlas places papers with a
  small embedding model); “never abstracts or reviewers” → never other papers' abstracts and never who a reviewer is
  (paper-page's page shows your own abstract; iclr-scores publishes scores); “no API key” notes paper-impact's.
- **“All the skills, from one marketplace” showed one install**: the section is now “Use them”: each tool on its own
  (it needs uv; gpu-budget Node 22+), what `@v0` is (the latest release, a tag that moves; a commit pins a version), and
  as skills — add the marketplace once, install the tools wanted by name; Claude Code is needed only for the skills.
- **Chinese wording** made precise: 按语义搜索, 在同一基准上报告的结果, 均值 ± 标准差 and 多个种子的结果支持时,
  失效的交叉引用（\label/\ref）, 社交分享预览标签（Open Graph）, 各平均分的录用率 and 录用率过半的分数线.
- **Scripts**: `check_skills.py` read a SKILL.md outside its error handling (one missing file stopped the run), called
  GitHub's API without a token (60 requests an hour, shared on CI's machines: CI now passes its read-only token),
  did not accept CRLF files, matched a tool's problems by name prefix (a future “paper” would take “paper-page”'s), and
  its docstring promised a check it did not make; `render.py` raised a bare KeyError for an incomplete entry, rendered
  empty stages, did not check that a command runs the `v0` the marketplace installs (now it does), and read the list
  twice. The Pages workflow now runs the render check before publishing; the CI file says that GitHub pauses a weekly
  workflow after 60 quiet days.
- **The site**: cards overflowed on 320 px phones (`minmax(min(300px, 100%), 1fr)`); dark mode now tells the browser
  (`color-scheme`); the language button had an English label while showing 中文, now it carries the language it shows;
  Back and Forward and an edited `#zh-CN` switch the language too. Checked in the browser.

Not possible here: trying the marketplace end to end means adding it to a Claude Code setup, which is the owner's.

Next: polishing round 3.

### 2026-11-14 — polishing round 3

**The site's first screen**: a row of the five stages under the lead, each with how many tools it has, linking to its
section (`Find and read 4 · Run experiments 3 · …`), in each language. Its first screenshot showed both languages' rows
at once: a class giving `display: flex` beats the `hidden` attribute, so a page-wide `[hidden] { display: none
!important; }` now keeps the other language hidden whatever a class says. The README shows that first screen
(`docs/site.png`, both languages).

**A way back from every tool**: each of the thirteen tools' READMEs, English and Chinese, now has a short section
before its licence pointing to research-kit and its site (two of them had no toolkit section at all). Committed and
pushed in each repository with a line in its POLISH_LOG; CI passed in all thirteen.

Next: polishing round 4.

### 2026-11-14 — polishing round 4

**Tests for the two scripts** (`tests/test_scripts.py`, offline): `render.load` takes a path, so made-up lists check
that a command not at `@v0`, an unknown stage, a missing language, a non-https site and a tool listed twice are each
refused; the marketplace entry is a `git-subdir` source at `v0`; a stage without tools is left out of the README and
the site; the page escapes the text; `fill` refuses a README without its markers; and the committed files are what
`tools.json` gives. `check_skills.check` takes the fetcher, so a made-up GitHub checks a good skill, CRLF line ends,
an unquoted description containing ": " (the YAML bug of six tools' 0.1.0), a description that does not say when, a
skill or plugin name that differs, and one unreadable SKILL.md (reported, not a crash). A message naming the tool
used `t['name']` where the loop had `name`; fixed.

**CI**: ruff (pinned 0.15.0; `ruff.toml`, long prose lines in the page template allowed) and the tests run before the
render and skill checks. The workflows were read again: read-only token, actions pinned, Pages publishes only after
`render.py --check` passes and its deploy job runs no project code.

Next: polishing round 5.

### 2026-11-14 — polishing round 5

A fresh review of every file, the Chinese text against the AI-tone list, and the site at phone width in dark mode
(no sideways scroll; both languages).

**gpu-budget's command ran its default branch.** `npx github:zch6a/gpu-budget` has no ref, so the README and site ran
whatever was on main while the plugin installs v0. It is now `npx github:zch6a/gpu-budget#v0` (tried: it runs), and
the check asks every command to run the tool at v0 as the program, not in a comment: `@v0 ` for uvx, `#v0 ` for npx.

**The site said less than the README**: its lead still had "no large language model" without the venue-atlas
exception (a small embedding model) that the README gained in round 2. Both languages now say it.

**Counts and names outside the markers**: the badge is now rewritten with the number of tools; the prose says "the
ones below" instead of a number; the install example (table-trace) must be in the list.

**Stricter list**: names and stage keys must be lowercase slugs (they go into ids and links as they are), tags a
list of words, every stage complete and listed once, no line breaks in descriptions and no ``` in a command.

**Skill check**: a `skills` entry that is not a folder (or an error object from the API) is reported instead of
crashing the run; a SKILL.md with a byte-order mark or nothing after its frontmatter is read.

**Site**: the Chinese parts carry `lang="zh-CN"` in the page itself; the language button is hidden until the
script runs (without it, it did nothing); the stage pills read "4 tools" to a screen reader. The marketplace's owner
has only its documented field; `claude plugin validate` passes. The README's contributing note lists tags.

Tests cover each new check. Next: v0.1.0.

### 2026-11-14 — every stage of the work: ours and the best of the rest

The goal changed from "our tools" to "the whole chain of research work": what a researcher can use at each stage,
whoever made it, and where nothing good exists yet.

**The survey**: four parallel searches of GitHub, one per part of the work (finding and reading; AI assistants,
writing and figures; experiments, compute, data and release; submission, review and after publication), from
repository search, topics and each field's awesome lists, every candidate then checked on its own. 189 picks, 171
after removing the ones two searches found; kept by the brief's rules (open-source, maintained or still the
standard, in real use; no abandoned or archived projects, thin wrappers, paid services with an open shell, or link
lists but the few a stage relies on). `scripts/refresh_landscape.py` then asked the GitHub API about all 171 again:
none had moved, been archived or disappeared; the stars, last push and licence on the page are its numbers, with
the date. It runs weekly in CI with `--check`, which fails on a project that has moved, been archived or gone.

**The page**: five stages, nineteen sections (following papers, searching, references, reading, AI assistants,
experiments, compute, evaluation, writing, checking the text, figures, checking before submission, deadlines,
review and rebuttal, releasing code and data, project pages and homepages, posters and talks, sharing and citations,
lab and reading groups). Each section shows our tools first (with their command), then a table of the others, most
starred first, with licence and update month. A missing licence is shown as "none" in red, with a note to ask before
reusing (the two most copied project-page templates have none). Our tools moved into sections; repro-score is now
under releasing code (stage "after"). The marketplace still has only our tools.

**What nothing covers yet**: 23 needs from the survey, each with its closest projects and what they miss, and
which of ours covers part of it (nine do: arxiv-diff, paper-impact, paper-proof, table-trace twice, fig-check,
submit-check twice, scholar-cards). Six more gaps the survey found are already filled by our tools, so they are not
listed.

**Checks**: `render.py` validates landscape.json (owner/name, no duplicates, none of ours, known sections, counts and
dates, nothing archived, every gap's closest projects in the list, every "ours" one of our tools, each of our tools'
section in its stage); tests for both. Chinese descriptions checked for marketing words (two "一键" phrasings made
plain). The site at 1280 px: no sideways scroll, 171 rows, 13 cards, 23 gaps; wide tables scroll inside their box.

### 2026-11-14 — paper-proof 0.2.0 fills a gap

The first two needs chosen from the list were built into paper-proof 0.2.0: consistency across a whole paper
(acronyms, one term written two ways, British and American spelling, symbols with two meanings) and `--review`, a
local check of a submitted PDF that sends nothing. The consistency need is off the list (22 left); the reviewer need
stays, marked as partly covered by paper-proof (a PDF's tables still cannot be compared with its claims).
paper-proof's description and tags updated; its skill at v0 checked.

### 2026-11-14 — Deadlines and venue rules

One of the needs on the list: "a deadline tracker that also keeps each venue's rules". Rather than keep dates by hand,
`scripts/refresh_deadlines.py` reads ccf-deadlines (MIT, 9.5k stars, updated daily) for 16 machine-learning venues at
its current commit, and submit-check's rules at its v0 tag, into `deadlines.json` (dates, places, links; the commit
recorded). `render.py` puts each venue's next deadline (or its last one, when the next edition has none yet) in both
READMEs and on the site, with time zone, conference dates, page limits and required sections, each rule linked to its
official page and to `submit-check --venue`. `site/deadlines.js` counts the days left from each deadline's UTC time
(AoE is UTC-12). Checked: `load_deadlines` refuses dates that do not parse and time zones it does not know; two tests
with made-up venues; the days-left script run on the page (CVPR 2027: 3 days left on 2026-11-14 in UTC-12).
The gap stays on the list, partly covered: supplementary deadlines, rebuttal windows and LLM policies are not
collected.
