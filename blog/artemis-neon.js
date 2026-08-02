(() => {
  "use strict";
  const consoleElement = document.querySelector("[data-power-console]");

  const buttons = consoleElement ? [...consoleElement.querySelectorAll("[data-power-select]")] : [];
  const output = consoleElement?.querySelector("[data-power-output]");
  const descriptions = {
    idle: "Telemetry watch",
    warming: "Core warming",
    active: "Stabilized core",
    critical: "Priority response",
    locked: "Human gate locked",
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const state = button.dataset.powerSelect;
      if (!Object.hasOwn(descriptions, state)) return;
      if (consoleElement) consoleElement.dataset.powerState = state;
      buttons.forEach((candidate) => candidate.setAttribute("aria-pressed", String(candidate === button)));
      if (output) output.textContent = descriptions[state];
    });
  });

  const architecture = document.querySelector("[data-architecture-console]");
  if (architecture) {
    const filters = [...architecture.querySelectorAll("[data-layer-select]")];
    const nodes = [...architecture.querySelectorAll("[data-layer]")];
    const status = architecture.querySelector("[data-layer-status]");
    const detail = architecture.querySelector("[data-layer-detail]");
    filters.forEach((filter) => filter.addEventListener("click", () => {
      const selected = filter.dataset.layerSelect;
      filters.forEach((item) => item.setAttribute("aria-pressed", String(item === filter)));
      nodes.forEach((node) => node.classList.toggle("is-muted", selected !== "all" && node.dataset.layer !== selected));
      if (status) status.textContent = selected === "all" ? "All trust domains visible" : `${selected} domain isolated`;
    }));
    nodes.forEach((node) => node.addEventListener("click", () => {
      nodes.forEach((item) => item.classList.toggle("is-selected", item === node));
      if (!detail) return;
      detail.querySelector("span").textContent = node.querySelector("strong").textContent;
      detail.querySelector("p").textContent = node.dataset.detail;
      detail.focus({ preventScroll: true });
    }));
  }

  const progress = document.createElement("div");
  progress.className = "reading-progress";
  progress.setAttribute("aria-hidden", "true");
  document.body.prepend(progress);
  const updateProgress = () => {
    const distance = document.documentElement.scrollHeight - innerHeight;
    progress.style.transform = `scaleX(${distance > 0 ? Math.min(scrollY / distance, 1) : 0})`;
  };
  addEventListener("scroll", updateProgress, { passive: true });
  updateProgress();

  document.querySelectorAll("pre").forEach((pre) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-code";
    button.textContent = "Copy code";
    button.setAttribute("aria-label", "Copy this code example");
    button.addEventListener("click", async () => {
      if (!navigator.clipboard) return;
      await navigator.clipboard.writeText(pre.querySelector("code")?.textContent || pre.textContent);
      button.textContent = "Copied";
      setTimeout(() => { button.textContent = "Copy code"; }, 1600);
    });
    pre.prepend(button);
  });
})();
