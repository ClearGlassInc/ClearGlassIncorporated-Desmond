(() => {
  "use strict";
  const consoleElement = document.querySelector("[data-power-console]");
  if (!consoleElement) return;

  const buttons = [...consoleElement.querySelectorAll("[data-power-select]")];
  const output = consoleElement.querySelector("[data-power-output]");
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
      consoleElement.dataset.powerState = state;
      buttons.forEach((candidate) => candidate.setAttribute("aria-pressed", String(candidate === button)));
      if (output) output.textContent = descriptions[state];
    });
  });
})();
