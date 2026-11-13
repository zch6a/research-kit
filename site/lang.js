// The page in English or Chinese: the choice kept in the address (#en, #zh) so that a link, Back and Forward show the same.
const button = document.getElementById("lang");
function show(lang) {
  for (const el of document.querySelectorAll("[data-lang]")) el.hidden = el.dataset.lang !== lang;
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  // the button shows the other language, in that language (its own lang, so a screen reader reads it right)
  button.textContent = lang === "zh" ? "English" : "中文";
  button.lang = lang === "zh" ? "en" : "zh-CN";
}
function fromAddress() {
  if (/^#zh/i.test(location.hash)) return "zh";
  if (/^#en/i.test(location.hash)) return "en";
  return navigator.language.startsWith("zh") ? "zh" : "en";
}
let lang = fromAddress();
show(lang);
button.addEventListener("click", () => {
  lang = lang === "zh" ? "en" : "zh";
  history.pushState(null, "", lang === "zh" ? "#zh" : "#en");
  show(lang);
});
window.addEventListener("popstate", () => { lang = fromAddress(); show(lang); });
window.addEventListener("hashchange", () => { lang = fromAddress(); show(lang); });
