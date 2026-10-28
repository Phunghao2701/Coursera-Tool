(() => {
  "use strict";

  const root = globalThis;
  if (root.__courseraNavigationGuardInstalled) return;
  root.__courseraNavigationGuardInstalled = true;

  const allowedDestination = (value) => {
    if (value == null || String(value).trim() === "") return true;

    let target;
    try {
      const base = root.location?.href || "https://www.coursera.org/";
      target = new URL(String(value), base);
    } catch {
      return false;
    }

    if (["chrome-extension:", "edge-extension:", "moz-extension:", "data:", "about:"].includes(target.protocol)) {
      return true;
    }

    if (target.protocol === "blob:") {
      const origin = target.origin;
      if (origin === "null") return true;
      try {
        target = new URL(origin);
      } catch {
        return false;
      }
    }

    if (target.protocol !== "https:" && target.protocol !== "http:") return false;
    const hostname = target.hostname.toLowerCase();
    return hostname === "coursera.org" || hostname.endsWith(".coursera.org");
  };

  root.__courseraNavigationAllowed = allowedDestination;

  const patchApi = (api, method, propertiesIndex, callbackIndex) => {
    try {
      const original = api?.[method];
      if (typeof original !== "function" || original.__courseraNavigationGuard) return;

      const guarded = function (...args) {
        const properties = args[propertiesIndex];
        const destinations = properties?.url;
        const allowed = Array.isArray(destinations)
          ? destinations.every(allowedDestination)
          : allowedDestination(destinations);

        if (!allowed) {
          const callback = args[callbackIndex];
          if (typeof callback === "function") {
            callback(undefined);
            return undefined;
          }
          return Promise.resolve(undefined);
        }

        return Reflect.apply(original, this, args);
      };

      Object.defineProperty(guarded, "__courseraNavigationGuard", { value: true });
      api[method] = guarded;
    } catch {
      // Some browser API objects expose methods that cannot be reassigned.
    }
  };

  patchApi(root.chrome?.tabs, "create", 0, 1);
  patchApi(root.chrome?.tabs, "update", 1, 2);
  patchApi(root.chrome?.windows, "create", 0, 1);
  patchApi(root.location, "assign", 0, 1);
  patchApi(root.location, "replace", 0, 1);

  const patchFormMethod = (method) => {
    try {
      const prototype = root.HTMLFormElement?.prototype;
      const original = prototype?.[method];
      if (typeof original !== "function" || original.__courseraNavigationGuard) return;

      const guarded = function (...args) {
        if (!allowedDestination(this.action)) return undefined;
        return Reflect.apply(original, this, args);
      };
      Object.defineProperty(guarded, "__courseraNavigationGuard", { value: true });
      prototype[method] = guarded;
    } catch {
      // Some browser prototypes expose methods that cannot be reassigned.
    }
  };

  patchFormMethod("submit");
  patchFormMethod("requestSubmit");

  try {
    const originalOpen = root.window?.open;
    if (typeof originalOpen === "function" && !originalOpen.__courseraNavigationGuard) {
      const guardedOpen = function (url, ...args) {
        if (!allowedDestination(url)) return null;
        return Reflect.apply(originalOpen, this, [url, ...args]);
      };
      Object.defineProperty(guardedOpen, "__courseraNavigationGuard", { value: true });
      root.window.open = guardedOpen;
    }
  } catch {
    // Leave the browser API untouched if the host makes it immutable.
  }

  root.document?.addEventListener("click", (event) => {
    if (event.isTrusted) return;
    const target = event.target instanceof root.Element ? event.target : event.target?.parentElement;
    const anchor = target?.closest?.("a[href]");
    if (!anchor || allowedDestination(anchor.href)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);

  root.document?.addEventListener("submit", (event) => {
    if (event.isTrusted) return;
    const form = event.target;
    if (!(form instanceof root.HTMLFormElement) || allowedDestination(form.action)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);

  try {
    const anchorPrototype = root.HTMLAnchorElement?.prototype;
    const originalClick = anchorPrototype?.click;
    if (typeof originalClick === "function" && !originalClick.__courseraNavigationGuard) {
      const guardedClick = function (...args) {
        if (!allowedDestination(this.href)) return undefined;
        return Reflect.apply(originalClick, this, args);
      };
      Object.defineProperty(guardedClick, "__courseraNavigationGuard", { value: true });
      anchorPrototype.click = guardedClick;
    }
  } catch {
    // Leave anchor behavior untouched if the host makes it immutable.
  }
})();
