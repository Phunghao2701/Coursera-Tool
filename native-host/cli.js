#!/usr/bin/env node
'use strict';

const path = require('node:path');
const { spawnSync } = require('node:child_process');

function fail(message) {
  console.error(message);
  process.exitCode = 1;
}

if (process.platform !== 'win32') {
  fail('Coursera Tools native helper setup and removal currently support Windows only.');
} else {
  let action = 'install';
  const args = process.argv.slice(2);
  if (args[0] === 'uninstall') {
    action = 'uninstall';
    args.shift();
  }

  let browser = action === 'uninstall' ? 'Both' : 'Edge';
  const extensionIds = [];
  let removeSavedCredentials = false;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === '--browser') {
      browser = args[++index] || '';
    } else if (arg.startsWith('--browser=')) {
      browser = arg.slice('--browser='.length);
    } else if (arg === '--extension-id') {
      extensionIds.push(args[++index] || '');
    } else if (arg.startsWith('--extension-id=')) {
      extensionIds.push(arg.slice('--extension-id='.length));
    } else if (arg === '--remove-saved-credentials') {
      removeSavedCredentials = true;
    } else if (arg === '--help' || arg === '-h') {
      console.log('Usage:');
      console.log('  coursera-tools-chatgpt-helper [--browser Edge|Chrome|Both] [--extension-id ID]');
      console.log('  coursera-tools-chatgpt-helper uninstall [--browser Edge|Chrome|Both] [--remove-saved-credentials]');
      process.exit(0);
    } else {
      fail(`Unknown option: ${arg}`);
      break;
    }
  }

  if (!process.exitCode && !['Edge', 'Chrome', 'Both'].includes(browser)) {
    fail('Choose Edge, Chrome, or Both with --browser.');
  }
  if (!process.exitCode && action === 'uninstall' && extensionIds.length) {
    fail('--extension-id is only used during installation.');
  }
  if (!process.exitCode && action === 'install' && removeSavedCredentials) {
    fail('--remove-saved-credentials is only used with uninstall.');
  }

  if (!process.exitCode) {
    const script = path.join(__dirname, action === 'uninstall' ? 'uninstall.ps1' : 'install.ps1');
    const powershellArgs = [
      '-NoLogo',
      '-NoProfile',
      '-ExecutionPolicy', 'Bypass',
      '-File', script,
      '-Browser', browser,
    ];
    if (action === 'install') {
      powershellArgs.push('-ExtensionPath', process.cwd());
      if (extensionIds.length) powershellArgs.push('-ExtensionId', ...extensionIds);
    }
    if (removeSavedCredentials) powershellArgs.push('-RemoveSavedCredentials');

    const result = spawnSync('powershell.exe', powershellArgs, { stdio: 'inherit' });
    if (result.error) {
      fail(`Could not start PowerShell: ${result.error.message}`);
    } else if (typeof result.status === 'number') {
      process.exitCode = result.status;
    } else {
      fail(`The helper ${action} command did not finish.`);
    }
  }
}
