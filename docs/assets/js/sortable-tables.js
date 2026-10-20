/* Click a column header to sort a table: ascending -> descending -> original order.
   Uses event delegation and reads the rows at click time, so tables that are
   filled in by other scripts (per-month / chosen-number tables) sort too.
   Opt out with <table data-sortable="false">; override a cell's sort value with
   data-sort="...". Rows whose cell count differs from the header (loading /
   empty-state placeholders) are never moved. */
(function () {
  var collator = new Intl.Collator("zh-TW", { numeric: true });

  function sortableTable(th) {
    var table = th.closest(".page-content table");
    if (!table || table.getAttribute("data-sortable") === "false") return null;
    if (!th.closest("thead") || th.colSpan > 1) return null;
    return table;
  }

  function cellValue(row, col) {
    var cell = row.cells[col];
    var raw = cell.hasAttribute("data-sort") ? cell.getAttribute("data-sort") : cell.textContent;
    raw = raw.trim();
    if (raw === "" || raw === "-" || raw === "—") return { empty: true };
    var num = Number(raw.replace(/[,%\s元注]/g, ""));
    return isNaN(num) ? { text: raw } : { num: num };
  }

  function compare(a, b) {
    if (a.empty || b.empty) return 0; // empties are handled by the caller
    if (a.num !== undefined && b.num !== undefined) return a.num - b.num;
    if (a.num !== undefined) return -1; // numbers before text
    if (b.num !== undefined) return 1;
    return collator.compare(a.text, b.text);
  }

  function sortBy(table, th) {
    var body = table.tBodies[0];
    if (!body) return;
    var col = th.cellIndex;
    var width = th.parentNode.cells.length;
    var rows = Array.prototype.filter.call(body.rows, function (r) {
      return r.cells.length === width;
    });
    if (rows.length < 2) return;

    var current = th.getAttribute("aria-sort");
    var next = current === "ascending" ? "descending" : current === "descending" ? "none" : "ascending";

    Array.prototype.forEach.call(th.parentNode.cells, function (h) {
      h.removeAttribute("aria-sort");
    });
    if (next !== "none") th.setAttribute("aria-sort", next);

    rows.forEach(function (r, i) {
      if (r.dataset.sortOrigin === undefined) r.dataset.sortOrigin = i;
    });
    var dir = next === "descending" ? -1 : 1;
    var keyed = rows.map(function (r) {
      return { row: r, value: next === "none" ? null : cellValue(r, col), origin: +r.dataset.sortOrigin };
    });
    keyed.sort(function (a, b) {
      if (next === "none") return a.origin - b.origin;
      if (a.value.empty !== b.value.empty) return a.value.empty ? 1 : -1; // empties last either way
      return compare(a.value, b.value) * dir || a.origin - b.origin;
    });
    keyed.forEach(function (k) {
      body.appendChild(k.row);
    });
  }

  function arm(th) {
    if (th.hasAttribute("tabindex")) return;
    th.setAttribute("tabindex", "0");
    th.classList.add("is-sortable");
  }

  document.addEventListener("click", function (e) {
    var th = e.target.closest && e.target.closest("th");
    var table = th && sortableTable(th);
    if (table) sortBy(table, th);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var th = e.target.closest && e.target.closest("th.is-sortable");
    var table = th && sortableTable(th);
    if (table) {
      e.preventDefault();
      sortBy(table, th);
    }
  });

  document.querySelectorAll(".page-content thead th").forEach(function (th) {
    if (sortableTable(th)) arm(th);
  });
})();
