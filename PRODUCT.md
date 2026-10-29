# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary user is the owner of this local browser profile, a Coursera learner who wants quick access to course-task automation while studying.

## Product Purpose

The extension exposes actions for quizzes, lectures, readings, discussions, dialogue activities, ungraded plugins, shareable links, and course backup from the current Coursera tab.

## Operating Context

The user opens the extension popup while a Coursera course is active, selects an action, and reviews the result in the course tab.

## Capabilities and Constraints

- The popup is the primary action surface; existing action names and handlers are in the bundled extension scripts.
- Skip Video+ is being removed from the available popup actions at the user's request.
- Extension actions must not send users to unrelated external pages.
- The user does not want automatic Coursera account linking, usage counters, or expiry dates in the popup.
- The popup includes an optional ChatGPT quiz assistant. It uses the local Sign in with ChatGPT flow and a native helper for the loopback OAuth callback; the helper stores tokens locally with Windows DPAPI.
- Quiz questions and choices are sent to OpenAI when the user clicks Fill quiz answers; the popup displays this disclosure. The assistant fills answers but does not submit the Coursera quiz.
- The current quiz assistant supports visible multiple-choice and checkbox questions. ChatGPT plan eligibility and usage limits apply; no OpenAI API key or ChatGPT cookie is collected.
- The bundled action runner is obfuscated and sends one-way messages, so the popup cannot confirm when a course action has finished. Do not show a completion or refresh alert until the runner exposes a reliable completion signal.

## Brand Commitments

- The product name is Coursera Tools.
- The logo is the selected open-book C mark in `dist/assets/coursera-tools-logo.png`.
- The extension is independent and is not endorsed by Coursera, as stated in README.md.

## Evidence on Hand

- `README.md` describes the extension's actions and intended use.
- `manifest.json` defines the browser-extension name, icons, and Coursera host access.
- The current UI is implemented in `dist/popup.html`, `dist/ui/popup.css`, and the obfuscated `dist/scripts/popup.js` bundle.

## Product Principles

- Put the current course actions within one click of the learner.
- Keep controls clear and avoid unnecessary account or plan information.
- Keep extension-initiated navigation relevant to the current Coursera task.
- Make any external AI assistance explicit before quiz content is sent.
