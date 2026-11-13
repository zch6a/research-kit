// The page in English or Chinese: the choice kept in the address (#zh) so that a link opens the same.
const button = document.getElementById("lang");
function show(lang) {
  for (const el of document.querySelectorAll("[data-lang]")) el.hidden = el.dataset.lang !== lang;
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  button.textContent = lang === "zh" ? "English" : "中文";
  button.setAttribute("aria-label", lang === "zh" ? "Switch to English" : "切换到中文");
}
let lang = location.hash === "#zh" || (!location.hash && navigator.language.startsWith("zh")) ? "zh" : "en";
show(lang);
button.addEventListener("click", () => {
  lang = lang === "zh" ? "en" : "zh";
  history.replaceState(null, "", lang === "zh" ? "#zh" : "#en");
  show(lang);
});
