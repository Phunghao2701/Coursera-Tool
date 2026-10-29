#!/usr/bin/env node
'use strict';

const path = require('node:path');
const { spawnSync } = require('node:child_process');

function fail(message) {
  console.error(message);
  process.exitCode = 1;
}

if (process.platform !== 'win32') {
  fail('The Coursera Tools native helper installer currently supports Windows only.');
} else {
  let browser = 'Edge';
  const extensionIds = [];
  const args = process.argv.slice(2);

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
    } else if (arg === '--help' || arg === '-h') {
      console.log('Usage: npx --yes --package=./native-host -- coursera-tools-chatgpt-helper [--browser Edge|Chrome|Both] [--extension-id ID]');
      process.exit(0);
    } else {
      fail(`Unknown option: ${arg}`);
      break;
    }
  }

  if (!process.exitCode && !['Edge', 'Chrome', 'Both'].includes(browser)) {
    fail('Choose Edge, Chrome, or Both with --browser.');
  }

  if (!process.exitCode) {
    const installer = path.join(__dirname, 'install.ps1');
    const powershellArgs = [
      '-NoLogo',
      '-NoProfile',
      '-ExecutionPolicy', 'Bypass',
      '-File', installer,
      '-Browser', browser,
      '-ExtensionPath', process.cwd(),
    ];
    if (extensionIds.length) powershellArgs.push('-ExtensionId', ...extensionIds);

    const result = spawnSync('powershell.exe', powershellArgs, { stdio: 'inherit' });
    if (result.error) {
      fail(`Could not start PowerShell: ${result.error.message}`);
    } else if (typeof result.status === 'number') {
      process.exitCode = result.status;
    } else {
      fail('The helper installer did not finish.');
    }
  }
}
