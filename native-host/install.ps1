param(
    [string[]]$ExtensionId = @(),

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
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')

if (-not $ExtensionId -or $ExtensionId.Count -eq 0) {
    $profileRoots = @()
    if ($Browser -eq 'Edge' -or $Browser -eq 'Both') {
        $profileRoots += [pscustomobject]@{
            Browser = 'Edge'
            Path = Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\User Data'
        }
    }
    if ($Browser -eq 'Chrome' -or $Browser -eq 'Both') {
        $profileRoots += [pscustomobject]@{
            Browser = 'Chrome'
            Path = Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data'
        }
    }

    $detectedExtensions = @()
    foreach ($profileRoot in $profileRoots) {
        if (-not (Test-Path -LiteralPath $profileRoot.Path -PathType Container)) { continue }
        $profiles = Get-ChildItem -LiteralPath $profileRoot.Path -Directory -ErrorAction SilentlyContinue
        foreach ($profile in $profiles) {
            $preferencesPath = Join-Path $profile.FullName 'Preferences'
            if (-not (Test-Path -LiteralPath $preferencesPath -PathType Leaf)) { continue }

            try {
                $preferences = Get-Content -LiteralPath $preferencesPath -Raw | ConvertFrom-Json
                $settings = $preferences.extensions.settings
                if ($null -eq $settings) { continue }
                foreach ($entry in $settings.PSObject.Properties) {
                    if ($entry.Name -notmatch '^[a-p]{32}$') { continue }
                    $name = [string]$entry.Value.manifest.name
                    $extensionPath = [string]$entry.Value.path
                    $sameFolder = $false
                    if ($extensionPath) {
                        try {
                            $sameFolder = [System.String]::Equals(([System.IO.Path]::GetFullPath($extensionPath).TrimEnd('\')), $repoRoot, [System.StringComparison]::OrdinalIgnoreCase)
                        }
                        catch { }
                    }
                    if (-not $sameFolder -and $name -notin @('Coursera Tools', 'Coursera Automation Extension')) { continue }
                    $detectedExtensions += [pscustomobject]@{
                        ExtensionId = $entry.Name
                        Browser = $profileRoot.Browser
                        Profile = $profile.Name
                        Path = $extensionPath
                    }
                }
            }
            catch {
                # Ignore profiles with unreadable or malformed preferences.
            }
        }
    }

    $sameFolderExtensions = @($detectedExtensions | Where-Object { $_.Path -and [System.String]::Equals($_.Path.TrimEnd('\'), $repoRoot, [System.StringComparison]::OrdinalIgnoreCase) })
    $candidates = if ($sameFolderExtensions.Count -gt 0) { $sameFolderExtensions } else { $detectedExtensions }
    $detectedIds = @($candidates.ExtensionId | Sort-Object -Unique)

    if ($detectedIds.Count -eq 1) {
        $ExtensionId = $detectedIds
        Write-Output "Detected Coursera Tools extension ID in $($candidates[0].Browser), profile $($candidates[0].Profile)."
    }
    else {
        if ($detectedIds.Count -gt 1) {
            Write-Output 'Multiple Coursera Tools installations were found:'
            $candidates | Select-Object Browser, Profile, ExtensionId | Format-Table -AutoSize | Out-Host
        }
        else {
            Write-Output 'Coursera Tools was not found in the selected browser profile.'
        }
        $enteredIds = Read-Host 'Enter the extension ID shown at edge://extensions or chrome://extensions'
        $ExtensionId = @($enteredIds -split '[,;\s]+' | Where-Object { $_ })
    }
}

$ExtensionId = @($ExtensionId | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ } | Sort-Object -Unique)
if ($ExtensionId.Count -eq 0 -or @($ExtensionId | Where-Object { $_ -notmatch '^[a-p]{32}$' }).Count -gt 0) {
    throw 'Enter one or more valid 32-character extension IDs containing letters a through p.'
}

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
    allowed_origins = @($ExtensionId | ForEach-Object { "chrome-extension://$_/" })
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
Write-Output "The browser will start the helper automatically when needed. Reload the extension, then choose Continue with ChatGPT."
