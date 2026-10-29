(() => {
  "use strict";

  const connectButton = document.getElementById("chatgptConnectBtn");
  const quizButton = document.getElementById("chatgptQuizBtn");
  const disconnectButton = document.getElementById("chatgptDisconnectBtn");
  const connectionState = document.getElementById("chatgptConnectionState");
  const message = document.getElementById("chatgptMessage");
  let connected = false;

  if (!connectButton || !quizButton || !disconnectButton || !connectionState || !message) return;

  function setMessage(text, isError = false) {
    message.textContent = text || "";
    message.classList.toggle("is-error", Boolean(isError));
  }

  function setBusy(button, busy, label) {
    button.disabled = busy;
    button.classList.toggle("is-loading", busy);
    if (label) button.textContent = label;
  }

  async function send(action, extra = {}) {
    try {
      return await chrome.runtime.sendMessage({
        type: "coursera-tools:chatgpt",
        action,
        ...extra,
      });
    } catch {
      return { ok: false, error: "The extension could not reach its background worker. Reload the extension and try again." };
    }
  }

  function renderStatus(status) {
    connected = Boolean(status?.connected);
    if (connected) {
      const account = status.email || status.name || "ChatGPT account";
      connectionState.textContent = `Connected · ${account}`;
      connectionState.title = account;
      connectionState.style.color = "#087443";
      connectButton.classList.add("hidden");
      quizButton.disabled = false;
      disconnectButton.classList.remove("hidden");
      return;
    }

    connectionState.textContent = "Not connected";
    connectionState.title = "Connect a ChatGPT account to use Quiz AI.";
    connectionState.style.color = "";
    connectButton.classList.remove("hidden");
    quizButton.disabled = true;
    disconnectButton.classList.add("hidden");
  }

  async function refreshStatus() {
    connectionState.textContent = "Checking connection…";
    const response = await send("status");
    if (!response?.ok) {
      renderStatus({ connected: false });
      setMessage(response?.error || "Install the local ChatGPT helper to connect.", true);
      return;
    }
    renderStatus(response.result);
  }

  connectButton.addEventListener("click", async () => {
    setMessage("");
    setBusy(connectButton, true, "Opening ChatGPT…");
    const response = await send("connect");
    setBusy(connectButton, false, "Continue with ChatGPT");
    if (!response?.ok) {
      setMessage(response?.error || "Could not start ChatGPT sign-in.", true);
      return;
    }
    setMessage("Complete sign-in and allow ChatGPT plan usage in the opened tab.");
  });

  quizButton.addEventListener("click", async () => {
    if (!connected) return;
    setMessage("Reading the current quiz and asking ChatGPT…");
    setBusy(quizButton, true, "Working…");
    const response = await send("quiz", { confirmed: true });
    setBusy(quizButton, false, "Fill quiz answers");
    if (!response?.ok) {
      setMessage(response?.error || "ChatGPT could not complete the quiz request.", true);
      return;
    }

    const filled = Number(response.result?.filled) || 0;
    const total = Number(response.result?.total) || 0;
    if (filled === 0) {
      setMessage("ChatGPT returned no answers that could be filled. Review the quiz and try again.", true);
      return;
    }
    setMessage(`Filled ${filled} answer${filled === 1 ? "" : "s"} across ${total} question${total === 1 ? "" : "s"}. Review them on Coursera before submitting.`);
  });

  disconnectButton.addEventListener("click", async () => {
    setBusy(disconnectButton, true, "Disconnecting…");
    setMessage("Disconnecting ChatGPT…");
    const response = await send("disconnect");
    setBusy(disconnectButton, false, "Disconnect ChatGPT");
    if (!response?.ok) {
      setMessage(response?.error || "Could not disconnect ChatGPT.", true);
      return;
    }
    setMessage(response.result?.revoked
      ? "ChatGPT disconnected. OpenAI revoked the refresh token."
      : "Disconnected locally. Remote revocation was not confirmed; review ChatGPT settings if you want to revoke access there.");
    renderStatus({ connected: false });
  });

  chrome.runtime.onMessage.addListener((event) => {
    if (event?.type !== "coursera-tools:chatgpt-event") return;
    if (event.event === "auth-result") {
      if (event.result?.success) {
        setMessage("ChatGPT is connected. You can now use Quiz AI.");
        refreshStatus();
      } else {
        setMessage(event.result?.error || "ChatGPT sign-in did not complete.", true);
      }
    }
    if (event.event === "helper-disconnected") {
      renderStatus({ connected: false });
      setMessage(event.error || "The local ChatGPT helper disconnected. Reload the extension and try again.", true);
    }
  });

  refreshStatus();
})();
