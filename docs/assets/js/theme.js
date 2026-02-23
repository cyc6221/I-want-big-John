// assets/js/theme.js
(function () {
  const STORAGE_KEY = "theme"; // 'light' | 'dark'
  const root = document.documentElement;

  function getTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === "dark" ? "dark" : "light"; // 預設一律 light
  }

  function applyTheme(theme, persist = true) {
    if (theme === "dark") {
      root.setAttribute("data-theme", "dark");
      if (persist) localStorage.setItem(STORAGE_KEY, "dark");
    } else {
      root.setAttribute("data-theme", "light");
      if (persist) localStorage.setItem(STORAGE_KEY, "light");
    }
    updateButton();
  }

  function updateButton() {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;

    const theme = getTheme();
    const next = theme === "dark" ? "light" : "dark";
    btn.dataset.next = next;

    // 目前 light 顯示 🌙（點了切深色）；目前 dark 顯示 ☀️（點了切淺色）
    btn.innerHTML = theme === "dark" ? "☀️" : "🌙";
    btn.title = theme === "dark" ? "切換為淺色模式" : "切換為深色模式";
    btn.setAttribute("aria-label", btn.title);
  }

  function mountButton() {
    const btn = document.createElement("button");
    btn.id = "theme-toggle";
    btn.type = "button";
    btn.className = "theme-toggle";
    document.body.appendChild(btn);

    btn.addEventListener("click", () => {
      applyTheme(btn.dataset.next || "dark", true);
    });

    updateButton();
  }

  // 初始化：永遠先套用「淺色」，除非使用者之前選過 dark
  applyTheme(getTheme(), false);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountButton);
  } else {
    mountButton();
  }
})();