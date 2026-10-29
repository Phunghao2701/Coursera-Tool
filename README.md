# Coursera Tools

Using this extension, complete Coursera courses within seconds. It can be used for free to complete lectures, dialogue, reading materials, ungraded plugins, discussions, shareable link, Locking browser and course backup. All features in this version are available without paid activation.

`Disclaimer:` Quiz Automation provides AI-generated answers, which may not always be accurate.

## Table of Contents

- [Features](#features-status)
- [Installation](#installation)
- [How to use](#how-to-use)
- [Shareable Link](#shareable-link)
- [Quiz Automation](#quiz-automation)
- [Keyboard Shortcuts](#keyboard-shortcuts)

## Features Status

| Feature                              | Status     | Notes |
| ------------------------------------ | ---------- | ----- |
| Complete quizzes                     | 🟢 Working |       |
| Complete lectures                    | 🟢 Working |       |
| Complete reading materials           | 🟢 Working |       |
| Complete ungraded plugins (dialogue) | 🟢 Working |       |
| Complete discussions                 | 🟢 Working |       |
| Shareable link                       | 🟢 Working |       |
| Quiz automation                      | 🟢 Working |       |
| Course Backup                        | 🟢 Working |       |
| Locking browser                      | 🟢 Working |       |

## Installation

1. Clone or download the repository.
2. Open the Chrome browser.
3. Go to `chrome://extensions/`.
4. Enable `Developer mode`.
5. Click on `Load unpacked`.
6. Select the downloaded folder.
7. The extension will be added to the browser.

### ChatGPT helper setup (once per PC)

With Node.js/npm installed, run this from the repository folder:

```powershell
npx --yes --package=./native-host -- coursera-tools-chatgpt-helper --browser Edge
```

Use `--browser Chrome` for Chrome or `--browser Both` for both browsers. The installer detects the Coursera Tools extension ID from the selected browser profile when possible; if it finds multiple copies or cannot detect one, it asks for the ID shown at the browser's extensions page. It registers the native helper for the current Windows account and does not require administrator access. After setup, the browser starts the helper automatically when Quiz AI connects. Reload Coursera Tools, then select **Continue with ChatGPT** in the popup. Run setup once per Windows account and computer.

If Node.js/npm is not installed, the Edge setup remains available by double-clicking `native-host/Install-CourseraTools-ChatGPT.cmd`.

## How to use

1. Open your Coursera course.
2. Click on the Extension icon.
3. Choose the task you want to automate.
4. Sit back while the Extension completes the task.

## Shareable Link

To generate a **Shareable Link** for your assignment submission:

1. **Navigate to the Submission Page**: Ensure you're on the "My Submission" tab of your assignment.

2. **Use the Extension**: Click the "Shareable Link" button provided by the extension.

## Quiz Automation

Extension will automatically get the solutions and mark the correct options.

`Note:` When you Reattempt the quiz, it's using the previous attempt feedback to improve the accuracy of the answers.

1. Open the quiz you want to complete.
2. **Wait 5 seconds** for answers to load.
3. If answers aren't marked correctly, press Alt + Z for a refresh.
4. Submit your answers.

## Keyboard Shortcuts

- `Alt + W` or `Alt + B`: Toggle the Extension
- `Alt + Z` or `Ctrl + Shift + Z`: Refresh the answers or Navigate to the next question(mark as correct)

---

> ⚠️ This extension is an independent tool designed for personal learning productivity and is not affiliated with or endorsed by Coursera.

---
