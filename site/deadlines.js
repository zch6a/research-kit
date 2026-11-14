// The days left before each deadline, from its time in UTC (data-utc); deadlines already past are marked.
for (const t of document.querySelectorAll("time[data-utc]")) {
  const days = (Date.parse(t.dataset.utc) - Date.now()) / 86400000;
  const zh = t.closest("[lang='zh-CN']") !== null;
  const out = t.parentElement.querySelector(".left");
  const row = t.closest("tr");
  if (days < 0) {
    row.classList.add("past");
    out.textContent = zh ? " 已截止" : " passed";
  } else {
    row.classList.remove("past");
    const n = Math.floor(days);
    out.textContent = zh ? ` 还剩 ${n} 天` : ` ${n} day${n === 1 ? "" : "s"} left`;
  }
}
