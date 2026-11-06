$ErrorActionPreference = 'Stop'
$CanonicalLauncher = Join-Path $PSScriptRoot 'scripts\Start-DGM-HUB.ps1'
if (-not (Test-Path $CanonicalLauncher)) {
    throw "O launcher canónico do DGM-HUB não foi encontrado: $CanonicalLauncher"
}
& $CanonicalLauncher
