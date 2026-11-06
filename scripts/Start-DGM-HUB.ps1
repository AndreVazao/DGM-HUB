$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$DgmRoot = if ($env:DGM_MAT_ROOT) { $env:DGM_MAT_ROOT } else { 'C:\ProgramasGodMode\DGM-MAT' }
$Port = if ($env:DGM_HUB_PORT) { [int]$env:DGM_HUB_PORT } else { 8771 }
$LogDir = Join-Path $Root 'runtime\multichat\logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-LocalUrl([string]$Url) {
    try {
        Invoke-RestMethod -Uri $Url -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Test-PortListener([int]$LocalPort) {
    try {
        return [bool](Get-NetTCPConnection -State Listen -LocalPort $LocalPort -ErrorAction Stop)
    } catch {
        return $false
    }
}

function Get-PythonCommand {
    if ($env:DGM_PYTHON_EXECUTABLE -and (Test-Path $env:DGM_PYTHON_EXECUTABLE)) {
        $candidate = @{ FilePath = $env:DGM_PYTHON_EXECUTABLE; PrefixArgs = @() }
    } else {
        $python = Get-Command python.exe -ErrorAction SilentlyContinue
        if ($python) {
            $candidate = @{ FilePath = $python.Source; PrefixArgs = @() }
        } else {
            $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
            if (-not $launcher) { throw 'Python 3.12 não foi encontrado. Instala Python 3.12 ou define DGM_PYTHON_EXECUTABLE.' }
            $candidate = @{ FilePath = $launcher.Source; PrefixArgs = @('-3.12') }
        }
    }
    $probeArgs = @($candidate.PrefixArgs) + @('-c', 'import fastapi, uvicorn')
    & $candidate.FilePath @probeArgs 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'O Python selecionado não tem FastAPI e Uvicorn instalados. Não foram instaladas dependências automaticamente.' }
    return $candidate
}

function Start-DgmMat {
    $health = 'http://127.0.0.1:8181/health'
    if (Test-LocalUrl $health) { Write-Host 'DGM-MAT já está saudável.'; return }
    $ExistingRuntime = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        ($_.Name -ieq 'DGM-MAT.exe' -and $_.CommandLine -match '--headless') -or
        ($_.Name -match '^pythonw?\.exe$' -and $_.CommandLine -match 'main\.py' -and $_.CommandLine -match '--headless' -and $_.CommandLine -match [regex]::Escape($DgmRoot))
    })
    if ($ExistingRuntime.Count -gt 0) {
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Milliseconds 500
            if (Test-LocalUrl $health) { Write-Host "DGM-MAT já estava em arranque (PID $($ExistingRuntime[0].ProcessId)) e ficou saudável."; return }
        }
        throw "Já existe um processo DGM-MAT (PID $($ExistingRuntime[0].ProcessId)), mas ainda não está saudável. Não iniciei uma segunda instância."
    }
    if (Test-PortListener 8181) { throw 'A porta 8181 está ocupada mas o DGM-MAT não responde ao health check. Não vou iniciar uma segunda instância.' }

    $exe = Join-Path $DgmRoot 'installed\DGM-MAT.exe'
    if (Test-Path $exe) {
        Start-Process -FilePath $exe -ArgumentList @('--headless') -WorkingDirectory $DgmRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'dgm-mat.stdout.log') -RedirectStandardError (Join-Path $LogDir 'dgm-mat.stderr.log') | Out-Null
    } else {
        $main = Join-Path $DgmRoot 'main.py'
        if (-not (Test-Path $main)) { throw "DGM-MAT não encontrado em $DgmRoot." }
        $python = Get-PythonCommand
        Start-Process -FilePath $python.FilePath -ArgumentList (@($python.PrefixArgs) + @($main, '--headless')) -WorkingDirectory $DgmRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'dgm-mat.stdout.log') -RedirectStandardError (Join-Path $LogDir 'dgm-mat.stderr.log') | Out-Null
    }

    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-LocalUrl $health) { Write-Host 'DGM-MAT iniciado e saudável.'; return }
    }
    throw 'DGM-MAT não ficou saudável dentro de 30 segundos. Consulta os logs do backend.'
}

function Start-Hub {
    $health = "http://127.0.0.1:$Port/api/health/live"
    if (Test-LocalUrl $health) { Write-Host 'DGM-HUB já está saudável.'; return }
    if (Test-PortListener $Port) { throw "A porta $Port está ocupada mas o DGM-HUB não responde ao health check. Não vou iniciar uma segunda instância." }

    $python = Get-PythonCommand
    $arguments = @($python.PrefixArgs) + @('-m', 'uvicorn', 'run_multichat:app', '--host', '127.0.0.1', '--port', [string]$Port)
    Start-Process -FilePath $python.FilePath -ArgumentList $arguments -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'hub.stdout.log') -RedirectStandardError (Join-Path $LogDir 'hub.stderr.log') | Out-Null

    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-LocalUrl $health) { Write-Host 'DGM-HUB iniciado e saudável.'; return }
    }
    Start-Process notepad.exe (Join-Path $LogDir 'hub.stderr.log')
    throw 'DGM-HUB não iniciou dentro de 20 segundos. Abri o registo de erros.'
}

$StartupMutex = New-Object System.Threading.Mutex($false, "Local\DGM-HUB-Startup-$Port")
$StartupLock = $false
try {
    try { $StartupLock = $StartupMutex.WaitOne(0) }
    catch [System.Threading.AbandonedMutexException] { $StartupLock = $true }
    if (-not $StartupLock) { throw 'O arranque do DGM-HUB já está a ser executado por outra janela. Não iniciei serviços duplicados.' }
    Start-DgmMat
    Start-Hub
} finally {
    if ($StartupLock) { $StartupMutex.ReleaseMutex() }
    $StartupMutex.Dispose()
}
Start-Process "http://127.0.0.1:$Port"
