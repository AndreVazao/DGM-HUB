param(
    [string]$Repo = "C:\ProgramasGodMode\DGM-HUB"
)

Set-Location $Repo

Write-Host ""
Write-Host "================================="
Write-Host "DGM-HUB LOCAL VALIDATION"
Write-Host "================================="
Write-Host ""

function Run-Step {

    param(
        [string]$Name,
        [string]$Cmd
    )

    Write-Host ""
    Write-Host ">>> $Name"
    Write-Host ""

    cmd /c $Cmd

    Write-Host ""
    Write-Host "--------------------------"
}

New-Item runtime\reports -ItemType Directory -Force | Out-Null

$report = "runtime\reports\session_$(Get-Date -Format yyyyMMdd_HHmmss).log"

Start-Transcript -Path $report

Run-Step "PYTHON VERSION" "py --version"

Run-Step "GIT STATUS" "git status"

Run-Step "UNIT TESTS" "py -m pytest -q"

Run-Step "INTEGRATION TESTS" "py -m pytest tests\integration -v"

Run-Step "CHAOS TESTS" "py -m pytest tests\chaos -v"

if (Test-Path benchmarks\run_benchmarks.py)
{
    Run-Step "BENCHMARKS" "py benchmarks\run_benchmarks.py"
}

if (Test-Path tests\real_world\run_validation.py)
{
    Run-Step "REAL VALIDATION" "py tests\real_world\run_validation.py"
}

Run-Step "FINAL STATUS" "git status"

Stop-Transcript

Write-Host ""
Write-Host "LOG:"
Write-Host $report
Write-Host ""
