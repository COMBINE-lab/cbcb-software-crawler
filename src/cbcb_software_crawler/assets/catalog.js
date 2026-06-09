(function () {
  function initCatalog(root) {
    const search = root.querySelector("[data-search]");
    const showAll = root.querySelector("[data-show-all]");
    const count = root.querySelector("[data-visible-count]");
    const tbody = root.querySelector("tbody");
    const rows = Array.from(root.querySelectorAll("tbody tr"));
    let sortColumn = null;
    let sortDirection = 1;

    function applyFilters() {
      const query = (search && search.value ? search.value : "").toLowerCase();
      let visible = 0;
      rows.forEach(function (row) {
        const active = row.dataset.active === "true";
        const matchesActivity = active || (showAll && showAll.checked);
        const matchesQuery = !query || row.textContent.toLowerCase().includes(query);
        const shouldShow = matchesActivity && matchesQuery;
        row.hidden = !shouldShow;
        if (shouldShow) visible += 1;
      });
      if (count) count.textContent = String(visible);
    }

    function sortRows(column) {
      if (sortColumn === column) {
        sortDirection *= -1;
      } else {
        sortColumn = column;
        sortDirection = 1;
      }
      rows.sort(function (a, b) {
        const av = a.children[column].textContent.trim().toLowerCase();
        const bv = b.children[column].textContent.trim().toLowerCase();
        return av.localeCompare(bv, undefined, { numeric: true }) * sortDirection;
      });
      rows.forEach(function (row) {
        tbody.appendChild(row);
      });
      applyFilters();
    }

    if (search) search.addEventListener("input", applyFilters);
    if (showAll) showAll.addEventListener("change", applyFilters);
    root.querySelectorAll("[data-sort]").forEach(function (button) {
      button.addEventListener("click", function () {
        sortRows(Number(button.dataset.sort));
      });
    });
    applyFilters();
  }

  document.querySelectorAll(".software-catalog").forEach(initCatalog);
})();
