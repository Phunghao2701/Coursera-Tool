param(
    [ValidateSet('Edge', 'Chrome', 'Both')]
    [string]$Browser = 'Edge',

    [switch]$RemoveSavedCredentials
)

$ErrorActionPreference = 'Stop'
$hostName = 'com.coursera.tools.chatgpt'
$appRoot = Join-Path $env:LOCALAPPDATA 'CourseraTools'
$hostDirectory = Join-Path $appRoot 'NativeHost'

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

if (Test-Path -LiteralPath $hostDirectory) {
    Remove-Item -LiteralPath $hostDirectory -Recurse -Force
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
