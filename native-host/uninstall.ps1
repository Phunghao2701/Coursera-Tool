param(
    [ValidateSet('Edge', 'Chrome', 'Both')]
    [string]$Browser = 'Both',

    [switch]$RemoveSavedCredentials
)

$ErrorActionPreference = 'Stop'
$hostName = 'com.coursera.tools.chatgpt'
$appRoot = Join-Path $env:LOCALAPPDATA 'CourseraTools'
$hostDirectory = Join-Path $appRoot 'NativeHost'
$hostExecutable = Join-Path $hostDirectory 'CourseraToolsNativeHost.exe'

$registryPaths = @()
if ($Browser -eq 'Edge' -or $Browser -eq 'Both') {
    $registryPaths += "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\$hostName"
}
if ($Browser -eq 'Chrome' -or $Browser -eq 'Both') {
    $registryPaths += "HKCU:\Software\Google\Chrome\NativeMessagingHosts\$hostName"
}

foreach ($registryPath in $registryPaths) {
    if (Test-Path -LiteralPath $registryPath) {
        Remove-Item -LiteralPath $registryPath -Recurse -Force
    }
}

$allRegistryPaths = @(
    "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\$hostName",
    "HKCU:\Software\Google\Chrome\NativeMessagingHosts\$hostName"
)
$remainingRegistrations = @($allRegistryPaths | Where-Object { Test-Path -LiteralPath $_ })

if ($remainingRegistrations.Count -eq 0 -and (Test-Path -LiteralPath $hostDirectory)) {
    if (Test-Path -LiteralPath $hostExecutable -PathType Leaf) {
        $normalizedHostExecutable = [System.IO.Path]::GetFullPath($hostExecutable)
        $runningHosts = @(Get-CimInstance -ClassName Win32_Process -Filter "Name='CourseraToolsNativeHost.exe'" -ErrorAction SilentlyContinue | Where-Object {
            $_.ExecutablePath -and [System.String]::Equals(
                [System.IO.Path]::GetFullPath($_.ExecutablePath),
                $normalizedHostExecutable,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        })

        foreach ($runningHost in $runningHosts) {
            try {
                Stop-Process -Id $runningHost.ProcessId -Force -ErrorAction Stop
                Wait-Process -Id $runningHost.ProcessId -Timeout 5 -ErrorAction SilentlyContinue
            }
            catch {
                throw "Could not stop the Coursera Tools helper process. Close Edge and Chrome, then retry. $($_.Exception.Message)"
            }
        }
    }

    try {
        Remove-Item -LiteralPath $hostDirectory -Recurse -Force -ErrorAction Stop
    }
    catch {
        throw "Could not remove the native helper files. Close Edge and Chrome, then run the uninstall command again. $($_.Exception.Message)"
    }
} elseif ($remainingRegistrations.Count -gt 0) {
    Write-Output 'Helper files were kept because another browser is still registered.'
}

if ($RemoveSavedCredentials) {
    $credentialPath = Join-Path $appRoot 'chatgpt-credentials.bin'
    if (Test-Path -LiteralPath $credentialPath) {
        Remove-Item -LiteralPath $credentialPath -Force
    }
}

Write-Output "Coursera Tools ChatGPT helper removed for $Browser."
if (-not $RemoveSavedCredentials) {
    Write-Output 'Saved ChatGPT credentials were kept. Pass -RemoveSavedCredentials to remove them too.'
}
