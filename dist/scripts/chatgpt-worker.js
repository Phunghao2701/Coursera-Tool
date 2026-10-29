(() => {
  "use strict";

  const NATIVE_HOST = "com.coursera.tools.chatgpt";
  const UI_URL = chrome.runtime.getURL("dist/popup.html");
  const pending = new Map();
  let nativePort = null;
  let quizGeneration = 0;
  let quizInFlight = false;
  let disconnecting = false;

  const makeId = () => `ct-${Date.now()}-${crypto.getRandomValues(new Uint32Array(1))[0]}`;

  function friendlyNativeHostError(detail) {
    if (/specified native messaging host not found|native messaging host not found/i.test(String(detail || ""))) {
      return "ChatGPT helper needs one-time setup on this PC. Double-click native-host/Install-CourseraTools-ChatGPT.cmd from the extension folder, then reload Coursera Tools. Edge starts the helper automatically after setup.";
    }
    return detail || "ChatGPT helper disconnected.";
  }

  function isPopup(sender) {
    return sender?.id === chrome.runtime.id && sender.url === UI_URL;
  }

  function ensureNativePort() {
    if (nativePort) return nativePort;

    const port = chrome.runtime.connectNative(NATIVE_HOST);
    nativePort = port;
    port.onMessage.addListener(handleNativeMessage);
    port.onDisconnect.addListener(() => {
      const detail = friendlyNativeHostError(chrome.runtime.lastError?.message);
      nativePort = null;
      for (const [requestId, request] of pending) {
        clearTimeout(request.timeout);
        request.reject(new Error(detail));
        pending.delete(requestId);
      }
      chrome.runtime.sendMessage({ type: "coursera-tools:chatgpt-event", event: "helper-disconnected", error: detail }).catch(() => {});
    });
    return port;
  }

  function hostCall(action, data = {}, timeoutMs = 30000) {
    return new Promise((resolve, reject) => {
      let port;
      try {
        port = ensureNativePort();
      } catch (error) {
        reject(new Error("Install the Coursera Tools ChatGPT helper first."));
        return;
      }

      const requestId = makeId();
      const timeout = setTimeout(() => {
        pending.delete(requestId);
        reject(new Error("The ChatGPT helper did not respond in time."));
      }, timeoutMs);
      pending.set(requestId, { resolve, reject, timeout, action });

      try {
        port.postMessage({ requestId, action, ...data });
      } catch (error) {
        clearTimeout(timeout);
        pending.delete(requestId);
        reject(new Error("Could not send a request to the ChatGPT helper."));
      }
    });
  }

  async function handleNativeMessage(message) {
    if (!message || typeof message !== "object") return;

    if (message.type === "auth_open") {
      const request = pending.get(message.requestId);
      try {
        const authUrl = new URL(message.url);
        if (authUrl.protocol !== "https:" || authUrl.hostname !== "auth.openai.com") {
          throw new Error("The helper returned an untrusted sign-in address.");
        }
        const tab = await chrome.tabs.create({ url: authUrl.href, active: true });
        if (!Number.isInteger(tab?.id)) throw new Error("The sign-in tab was blocked. Reload Coursera Tools and try again.");
        if (request) {
          clearTimeout(request.timeout);
          pending.delete(message.requestId);
          request.resolve({ started: true });
        }
      } catch (error) {
        if (request) {
          clearTimeout(request.timeout);
          pending.delete(message.requestId);
          request.reject(error);
        }
        try { await hostCall("cancel_sign_in", {}, 5000); } catch { /* The host may already be disconnected. */ }
      }
      return;
    }

    if (message.type === "auth_result") {
      chrome.runtime.sendMessage({ type: "coursera-tools:chatgpt-event", event: "auth-result", result: message }).catch(() => {});
    }

    const request = pending.get(message.requestId);
    if (!request) return;
    clearTimeout(request.timeout);
    pending.delete(message.requestId);

    if (message.type === "error" || message.success === false) {
      request.reject(new Error(message.error || "The ChatGPT request failed."));
      return;
    }

    request.resolve(message);
  }

  function sanitizeQuestions(value, detectedControlCount) {
    if (!Array.isArray(value) || value.length < 1 || value.length > 25) {
      if (Array.isArray(value) && value.length === 0) {
        const count = Number(detectedControlCount) || 0;
        if (count === 0) {
          throw new Error("No visible radio or checkbox choices were detected. Open a multiple-choice quiz, wait for it to finish loading, then try again.");
        }
        throw new Error(`Found ${count} visible answer controls, but could not group them into quiz questions. This Coursera quiz layout needs additional support.`);
      }
      throw new Error("Could not find a supported quiz with 1 to 25 questions.");
    }

    const questions = value.map((question, index) => {
      const stem = String(question?.stem || "").trim().slice(0, 2500);
      const options = Array.isArray(question?.options)
        ? question.options.slice(0, 12).map((option) => String(option || "").trim().slice(0, 500))
        : [];
      const kind = options.length > 0
        ? (question?.kind === "multiple_choice" ? "multiple_choice" : "single_choice")
        : "free_text";

      if (!stem) throw new Error(`Question ${index + 1} has no readable text.`);
      if (kind !== "free_text" && options.length < 2) throw new Error(`Question ${index + 1} has too few choices.`);

      return { index: index + 1, kind, stem, options };
    });

    if (JSON.stringify(questions).length > 24000) {
      throw new Error("The quiz section is too large. Try a shorter section.");
    }
    return questions;
  }

  function parseAnswers(text, questionCount) {
    const firstBrace = text.indexOf("{");
    const lastBrace = text.lastIndexOf("}");
    if (firstBrace < 0 || lastBrace <= firstBrace) throw new Error("ChatGPT returned an answer that could not be read.");

    let document;
    try {
      document = JSON.parse(text.slice(firstBrace, lastBrace + 1));
    } catch {
      throw new Error("ChatGPT returned an answer that could not be read.");
    }

    if (!Array.isArray(document.answers)) throw new Error("ChatGPT did not return quiz answers in the expected format.");
    return document.answers
      .filter((answer) => Number.isInteger(Number(answer?.question)) && Number(answer.question) >= 1 && Number(answer.question) <= questionCount)
      .map((answer) => ({
        question: Number(answer.question),
        choices: Array.isArray(answer.choices)
          ? answer.choices.map(Number).filter((choice) => Number.isInteger(choice) && choice >= 1 && choice <= 12)
          : [],
        text: typeof answer.text === "string" ? answer.text.trim().slice(0, 1500) : "",
        explanation: typeof answer.explanation === "string" ? answer.explanation.trim().slice(0, 400) : "",
      }));
  }

  async function activeCourseraTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id || !tab.url) throw new Error("Open the Coursera quiz tab first.");
    const url = new URL(tab.url);
    if (!/(^|\.)coursera\.org$/i.test(url.hostname)) throw new Error("Open a Coursera quiz page before using Quiz AI.");
    return tab;
  }

  async function assistActiveQuiz() {
    if (disconnecting) throw new Error("ChatGPT is disconnecting. Try again after it finishes.");
    const runId = ++quizGeneration;
    quizInFlight = true;
    try {
      const tab = await activeCourseraTab();
      let extraction;
      try {
        extraction = await chrome.tabs.sendMessage(tab.id, { type: "coursera-tools:extract-quiz" });
      } catch {
        throw new Error("Reload the Coursera quiz page, then try again.");
      }
      const questions = sanitizeQuestions(extraction?.questions, extraction?.detectedControlCount);
      const response = await hostCall("ask_quiz", { questions }, 180000);
      if (runId !== quizGeneration || disconnecting) throw new Error("Quiz request was cancelled because ChatGPT was disconnected.");
      const answers = parseAnswers(response.text || "", questions.length);
      if (!answers.length) throw new Error("ChatGPT did not return any usable answers.");

      let filled;
      try {
        filled = await chrome.tabs.sendMessage(tab.id, {
          type: "coursera-tools:fill-quiz",
          answers,
          fingerprint: extraction.fingerprint,
        });
      } catch {
        throw new Error("The quiz page changed while ChatGPT was working. Try again.");
      }
      if (filled?.changed) throw new Error("The quiz changed while ChatGPT was working. No answers were filled; try again.");

      return {
        filled: Number(filled?.filled) || 0,
        total: questions.length,
        explanations: answers.filter((answer) => answer.explanation).map((answer) => ({ question: answer.question, explanation: answer.explanation })),
      };
    } finally {
      if (runId === quizGeneration) quizInFlight = false;
    }
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type !== "coursera-tools:chatgpt") return false;
    if (!isPopup(sender)) {
      sendResponse({ ok: false, error: "This ChatGPT action can only be started from the extension popup." });
      return false;
    }

    (async () => {
      try {
        let result;
        switch (message.action) {
          case "status":
            result = await hostCall("status");
            break;
          case "connect":
            if (disconnecting) throw new Error("ChatGPT is disconnecting. Try again after it finishes.");
            result = await hostCall("sign_in", {}, 30000);
            break;
          case "disconnect":
            if (disconnecting) throw new Error("ChatGPT is already disconnecting.");
            disconnecting = true;
            if (quizInFlight) {
              quizGeneration += 1;
              quizInFlight = false;
              try { await hostCall("cancel_quiz", {}, 5000); } catch { /* Sign-out also cancels in the native host. */ }
            }
            try {
              result = await hostCall("sign_out", {}, 150000);
            } finally {
              disconnecting = false;
            }
            break;
          case "quiz":
            if (message.confirmed !== true) throw new Error("Confirm before sending quiz text to OpenAI.");
            if (disconnecting) throw new Error("ChatGPT is disconnecting. Try again after it finishes.");
            result = await assistActiveQuiz();
            break;
          default:
            throw new Error("Unknown ChatGPT action.");
        }
        sendResponse({ ok: true, result });
      } catch (error) {
        sendResponse({ ok: false, error: error?.message || "ChatGPT could not complete the request." });
      }
    })();

    return true;
  });
})();
