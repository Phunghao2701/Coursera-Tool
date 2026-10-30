# Coursera Tools release installation

## Microsoft Edge

1. Download `Coursera-Tools-<version>.zip` from the latest GitHub Release's **Assets** section. Do not download GitHub's automatically generated **Source code** archive.
2. Extract the ZIP to a permanent folder, such as `%LOCALAPPDATA%\CourseraTools\Extension`. Keep the folder in the same location so the unpacked extension ID remains stable.
3. Open `edge://extensions`, turn on **Developer mode**, choose **Load unpacked**, and select the extracted folder containing `manifest.json`.
4. To enable ChatGPT quiz help, double-click `native-host\Install-CourseraTools-ChatGPT.cmd` inside the extracted folder once. The release includes a prebuilt helper; Node.js and npm are not required.

## Google Chrome

Repeat the steps above using `chrome://extensions`. To register the ChatGPT helper for Chrome, open PowerShell in the extracted folder and run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\native-host\install.ps1 -Browser Chrome
```

Use `-Browser Both` to register the helper for both browsers.

## Update

Download the new release ZIP and replace the contents of the same extracted folder. In the browser's extensions page, click **Reload**, then refresh any open Coursera tabs. GitHub Releases do not push updates to unpacked extensions automatically.

The native helper is installed separately under the current Windows account. You do not need to reinstall it for ordinary extension updates. If a release announces a native helper change, close Edge and Chrome, then run the helper installer again.

## Remove the ChatGPT helper

Run this from the extracted extension folder:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\native-host\uninstall.ps1 -Browser Both
```

The saved ChatGPT credentials are kept unless `-RemoveSavedCredentials` is also specified.
