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

### Install a release (no source checkout or Node.js)

Download `Coursera-Tools-<version>.zip` from the [latest GitHub Release](https://github.com/Phunghao2701/Coursera-Tool/releases/latest) under **Assets**. Extract it to a permanent folder, open `edge://extensions`, enable **Developer mode**, choose **Load unpacked**, and select the extracted folder containing `manifest.json`.

For ChatGPT quiz help, double-click `native-host/Install-CourseraTools-ChatGPT.cmd` from the extracted folder once. The release includes a prebuilt helper, so end users do not need Node.js or npm. Chrome users can follow [`release/INSTALL.md`](release/INSTALL.md) for the Chrome-specific setup command.

### Updates

GitHub Releases do not automatically update an unpacked extension. Download the new release ZIP, replace the files in the same extracted folder, click **Reload** on the browser's extensions page, then refresh Coursera tabs. Ordinary extension updates do not require reinstalling the native helper.

### Install from source (maintainers)

1. Clone or download the repository.
2. Open `edge://extensions` (or `chrome://extensions`), enable **Developer mode**, and choose **Load unpacked**.
3. Select the repository folder containing `manifest.json`.
4. To set up the ChatGPT helper from source with Node.js/npm, run this from the repository folder:

```powershell
npx --yes --package=./native-host -- coursera-tools-chatgpt-helper --browser Edge
```

Use `--browser Chrome` or `--browser Both` as needed. The helper installer is also available at `native-host/Install-CourseraTools-ChatGPT.cmd` for Edge without Node.js.

### Publish a release (maintainers)

Update `manifest.json`'s version, commit the change, and push a matching `v<version>` tag. For example, after setting the version to `3.7.1`:

```powershell
git tag v3.7.1
git push origin v3.7.1
```

GitHub Actions validates the tag, builds the Windows helper, packages the user files, and publishes the ZIP to a GitHub Release. Users still download each new release manually and reload their unpacked extension.

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
