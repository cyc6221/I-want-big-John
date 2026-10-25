/* Tag filter + sort for the all-articles page.
   Each chip belongs to a group (data-filter-group) and matches an article's
   data-<group> attribute. Chips in one group are exclusive (click again to
   clear); groups combine with AND. Chips that match no article are disabled.
   Archived (已下架) instants are hidden until the "顯示已下架" box is ticked.
   Without JS the full list simply stays visible. */
(function () {
  var root = document.querySelector("[data-article-filter]");
  var list = document.querySelector("[data-article-list]");
  if (!root || !list) return;

  var items = Array.prototype.slice.call(list.querySelectorAll(".post-item"));
  var chips = Array.prototype.slice.call(root.querySelectorAll(".tag-chip"));
  var sortSelect = root.querySelector("[data-filter-sort]");
  var countEl = root.querySelector("[data-filter-count]");
  var emptyEl = list.querySelector("[data-filter-empty]");
  var archivedBox = root.querySelector("[data-filter-archived]");
  var archivedCountEl = root.querySelector("[data-filter-archived-count]");
  var collator = new Intl.Collator("zh-TW", { numeric: true });
  var active = {}; // group -> selected value

  function groupOf(chip) {
    return chip.parentNode.getAttribute("data-filter-group");
  }

  function isArchived(item) {
    return item.getAttribute("data-status") === "archived";
  }

  function matchesGroups(item, skipGroup) {
    return Object.keys(active).every(function (group) {
      return group === skipGroup || item.getAttribute("data-" + group) === active[group];
    });
  }

  function matches(item, skipGroup) {
    return matchesGroups(item, skipGroup) && (archivedBox.checked || !isArchived(item));
  }

  // Count per chip = articles that would match if that chip were chosen.
  function updateChips() {
    chips.forEach(function (chip) {
      var group = groupOf(chip);
      var value = chip.getAttribute("data-filter-value");
      var n = items.filter(function (item) {
        return matches(item, group) && item.getAttribute("data-" + group) === value;
      }).length;
      var badge = chip.querySelector(".tag-chip__count");
      if (!badge) {
        badge = document.createElement("span");
        badge.className = "tag-chip__count";
        chip.appendChild(badge);
      }
      badge.textContent = n;
      var selected = active[group] === value;
      chip.setAttribute("aria-pressed", selected ? "true" : "false");
      chip.disabled = n === 0 && !selected;
    });
    // Archived articles that the other filters would let through.
    var archivedN = items.filter(function (item) {
      return isArchived(item) && matchesGroups(item);
    }).length;
    archivedCountEl.textContent = "(" + archivedN + ")";
    archivedBox.disabled = archivedN === 0 && !archivedBox.checked;
  }

  function compareItems(a, b) {
    var mode = sortSelect.value;
    var byTitle = collator.compare(a.getAttribute("data-title"), b.getAttribute("data-title"));
    if (mode === "title") return byTitle;
    var da = a.getAttribute("data-date");
    var db = b.getAttribute("data-date");
    var byDate = da < db ? -1 : da > db ? 1 : 0;
    // Same-day articles follow the date direction, so newer issue numbers lead in "new to old".
    return (byDate || byTitle) * (mode === "date-asc" ? 1 : -1);
  }

  function render() {
    updateChips();
    var shown = items.filter(function (item) { return matches(item); });
    items.sort(compareItems);
    items.forEach(function (item) {
      item.hidden = shown.indexOf(item) === -1;
      item.classList.remove("is-first");
      list.insertBefore(item, emptyEl);
    });
    var firstShown = items.filter(function (item) { return !item.hidden; })[0];
    if (firstShown) firstShown.classList.add("is-first");
    emptyEl.hidden = shown.length > 0;
    countEl.textContent = "共 " + shown.length + " 篇";
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var group = groupOf(chip);
      var value = chip.getAttribute("data-filter-value");
      if (active[group] === value) delete active[group];
      else active[group] = value;
      render();
    });
  });
  sortSelect.addEventListener("change", render);
  archivedBox.addEventListener("change", render);

  render();
})();
