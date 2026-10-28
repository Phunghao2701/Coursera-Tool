(() => {
  "use strict";

  const tabs = [...document.querySelectorAll(".tab[data-tab]")];

  const syncTabs = () => {
    for (const tab of tabs) {
      const panel = document.getElementById(tab.dataset.tab);
      const selected = tab.classList.contains("active");
      tab.setAttribute("aria-selected", String(selected));
      if (panel) panel.setAttribute("aria-hidden", String(!selected));
    }
  };

  for (const [index, tab] of tabs.entries()) {
    tab.addEventListener("click", syncTabs);
    tab.addEventListener("keydown", (event) => {
      const keyDirection = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
      const nextIndex = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (index + keyDirection + tabs.length) % tabs.length;
      if (!keyDirection && event.key !== "Home" && event.key !== "End") return;
      event.preventDefault();
      tabs[nextIndex].focus();
      tabs[nextIndex].click();
    });
  }

  for (const status of document.querySelectorAll("#status, #additionalStatus")) {
    const statusObserver = new MutationObserver(() => {
      const message = status.textContent.trim();
      if (!message || !/(saved|success)/i.test(message) || /refresh/i.test(message)) return;
      status.textContent = `${message} Refresh the Coursera tab to apply changes.`;
    });
    statusObserver.observe(status, { childList: true, characterData: true, subtree: true });
  }

  const tabsObserver = new MutationObserver(syncTabs);
  const tabsRoot = document.querySelector(".tabs");
  if (tabsRoot) tabsObserver.observe(tabsRoot, { attributes: true, subtree: true, attributeFilter: ["class"] });
  syncTabs();
})();
