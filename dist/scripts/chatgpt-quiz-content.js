(() => {
  "use strict";

  const CONTROL_SELECTOR = 'input[type="radio"], input[type="checkbox"], [role="radio"], [role="checkbox"]';
  const normalize = (value) => String(value || "").replace(/\s+/g, " ").trim();

  function visible(element) {
    if (!(element instanceof Element)) return false;

    // Coursera hides some native radio inputs visually and draws the control
    // on their associated label. Check that label before rejecting an input
    // for opacity: 0 or a zero-sized hit target.
    if (element instanceof HTMLInputElement && element.labels) {
      const hasVisibleLabel = Array.from(element.labels).some((label) => {
        const labelStyle = window.getComputedStyle(label);
        if (labelStyle.display === "none" || labelStyle.visibility === "hidden" || Number(labelStyle.opacity) === 0) return false;
        const labelRect = label.getBoundingClientRect();
        return labelRect.width > 0 && labelRect.height > 0;
      });
      if (hasVisibleLabel) return true;
    }

    const style = window.getComputedStyle(element);
    if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity) === 0) return false;
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function controlsWithin(element) {
    return Array.from(element.querySelectorAll(CONTROL_SELECTOR)).filter((control) => visible(control) && !control.disabled);
  }

  function looksLikeQuestionContainer(element) {
    const semantic = [
      element.tagName === "FIELDSET",
      /^(group|radiogroup)$/i.test(element.getAttribute("role") || ""),
      /question|assessment|quiz/i.test(element.getAttribute("data-testid") || ""),
      /question|assessment|quiz/i.test(typeof element.className === "string" ? element.className : ""),
    ];
    return semantic.some(Boolean);
  }

  function findGroup(control) {
    let fallback = null;
    let current = control.parentElement;
    let depth = 0;
    while (current && current !== document.body && depth < 12) {
      const controls = controlsWithin(current);
      if (controls.length >= 2 && controls.length <= 12) {
        if (!fallback) fallback = current;
        const options = controls.map(optionLabel).filter(Boolean);
        const stem = removeOptionLines(current, options);
        if (stem.length >= 4) return current;
        if (looksLikeQuestionContainer(current)) fallback = current;
      }
      if (current.tagName === "FORM" && fallback) break;
      current = current.parentElement;
      depth += 1;
    }
    return fallback;
  }

  function optionLabel(control) {
    const aria = normalize(control.getAttribute("aria-label"));
    if (aria) return aria;

    const labelledBy = normalize(control.getAttribute("aria-labelledby"));
    if (labelledBy) {
      const text = labelledBy.split(" ").map((id) => normalize(document.getElementById(id)?.innerText)).filter(Boolean).join(" ");
      if (text) return text;
    }

    if (control instanceof HTMLInputElement) {
      const label = control.labels?.[0] || control.closest("label");
      if (label) return normalize(label.innerText || label.textContent);
    }

    const title = normalize(control.getAttribute("title"));
    return title || normalize(control.innerText || control.textContent);
  }

  function removeOptionLines(container, options) {
    const optionSet = new Set(options.map(normalize).filter(Boolean));
    const text = normalize(container.innerText || container.textContent);
    const lines = (container.innerText || container.textContent || "").split(/\n+/).map(normalize).filter(Boolean);
    const stripOptionPrefix = (line) => line
      .replace(/^(?:[A-Z]|\d+)[.)]\s+/i, "")
      .replace(/^[-*•]\s+/, "");
    const remaining = lines.filter((line) => {
      const content = stripOptionPrefix(line);
      return !optionSet.has(line) && !optionSet.has(content) && !/^question\s*\d*$/i.test(content);
    });
    let stem = normalize(remaining.join(" "));
    if (!stem && text) {
      stem = text;
      for (const option of optionSet) stem = normalize(stem.replace(option, " "));
    }
    return stem.slice(0, 2500);
  }

  function collectQuestions() {
    const allControls = Array.from(document.querySelectorAll(CONTROL_SELECTOR)).filter((control) => visible(control) && !control.disabled);
    const groups = [];
    const seen = new Set();

    for (const control of allControls) {
      const group = findGroup(control);
      if (!group || seen.has(group)) continue;
      seen.add(group);

      const controls = controlsWithin(group);
      if (controls.length < 2 || controls.length > 12) continue;
      const optionEntries = controls.map((item) => ({ control: item, text: optionLabel(item) })).filter((item) => item.text);
      const options = optionEntries.map((item) => item.text);
      if (options.length < 2) continue;
      const stem = removeOptionLines(group, options);
      if (!stem || stem.length < 4) continue;

      const validControls = optionEntries.map((item) => item.control);
      const hasCheckbox = validControls.some((item) => item instanceof HTMLInputElement ? item.type === "checkbox" : item.getAttribute("role") === "checkbox");
      groups.push({
        element: group,
        controls: validControls,
        kind: hasCheckbox ? "multiple_choice" : "single_choice",
        stem,
        options,
      });
    }

    return groups.slice(0, 25);
  }

  function readQuestions() {
    return collectQuestions().map(({ kind, stem, options }) => ({ kind, stem, options }));
  }

  function fingerprintQuestions(questions) {
    return JSON.stringify(questions.map((question) => {
      const options = Array.isArray(question.options) ? question.options.slice(0, 12).map((option) => normalize(option).slice(0, 500)) : [];
      return {
        kind: options.length ? (question.kind === "multiple_choice" ? "multiple_choice" : "single_choice") : "free_text",
        stem: normalize(question.stem).slice(0, 2500),
        options,
      };
    }));
  }

  function applyChoice(control) {
    if (control instanceof HTMLInputElement) {
      const label = control.labels?.[0] || control.closest("label");
      (label || control).click();
      control.checked = true;
      control.dispatchEvent(new Event("input", { bubbles: true }));
      control.dispatchEvent(new Event("change", { bubbles: true }));
      return;
    }
    control.click();
    control.dispatchEvent(new Event("input", { bubbles: true }));
    control.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function fillAnswers(answers, expectedFingerprint) {
    if (!Array.isArray(answers)) return { filled: 0 };
    const questions = collectQuestions();
    const snapshot = questions.map(({ kind, stem, options }) => ({ kind, stem, options }));
    if (!expectedFingerprint || fingerprintQuestions(snapshot) !== expectedFingerprint) return { filled: 0, changed: true };
    let filled = 0;

    for (const answer of answers) {
      const questionIndex = Number(answer?.question) - 1;
      const group = questions[questionIndex];
      if (!group) continue;
      const controls = group.controls;
      const choices = Array.isArray(answer.choices) ? answer.choices : [];
      let changed = false;
      for (const choice of choices) {
        const control = controls[Number(choice) - 1];
        if (!control) continue;
        applyChoice(control);
        changed = true;
      }
      if (changed) filled += 1;
    }

    return { filled };
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type === "coursera-tools:extract-quiz") {
      const questions = readQuestions();
      const detectedControlCount = Array.from(document.querySelectorAll(CONTROL_SELECTOR))
        .filter((control) => visible(control) && !control.disabled).length;
      sendResponse({ questions, fingerprint: fingerprintQuestions(questions), detectedControlCount });
      return false;
    }
    if (message?.type === "coursera-tools:fill-quiz") {
      sendResponse(fillAnswers(message.answers, message.fingerprint));
      return false;
    }
    return false;
  });
})();
