// assets/js/theme.js
(function () {
  const STORAGE_KEY = "theme"; // 'light' | 'dark'
  const root = document.documentElement;

  function currentEffectiveTheme() {
    // 若使用者已選擇就用它，否則用系統
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function applyTheme(theme, persist = true) {
    if (theme === "light") {
      root.setAttribute("data-theme", "light");
      if (persist) localStorage.setItem(STORAGE_KEY, "light");
    } else if (theme === "dark") {
      root.setAttribute("data-theme", "dark");
      if (persist) localStorage.setItem(STORAGE_KEY, "dark");
    } else {
      // auto：移除 data-theme，回到跟隨系統
      root.removeAttribute("data-theme");
      if (persist) localStorage.removeItem(STORAGE_KEY);
    }
    updateButton();
  }

  function updateButton() {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;

    const saved = localStorage.getItem(STORAGE_KEY);
    const effective = currentEffectiveTheme();

    // 顯示：目前是 dark 就顯示 ☀️（點了會切回 light）；反之顯示 🌙
    const next = effective === "dark" ? "light" : "dark";
    btn.dataset.next = next;
    btn.setAttribute("aria-label", next === "dark" ? "切換為深色模式" : "切換為淺色模式");
    btn.title = saved
      ? `目前：${effective}（已固定）`
      : `目前：${effective}（跟隨系統）`;

    btn.innerHTML = effective === "dark" ? "☀️" : "🌙";
  }

  function mountButton() {
    const btn = document.createElement("button");
    btn.id = "theme-toggle";
    btn.type = "button";
    btn.className = "theme-toggle";
    document.body.appendChild(btn);

    btn.addEventListener("click", () => {
      const next = btn.dataset.next || "dark";
      applyTheme(next, true);
    });

    // 讓「跟隨系統」時，系統切換會即時更新 icon
    const mq = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)");
    if (mq && mq.addEventListener) {
      mq.addEventListener("change", () => {
        if (!localStorage.getItem(STORAGE_KEY)) updateButton();
      });
    }

    updateButton();
  }

  // 初始化：先套用使用者選擇（若有），否則不設 data-theme（跟系統）
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "light" || saved === "dark") {
    root.setAttribute("data-theme", saved);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountButton);
  } else {
    mountButton();
  }
})();