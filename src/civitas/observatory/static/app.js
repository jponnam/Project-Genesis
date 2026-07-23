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

  // Reveal motion: animate from a class so first paint stays readable
  // (important for docs screenshots and no-JS readability).
  document.querySelectorAll("[data-reveal]").forEach((el, index) => {
    if (reduce) {
      el.classList.add("is-revealed");
      return;
    }
    window.setTimeout(() => {
      el.classList.add("is-revealed");
    }, 60 + index * 50);
  });
})();
