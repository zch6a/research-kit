// Filters (by stage, and by words for the projects), copy buttons, and the pipeline steps that filter the tools.
// The page works without it: everything is shown and the commands can be selected by hand.
for (const root of document.querySelectorAll("[data-lang]")) {
  if (root.tagName !== "DIV") continue;
  const tools = root.querySelectorAll(".tool");
  const toolChips = root.querySelectorAll("[id$='-tools'] .chip");
  const steps = root.querySelectorAll(".step");
  function showTools(stage) {
    for (const t of tools) t.hidden = stage !== "all" && t.dataset.stage !== stage;
    for (const c of toolChips) c.classList.toggle("on", c.dataset.filter === stage);
    for (const s of steps) s.classList.toggle("on", s.dataset.stage === stage);
  }
  for (const c of toolChips) c.addEventListener("click", () => showTools(c.dataset.filter));
  for (const s of steps) {
    s.addEventListener("click", () => {
      showTools(s.classList.contains("on") ? "all" : s.dataset.stage);
      root.querySelector("[id$='-tools']").scrollIntoView();
    });
  }

  const land = root.querySelector("[id$='-landscape']");
  if (land) {
    const search = land.querySelector(".search");
    const chips = land.querySelectorAll(".chip");
    const empty = land.querySelector(".empty");
    let stage = "all";
    function apply() {
      const words = search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
      let shown = 0;
      for (const box of land.querySelectorAll(".stagebox")) {
        let inBox = 0;
        for (const row of box.querySelectorAll("tbody tr")) {
          const text = row.textContent.toLowerCase();
          const ok = (stage === "all" || box.dataset.stage === stage) && words.every((w) => text.includes(w));
          row.hidden = !ok;
          inBox += ok ? 1 : 0;
        }
        box.hidden = inBox === 0;
        shown += inBox;
      }
      empty.hidden = shown > 0;
    }
    search.addEventListener("input", apply);
    for (const c of chips) {
      c.addEventListener("click", () => {
        stage = c.dataset.filter;
        for (const x of chips) x.classList.toggle("on", x === c);
        apply();
      });
    }
  }
}

for (const b of document.querySelectorAll(".copy")) {
  b.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(b.dataset.copy);
    } catch {
      return; // no clipboard (an old browser, a file:// page): the command stays visible to select
    }
    const label = b.textContent;
    b.textContent = b.dataset.done;
    b.classList.add("done");
    setTimeout(() => { b.textContent = label; b.classList.remove("done"); }, 1600);
  });
}
