$ErrorActionPreference = 'Stop'

$sourcePath = Join-Path $PSScriptRoot 'CourseraToolsNativeHost.cs'
$binaryDirectory = Join-Path $PSScriptRoot 'bin'
$binaryPath = Join-Path $binaryDirectory 'CourseraToolsNativeHost.exe'
$compilerCandidates = @(
    (Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'),
    (Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe')
)
$compiler = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1

if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw "Native host source was not found: $sourcePath"
}
if (-not $compiler) {
    throw 'The .NET Framework C# compiler was not found.'
}

New-Item -ItemType Directory -Path $binaryDirectory -Force | Out-Null
$compilerArguments = @(
    '/nologo',
    '/target:exe',
    "/out:$binaryPath",
    '/reference:System.Web.Extensions.dll',
    '/reference:System.Security.dll',
    $sourcePath
)
& $compiler @compilerArguments
if ($LASTEXITCODE -ne 0) {
    throw "Native host compilation failed with exit code $LASTEXITCODE."
}

Write-Output "Native host built: $binaryPath"
