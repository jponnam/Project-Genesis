(() => {
  "use strict";

  const root = document.documentElement;
  const toastRegion = document.querySelector("[data-toast-region]");
  const showToast = (message) => {
    if (!toastRegion) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    toastRegion.append(toast);
    window.setTimeout(() => toast.remove(), 2600);
  };
  if (new URLSearchParams(window.location.search).get("launched") === "1") {
    window.setTimeout(() => showToast("Execution completed and artifacts were persisted."), 50);
  }

  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    const update = () => {
      const light = root.dataset.theme === "light";
      button.setAttribute("aria-label", light ? "Switch to dark theme" : "Switch to light theme");
      button.title = light ? "Switch to dark theme" : "Switch to light theme";
    };
    update();
    button.addEventListener("click", () => {
      root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
      localStorage.setItem("civitas-theme", root.dataset.theme);
      update();
    });
  });

  const drawer = document.querySelector("[data-drawer]");
  const trigger = document.querySelector("[data-drawer-trigger]");
  const backdrop = document.querySelector("[data-drawer-backdrop]");
  const closeDrawer = () => {
    if (!drawer || !trigger || !backdrop) return;
    drawer.classList.remove("is-open");
    trigger.setAttribute("aria-expanded", "false");
    backdrop.hidden = true;
    document.body.style.overflow = "";
  };
  const openDrawer = () => {
    if (!drawer || !trigger || !backdrop) return;
    drawer.classList.add("is-open");
    trigger.setAttribute("aria-expanded", "true");
    backdrop.hidden = false;
    document.body.style.overflow = "hidden";
    drawer.querySelector("a")?.focus();
  };
  trigger?.addEventListener("click", () => drawer?.classList.contains("is-open") ? closeDrawer() : openDrawer());
  backdrop?.addEventListener("click", closeDrawer);
  drawer?.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeDrawer));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && drawer?.classList.contains("is-open")) {
      closeDrawer();
      trigger?.focus();
    }
  });

  document.querySelectorAll(".bar-fill[data-width]").forEach((element) => {
    const width = Number(element.getAttribute("data-width") || "0");
    element.style.width = `${Math.max(0, Math.min(100, width))}%`;
  });

  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const selector = button.getAttribute("data-copy");
      const source = selector ? document.querySelector(selector) : null;
      const value = source?.textContent?.trim() || button.getAttribute("data-copy-value") || "";
      if (!value) return;
      try {
        await navigator.clipboard.writeText(value);
        showToast("Copied to clipboard");
      } catch {
        showToast("Copy unavailable");
      }
    });
  });

  document.querySelectorAll("[data-submit-state]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const message = form.getAttribute("data-confirm");
      if (message && !window.confirm(message)) {
        event.preventDefault();
        return;
      }
      const button = form.querySelector("button[type='submit']");
      if (button) {
        button.disabled = true;
        button.dataset.originalLabel = button.textContent || "";
        button.textContent = button.getAttribute("data-loading-label") || "Running…";
      }
    });
  });

  document.querySelectorAll("[data-table-search]").forEach((input) => {
    const target = document.querySelector(input.getAttribute("data-table-search") || "");
    if (!target) return;
    input.addEventListener("input", () => {
      const query = input.value.trim().toLowerCase();
      target.querySelectorAll("tbody tr").forEach((row) => {
        row.hidden = Boolean(query) && !row.textContent.toLowerCase().includes(query);
      });
    });
  });

  document.querySelectorAll("[data-sort-table]").forEach((button) => {
    button.addEventListener("click", () => {
      const table = button.closest("table");
      const body = table?.querySelector("tbody");
      if (!body) return;
      const index = Number(button.getAttribute("data-column") || "0");
      const nextDirection = button.dataset.direction === "asc" ? "desc" : "asc";
      const rows = [...body.querySelectorAll("tr")];
      rows.sort((left, right) => {
        const a = left.children[index]?.getAttribute("data-sort-value") || left.children[index]?.textContent || "";
        const b = right.children[index]?.getAttribute("data-sort-value") || right.children[index]?.textContent || "";
        const numeric = Number(a) - Number(b);
        const result = Number.isNaN(numeric) ? a.localeCompare(b) : numeric;
        return nextDirection === "asc" ? result : -result;
      });
      rows.forEach((row) => body.append(row));
      button.dataset.direction = nextDirection;
      button.setAttribute("aria-sort", nextDirection === "asc" ? "ascending" : "descending");
    });
  });

  document.querySelectorAll("[data-swap-runs]").forEach((button) => {
    button.addEventListener("click", () => {
      const form = button.closest("form");
      const left = form?.querySelector("[name='left']");
      const right = form?.querySelector("[name='right']");
      if (!left || !right) return;
      [left.value, right.value] = [right.value, left.value];
    });
  });

  document.querySelectorAll("[data-run-selector]").forEach((form) => {
    form.querySelector("[data-open-selected]")?.addEventListener("click", () => {
      const selected = form.querySelector("[name='run_id']")?.value;
      if (selected) window.location.assign(`/ui/runs/${encodeURIComponent(selected)}`);
    });
  });
})();
