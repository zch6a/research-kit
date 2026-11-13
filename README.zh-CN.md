<div align="center">

# research-kit

**一套开源科研工具，从读论文到论文发表之后。** 每个都是一条命令（不用注册、不用 API key）和一个智能体技能，有的还有网站。靠规则和公开数据，不靠大模型：给出的每个结果都标明出处。

<a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-blue"></a>
<img alt="13 tools" src="https://img.shields.io/badge/tools-13-2ea44f">

[English](README.md) · **简体中文** · **[zch6a.github.io/research-kit](https://zch6a.github.io/research-kit/)**

</div>

---

## 一个插件市场装上全部技能

在 Claude Code 里：

```text
/plugin marketplace add zch6a/research-kit
/plugin install table-trace@research-kit
```

每个插件就是一个工具的技能，取自该工具仓库的最新发布版（`v0`）：智能体用 `uvx`（或 `npx`）运行工具，引用它找到的结果并注明出处。每个工具也可以单独使用，命令就写在它下面。

## 按科研流程排列的工具

<!-- tools:start -->
### 找文献、读论文

**[venue-atlas](https://github.com/zch6a/venue-atlas)** · [网站](https://zch6a.github.io/venue-atlas/) — 一个会议这些年都在研究什么：七个会议的 6 万篇论文按内容画成地图，主题有名字、有逐年趋势，可以在浏览器里按意思搜索。

```bash
uvx --from git+https://github.com/zch6a/venue-atlas@v0 venue-atlas build iclr icml --out site
```

**[paper-impact](https://github.com/zch6a/paper-impact)** · [网站](https://zch6a.github.io/paper-impact/) — AI 会议里哪些论文真正有影响：NeurIPS、ICML、ICLR、CVPR、ACL 的每篇论文，附 OpenAlex 的引用数和按领域归一化的影响力，并注明 OpenAlex 覆盖了多少。

```bash
uvx --from git+https://github.com/zch6a/paper-impact@v0 paper-impact build venues.json -o site/
```

**[table-trace](https://github.com/zch6a/table-trace)** — 论文表格里的每个数字都从 LaTeX 源码读出、标明在哪个单元格；还能把各篇论文对同一模型、同一基准报的数并排列出来。

```bash
uvx --from git+https://github.com/zch6a/table-trace@v0 table-trace compare 1512.03385 2201.03545 --row ResNet-50 --col top-1 --col acc
```

**[arxiv-diff](https://github.com/zch6a/arxiv-diff)** — 论文两个版本之间改了什么：表格里按行列对应的结果数字，以及正文、摘要、作者、图和参考文献。

```bash
uvx --from git+https://github.com/zch6a/arxiv-diff@v0 arxiv-diff 2106.09685
```

### 做实验

**[gpu-budget](https://github.com/zch6a/gpu-budget)** · [网站](https://zch6a.github.io/gpu-budget/) — 训练、微调或部署一个大模型要多少显存、时间和钱，每一项都给出公式（ZeRO/FSDP、各种并行、MoE、LoRA/QLoRA、KV 缓存），并和公开的训练记录对照过。

```bash
npx github:zch6a/gpu-budget train llama-3.1-70b --gpus 64 --zero 3 --tokens 2e12 --price 2.5
```

**[exp-tables](https://github.com/zch6a/exp-tables)** — 把实验结果变成论文里的表：多个种子的均值 ± 波动、与最好方法的显著性检验，只有种子数据撑得住时才加粗；可读 CSV、wandb、TensorBoard、MLflow。

```bash
uvx --from git+https://github.com/zch6a/exp-tables@v0 exp-tables results.csv --format markdown
```

**[repro-score](https://github.com/zch6a/repro-score)** — 别人能不能用你的代码复现论文：给科研代码仓库逐项打分并给出依据，只读文件、不运行任何代码。

```bash
uvx --from git+https://github.com/zch6a/repro-score@v0 repro-score github:owner/repo
```

### 写论文

**[fig-check](https://github.com/zch6a/fig-check)** — 按论文印出来的样子检查每张图：印刷后的字号、色觉异常读者分不清的颜色、位图分辨率；覆盖 LaTeX 工程里的所有图。

```bash
uvx --from git+https://github.com/zch6a/fig-check@v0 fig-check paper/
```

**[paper-proof](https://github.com/zch6a/paper-proof)** — 赶在审稿人之前检查论文：编造或写错的参考文献、标粗却不是最好的结果、对不上的提升幅度、摘要里过时的数字、失效的引用标签。

```bash
uvx --from git+https://github.com/zch6a/paper-proof@v0 paper-proof path/to/paper
```

### 投稿

**[submit-check](https://github.com/zch6a/submit-check)** — 别因为疏忽被直接拒稿：按会议规定检查 LaTeX 论文（双盲信息泄露、模板模式、页数、必需章节、PDF 字体、残留的 TODO）。

```bash
uvx --from git+https://github.com/zch6a/submit-check@v0 submit-check path/to/paper
```

**[iclr-scores](https://github.com/zch6a/iclr-scores)** · [网站](https://zch6a.github.io/iclr-scores/) — ICLR 2017–2025 年的审稿分数最后换来了什么：按平均分的录用比例、录用一半的位置、审稿人意见分歧的影响，以及你这组分数在往年的录用比例。

```bash
uvx --from git+https://github.com/zch6a/iclr-scores@v0 iclr-scores odds 6 6 8 5 --year 2025
```

### 发表之后

**[paper-page](https://github.com/zch6a/paper-page)** · [网站](https://zch6a.github.io/paper-page/) — 用 arXiv 编号生成论文项目主页：链接、预览图、摘要、BibTeX、Google Scholar 与链接预览标签，一个静态 HTML 文件，直接放到 GitHub Pages。

```bash
uvx --from git+https://github.com/zch6a/paper-page@v0 paper-page new 2003.08934 -o page/
```

**[scholar-cards](https://github.com/zch6a/scholar-cards)** — 把 OpenAlex 上你的引用数、h 指数和高被引论文做成 SVG 卡片，放进学术主页或 GitHub 个人页，由 GitHub Action 自动更新，不需要 API key。

```bash
uvx --from git+https://github.com/zch6a/scholar-cards@v0 scholar-cards search "Your Name"
```
<!-- tools:end -->

## 这些工具是怎么做的

- **都用真实材料检验过。** 每个工具发布前都在真实的论文、代码仓库或公开数据上试过，README 里的数字就来自这些实测；各仓库的 POLISH_LOG 记录了试了什么、修了什么。
- **不保存不属于你的东西。** 论文源码和数据集只在原处读取，或下载到临时目录、读完即删；网站只发布数量、标题和链接，不发布摘要，也不涉及审稿人。
- **统一的做法。** Python 3.10+（gpu-budget 用 Node），可以用 `uvx` 直接从 GitHub 运行，MIT 许可，测试不联网，CI 覆盖 Linux、macOS 和 Windows，工作流的 action 固定到具体提交，令牌只读。

## 参与贡献

`tools.json` 是工具清单：每个工具所属的阶段、中英文介绍、命令和网站。`python scripts/render.py` 据此生成插件市场、两份 README 里的工具部分和网站；CI 会检查它们是否最新。各工具的问题请到它自己的仓库提。

## 许可证

MIT，每个工具也都是 MIT。
