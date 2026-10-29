param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-p]{32}$')]
    [string]$ExtensionId,

    [ValidateSet('Edge', 'Chrome', 'Both')]
    [string]$Browser = 'Edge'
)

$ErrorActionPreference = 'Stop'
$hostName = 'com.coursera.tools.chatgpt'
$sourcePath = Join-Path $PSScriptRoot 'CourseraToolsNativeHost.cs'
$appRoot = Join-Path $env:LOCALAPPDATA 'CourseraTools'
$hostDirectory = Join-Path $appRoot 'NativeHost'
$hostPath = Join-Path $hostDirectory 'CourseraToolsNativeHost.exe'
$manifestPath = Join-Path $hostDirectory ($hostName + '.json')

if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw "Native host source was not found: $sourcePath"
}

$compilerCandidates = @(
    (Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'),
    (Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe')
)
$compiler = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $compiler) {
    throw 'The .NET Framework C# compiler was not found. Install the .NET Framework 4.x developer tools and run this installer again.'
}

New-Item -ItemType Directory -Path $hostDirectory -Force | Out-Null
$compilerArguments = @(
    '/nologo',
    '/target:exe',
    "/out:$hostPath",
    '/reference:System.Web.Extensions.dll',
    '/reference:System.Security.dll',
    $sourcePath
)
& $compiler @compilerArguments
if ($LASTEXITCODE -ne 0) {
    throw "Native host compilation failed with exit code $LASTEXITCODE."
}

$nativeManifest = [ordered]@{
    name = $hostName
    description = 'Local ChatGPT connection for Coursera Tools'
    path = $hostPath
    type = 'stdio'
    allowed_origins = @("chrome-extension://$ExtensionId/")
}
$manifestJson = $nativeManifest | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText($manifestPath, $manifestJson, [System.Text.UTF8Encoding]::new($false))

$registryPaths = @()
if ($Browser -eq 'Edge' -or $Browser -eq 'Both') {
    $registryPaths += "Software\Microsoft\Edge\NativeMessagingHosts\$hostName"
}
if ($Browser -eq 'Chrome' -or $Browser -eq 'Both') {
    $registryPaths += "Software\Google\Chrome\NativeMessagingHosts\$hostName"
}

foreach ($registryPath in $registryPaths) {
    $key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey($registryPath)
    if (-not $key) {
        throw "Could not create the native messaging registry entry: HKCU\$registryPath"
    }
    try {
        $key.SetValue('', $manifestPath, [Microsoft.Win32.RegistryValueKind]::String)
    }
    finally {
        $key.Dispose()
    }
}

Write-Output "Coursera Tools ChatGPT helper installed for $Browser."
Write-Output "Reload the extension in the browser, then choose Continue with ChatGPT in its popup."
