$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$DgmRoot = $env:DGM_MAT_ROOT
if ([string]::IsNullOrWhiteSpace($DgmRoot)) { $DgmRoot = 'C:\ProgramasGodMode\DGM-MAT' }
$Port = 8770
$LogDir = Join-Path $Root 'runtime\multichat\logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-LocalUrl([string]$Url) {
    try { Invoke-RestMethod -Uri $Url -TimeoutSec 2 | Out-Null; return $true }
    catch { return $false }
}

$Python = (Get-Command python -ErrorAction Stop).Source

# DGM-MAT remains a non-authoritative observer. Start only if it is not already healthy.
if (-not (Test-LocalUrl 'http://127.0.0.1:8181/health')) {
    $Main = Join-Path $DgmRoot 'main.py'
    if (Test-Path $Main) {
        Start-Process -FilePath $Python -ArgumentList @($Main, '--headless') -WorkingDirectory $DgmRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'dgm-mat.stdout.log') -RedirectStandardError (Join-Path $LogDir 'dgm-mat.stderr.log') | Out-Null
        for ($i=0; $i -lt 20; $i++) {
            Start-Sleep -Milliseconds 500
            if (Test-LocalUrl 'http://127.0.0.1:8181/health') { break }
        }
    }
}

# Never start Ollama or FCC automatically. They are controlled by their own Hub buttons.
if (-not (Test-LocalUrl "http://127.0.0.1:$Port/api/health")) {
    Start-Process -FilePath $Python -ArgumentList @('-m','uvicorn','run_multichat:app','--host','127.0.0.1','--port',[string]$Port) -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'hub.stdout.log') -RedirectStandardError (Join-Path $LogDir 'hub.stderr.log') | Out-Null
    $Ready = $false
    for ($i=0; $i -lt 24; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-LocalUrl "http://127.0.0.1:$Port/api/health") { $Ready = $true; break }
    }
    if (-not $Ready) {
        Start-Process notepad.exe (Join-Path $LogDir 'hub.stderr.log')
        throw 'O DGM-HUB não iniciou. Abri o registo de erros.'
    }
}
Start-Process "http://127.0.0.1:$Port"
