(() => {
  "use strict";

  const PAGE = 40;
  const state = {
    yearsMeta: [],
    loadedYears: new Map(),
    loadingYears: new Set(),
    filter: "all",
    query: "",
    items: [],
    shown: 0,
    totalKnown: 0,
  };

  const el = {
    list: document.getElementById("list"),
    status: document.getElementById("status"),
    meta: document.getElementById("metaBar"),
    more: document.getElementById("more"),
    q: document.getElementById("q"),
    clear: document.getElementById("clear"),
    install: document.getElementById("installHint"),
  };

  function showInstallHint() {
    const ua = navigator.userAgent || "";
    const isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true;
    if (isIOS && !standalone) {
      el.install.hidden = false;
      el.install.classList.add("visible");
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function allLoadedItems() {
    const out = [];
    for (const y of state.yearsMeta) {
      const rows = state.loadedYears.get(y.year);
      if (rows) out.push(...rows);
    }
    return out;
  }

  function matches(item) {
    if (state.filter !== "all" && item.c !== state.filter) return false;
    const q = state.query.trim().toLowerCase();
    if (!q) return true;
    return (
      item.t.toLowerCase().includes(q) ||
      String(item.y).includes(q) ||
      (item.r && item.r.toLowerCase().includes(q)) ||
      (item.d && item.d.includes(q))
    );
  }

  function recompute() {
    state.items = allLoadedItems().filter(matches);
    // Prefer newer years first when browsing without search
    if (!state.query.trim()) {
      state.items.sort((a, b) => b.y - a.y || a.t.localeCompare(b.t, "fr"));
    } else {
      state.items.sort((a, b) => b.y - a.y || a.t.localeCompare(b.t, "fr"));
    }
    state.shown = 0;
    el.list.innerHTML = "";
    renderMore();
    updateMeta();
  }

  function updateMeta() {
    const loadedCount = [...state.loadedYears.values()].reduce((n, a) => n + a.length, 0);
    const yearsLoaded = state.loadedYears.size;
    const yearsTotal = state.yearsMeta.length;
    el.meta.innerHTML = `<span><strong>${state.items.length.toLocaleString("fr-CH")}</strong> affichés</span>
      <span><strong>${loadedCount.toLocaleString("fr-CH")}</strong> / ${state.totalKnown.toLocaleString("fr-CH")} chargés</span>
      <span>Années ${yearsLoaded}/${yearsTotal}</span>`;
  }

  function rowHtml(item) {
    const badge = item.c === "rs" ? "RS" : "RO/AS";
    const badgeClass = item.c === "rs" ? "rs" : "oc";
    const rs = item.r ? `<span class="rs-num">RS ${escapeHtml(item.r)}</span>` : "";
    const date = item.d ? `<div class="date">${escapeHtml(item.d)}</div>` : "";
    return `<li>
      <a class="row" href="${escapeHtml(item.u)}" target="_blank" rel="noopener noreferrer">
        <div class="row-top">
          <span class="badge ${badgeClass}">${badge}</span>
          <span class="year">${item.y}</span>
          ${rs}
        </div>
        <div class="title">${escapeHtml(item.t)}</div>
        ${date}
      </a>
    </li>`;
  }

  function renderMore() {
    const next = state.items.slice(state.shown, state.shown + PAGE);
    if (state.shown === 0 && next.length === 0) {
      el.status.hidden = false;
      el.status.className = "status";
      el.status.textContent =
        state.loadedYears.size === 0
          ? "Chargement…"
          : "Aucun résultat pour cette recherche.";
      el.more.hidden = true;
      return;
    }
    el.status.hidden = true;
    el.list.insertAdjacentHTML("beforeend", next.map(rowHtml).join(""));
    state.shown += next.length;
    const remaining = state.items.length - state.shown;
    const moreYears = state.yearsMeta.some((y) => !state.loadedYears.has(y.year));
    if (remaining > 0) {
      el.more.hidden = false;
      el.more.disabled = false;
      el.more.textContent = `Charger plus (${remaining.toLocaleString("fr-CH")} restants)`;
    } else if (moreYears && !state.query.trim()) {
      el.more.hidden = false;
      el.more.disabled = false;
      el.more.textContent = "Charger l’année précédente";
    } else if (moreYears && state.query.trim()) {
      el.more.hidden = false;
      el.more.disabled = false;
      el.more.textContent = "Chercher dans d’autres années";
    } else {
      el.more.hidden = true;
    }
  }

  async function loadYear(yearMeta) {
    if (state.loadedYears.has(yearMeta.year) || state.loadingYears.has(yearMeta.year)) {
      return state.loadedYears.get(yearMeta.year) || [];
    }
    state.loadingYears.add(yearMeta.year);
    try {
      const res = await fetch(yearMeta.file);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const rows = await res.json();
      state.loadedYears.set(yearMeta.year, rows);
      return rows;
    } finally {
      state.loadingYears.delete(yearMeta.year);
    }
  }

  async function ensureInitialYears() {
    // Load newest 3 years first for fast first paint on iPhone
    const first = state.yearsMeta.slice(0, 3);
    await Promise.all(first.map(loadYear));
  }

  async function loadNextYearBatch(count = 2) {
    const pending = state.yearsMeta.filter((y) => !state.loadedYears.has(y.year)).slice(0, count);
    if (!pending.length) return false;
    el.more.disabled = true;
    el.more.textContent = "Chargement…";
    await Promise.all(pending.map(loadYear));
    return true;
  }

  async function loadAllRemainingForSearch() {
    const pending = state.yearsMeta.filter((y) => !state.loadedYears.has(y.year));
    if (!pending.length) return;
    el.status.hidden = false;
    el.status.className = "status";
    el.status.textContent = "Recherche dans toutes les années…";
    // Load in small batches to keep UI responsive
    for (let i = 0; i < pending.length; i += 4) {
      await Promise.all(pending.slice(i, i + 4).map(loadYear));
      updateMeta();
    }
  }

  let searchTimer = null;
  function onSearchInput() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(async () => {
      state.query = el.q.value;
      if (state.query.trim().length >= 2) {
        await loadAllRemainingForSearch();
      }
      recompute();
    }, 220);
  }

  async function onMore() {
    if (state.shown < state.items.length) {
      renderMore();
      return;
    }
    if (state.query.trim()) {
      await loadAllRemainingForSearch();
      recompute();
      return;
    }
    const loaded = await loadNextYearBatch(2);
    if (loaded) recompute();
    else renderMore();
  }

  document.querySelectorAll(".chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".chip").forEach((b) => b.setAttribute("aria-pressed", "false"));
      btn.setAttribute("aria-pressed", "true");
      state.filter = btn.dataset.filter;
      recompute();
    });
  });

  el.q.addEventListener("input", onSearchInput);
  el.clear.addEventListener("click", () => {
    el.q.value = "";
    state.query = "";
    recompute();
    el.q.focus();
  });
  el.more.addEventListener("click", onMore);

  // Infinite-ish scroll near bottom
  let ticking = false;
  window.addEventListener(
    "scroll",
    () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        ticking = false;
        const nearBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - 400;
        if (nearBottom && !el.more.hidden && !el.more.disabled) {
          onMore();
        }
      });
    },
    { passive: true }
  );

  async function boot() {
    showInstallHint();
    try {
      const res = await fetch("data/index.json");
      if (!res.ok) throw new Error(`index ${res.status}`);
      const index = await res.json();
      state.yearsMeta = index.years || [];
      state.totalKnown = index.counts?.totalEntries || 0;
      await ensureInitialYears();
      recompute();
      // Warm a few more years in background
      loadNextYearBatch(3).then(() => recompute());
    } catch (err) {
      el.status.hidden = false;
      el.status.className = "status error";
      el.status.textContent = "Impossible de charger les données Fedlex. Réessayez plus tard.";
      console.error(err);
    }

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("./sw.js").catch(() => {});
    }
  }

  boot();
})();
