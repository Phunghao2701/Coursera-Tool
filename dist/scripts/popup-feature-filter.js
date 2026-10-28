(() => {
  "use strict";

  const isSkipVideoButton = (element) =>
    /^skip\s*video\+/i.test((element?.textContent || "").replace(/\s+/g, " ").trim());

  const removeSkipVideoFeature = () => {
    const grid = document.getElementById("courseraModelGrid");
    if (!grid) return false;

    for (const button of grid.querySelectorAll(".courseraModelBtn")) {
      if (!isSkipVideoButton(button)) continue;
      (button.closest(".courseraBtnWrapper") || button).remove();
    }

    return true;
  };

  document.addEventListener(
    "click",
    (event) => {
      const target = event.target instanceof Element ? event.target : event.target?.parentElement;
      const button = target?.closest?.(".courseraModelBtn");
      if (!button || !isSkipVideoButton(button)) return;

      event.preventDefault();
      event.stopImmediatePropagation();
    },
    true,
  );

  const gridObserver = new MutationObserver(removeSkipVideoFeature);
  const rootObserver = new MutationObserver(() => {
    if (!removeSkipVideoFeature()) return;

    const grid = document.getElementById("courseraModelGrid");
    if (grid) gridObserver.observe(grid, { childList: true, subtree: true });
    rootObserver.disconnect();
  });

  if (document.documentElement) {
    rootObserver.observe(document.documentElement, { childList: true, subtree: true });
  }

  document.addEventListener("DOMContentLoaded", () => {
    removeSkipVideoFeature();
    const grid = document.getElementById("courseraModelGrid");
    if (grid) gridObserver.observe(grid, { childList: true, subtree: true });
    rootObserver.disconnect();
  }, { once: true });

  removeSkipVideoFeature();
})();
