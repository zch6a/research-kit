<div align="center">

# research-kit

**Open tools for research work, from reading papers to after publication.** Each is a command (no account; no API
key, though paper-impact goes faster with a free one), an agent skill, and some a site. Rules and published data, no
large language model (venue-atlas places papers with a small embedding model): what they report says where it comes
from.

<a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-blue"></a>
<img alt="13 tools" src="https://img.shields.io/badge/tools-13-2ea44f">

**English** · [简体中文](README.zh-CN.md) · **[zch6a.github.io/research-kit](https://zch6a.github.io/research-kit/)**

</div>

---

## Use them

**On their own**, each tool is the command under it below. They need [uv](https://docs.astral.sh/uv/) (it fetches
Python 3.10+ if needed); gpu-budget needs Node 22+. `@v0` in a command is the tool's latest release: a tag that moves
with each release (put a commit there instead for a fixed version).

**As agent skills**, in Claude Code: add the marketplace once, then install the tools you want by name (any of the
thirteen below):

```text
/plugin marketplace add zch6a/research-kit
/plugin install table-trace@research-kit
/plugin install paper-proof@research-kit
```

Each plugin is one tool's skill, from that tool's repository at `v0`: the agent runs the tool and quotes what it
found, with where it found it. Claude Code is only needed for the skills, not for the tools.

## The tools, in the order of the work

<!-- tools:start -->
### Find and read

**[venue-atlas](https://github.com/zch6a/venue-atlas)** · [site](https://zch6a.github.io/venue-atlas/) — What a conference was about, year by year: 60,000 papers of seven venues on maps by meaning, named topics with their trends, search by meaning in the browser.

```bash
uvx --from git+https://github.com/zch6a/venue-atlas@v0 venue-atlas model    # the model, 30 MB, once
uvx --from git+https://github.com/zch6a/venue-atlas@v0 venue-atlas build iclr icml --out site
```

**[paper-impact](https://github.com/zch6a/paper-impact)** · [site](https://zch6a.github.io/paper-impact/) — Which papers at AI venues mattered: every NeurIPS, ICML, ICLR, CVPR and ACL paper with its citations and field-normalized impact from OpenAlex, and how much OpenAlex covers. A free OpenAlex key makes a full build days, not months.

```bash
curl -LO https://raw.githubusercontent.com/zch6a/paper-impact/v0/venues.json
uvx --from git+https://github.com/zch6a/paper-impact@v0 paper-impact build venues.json -o site/ --years 2024
```

**[table-trace](https://github.com/zch6a/table-trace)** — Every number in a paper's tables, read from its LaTeX source and traced to its cell; and what papers report for the same model on the same benchmark, side by side.

```bash
uvx --from git+https://github.com/zch6a/table-trace@v0 table-trace compare 1512.03385 2201.03545 --row ResNet-50 --col top-1 --col acc
```

**[arxiv-diff](https://github.com/zch6a/arxiv-diff)** — What changed between two versions of a paper: the result numbers in its tables by row and column, and the text, abstract, authors, figures and references.

```bash
uvx --from git+https://github.com/zch6a/arxiv-diff@v0 arxiv-diff 2106.09685
```

### Run experiments

**[gpu-budget](https://github.com/zch6a/gpu-budget)** · [site](https://zch6a.github.io/gpu-budget/) — How much GPU memory, time and money training, fine-tuning or serving an LLM takes, each part with its formula (ZeRO/FSDP, parallelism, MoE, LoRA/QLoRA, KV cache), checked against published runs.

```bash
npx github:zch6a/gpu-budget train llama-3.1-70b --gpus 64 --zero 3 --tokens 2e12 --price 2.5
```

**[exp-tables](https://github.com/zch6a/exp-tables)** — Experiment results to your paper's table: mean ± spread over seeds, significance against the best, bold only where the seeds support it; from CSV, wandb, TensorBoard or MLflow.

```bash
uvx --from git+https://github.com/zch6a/exp-tables@v0 exp-tables results.csv --format markdown
```

**[repro-score](https://github.com/zch6a/repro-score)** — Can someone reproduce your paper from your code? A score out of 100 for a research code repository, item by item with the file and line behind it, read from the files with nothing run.

```bash
uvx --from git+https://github.com/zch6a/repro-score@v0 repro-score github:owner/repo
```

### Write the paper

**[fig-check](https://github.com/zch6a/fig-check)** — A paper's figures as they will print: text size at the printed scale, colours that collapse for colour-blind readers, raster resolution; for every figure of a LaTeX project.

```bash
uvx --from git+https://github.com/zch6a/fig-check@v0 fig-check paper/
```

**[paper-proof](https://github.com/zch6a/paper-proof)** — Check your paper before reviewers do: invented or wrong references, bold results that are not the best, claimed gains that do not add up, stale abstract numbers, broken labels.

```bash
uvx --from git+https://github.com/zch6a/paper-proof@v0 paper-proof path/to/paper
```

### Submit

**[submit-check](https://github.com/zch6a/submit-check)** — Don't get desk-rejected for a slip: a LaTeX paper checked against the venue's rules (double-blind leaks, template mode, page limit, required sections, PDF fonts, leftover TODOs).

```bash
uvx --from git+https://github.com/zch6a/submit-check@v0 submit-check path/to/paper
```

**[iclr-scores](https://github.com/zch6a/iclr-scores)** · [site](https://zch6a.github.io/iclr-scores/) — What ICLR's review scores led to, 2017-2025: the acceptance rate by mean score, where half the papers got in, what disagreement did, and the odds for your scores.

```bash
uvx --from git+https://github.com/zch6a/iclr-scores@v0 iclr-scores odds 6 6 8 5 --year 2025
```

### After it is out

**[paper-page](https://github.com/zch6a/paper-page)** · [site](https://zch6a.github.io/paper-page/) — A project page for your paper from its arXiv id: links, teaser, abstract, BibTeX, Google Scholar and link-preview tags, in one static HTML file for GitHub Pages.

```bash
uvx --from git+https://github.com/zch6a/paper-page@v0 paper-page new 2003.08934 -o page/
```

**[scholar-cards](https://github.com/zch6a/scholar-cards)** — Your citations, h-index and most cited papers from OpenAlex as SVG cards for an academic homepage or a GitHub profile, kept fresh by a GitHub Action; no API key.

```bash
uvx --from git+https://github.com/zch6a/scholar-cards@v0 scholar-cards search "Your Name"
```
<!-- tools:end -->

## How they are made

- **Checked against something real.** Each tool was tried on real papers, repositories or published data before its
  release, and the numbers in its README come from those runs; its POLISH_LOG says what was tried and what broke.
- **Nothing kept that is not yours.** Papers' sources and datasets are read where they are, or downloaded to a
  temporary folder and deleted; the sites publish counts, titles, links and scores, never other papers' abstracts
  and never who a reviewer is (paper-page's page shows your own paper's abstract).
- **The same shape.** Python 3.10+ (gpu-budget: Node), installable with `uvx` from GitHub, MIT licensed, a test suite
  that needs no network, CI on Linux, macOS and Windows, actions pinned to commits, read-only tokens but for the job
  that makes a release (which runs nothing of the project).

## Contributing

`tools.json` is the list: each tool's stage, description in both languages, command and site. `python
scripts/render.py` writes the marketplace, the tool sections of both READMEs and the site from it; CI checks they are
up to date. Each tool's own repository takes its issues.

## License

MIT, as is every tool.
