(() => {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll(".bar-fill[data-width]").forEach((el, index) => {
    const width = Number(el.getAttribute("data-width") || "0");
    const apply = () => {
      el.style.width = `${Math.max(0, Math.min(100, width))}%`;
    };
    if (reduce) {
      apply();
      return;
    }
    el.style.width = "0%";
    window.setTimeout(apply, 80 + index * 40);
  });

  document.querySelectorAll("[data-reveal]").forEach((el, index) => {
    if (reduce) {
      el.style.opacity = "1";
      return;
    }
    el.style.opacity = "0";
    el.style.transform = "translateY(8px)";
    el.style.transition = "opacity 420ms ease, transform 420ms ease";
    window.setTimeout(() => {
      el.style.opacity = "1";
      el.style.transform = "translateY(0)";
    }, 60 + index * 50);
  });
})();
