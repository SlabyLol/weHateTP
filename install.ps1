#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "  TypeBot · weHateTP  installer" -ForegroundColor Red
Write-Host "  By DarkFox" -ForegroundColor DarkGray
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

function Test-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Ensure-Python {
    if (Test-Command "python") {
        $ver = & python --version 2>&1
        Write-Host "[OK] Python found: $ver" -ForegroundColor Green
        return
    }
    if (Test-Command "py") {
        $ver = & py --version 2>&1
        Write-Host "[OK] Python found via py launcher: $ver" -ForegroundColor Green
        return
    }

    Write-Host "[..] Python not found – installing..." -ForegroundColor Yellow

    if (Test-Command "winget") {
        Write-Host "[..] Installing Python 3.12 via winget..." -ForegroundColor Cyan
        winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        if (Test-Command "python") {
            Write-Host "[OK] Python installed via winget" -ForegroundColor Green
            return
        }
    }

    if (Test-Command "choco") {
        Write-Host "[..] Installing Python via Chocolatey..." -ForegroundColor Cyan
        choco install python -y
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        if (Test-Command "python") {
            Write-Host "[OK] Python installed via Chocolatey" -ForegroundColor Green
            return
        }
    }

    Write-Host "[!!] Could not install Python automatically." -ForegroundColor Red
    Write-Host "     Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "     Enable 'Add python.exe to PATH' during setup, then re-run this script." -ForegroundColor Yellow
    exit 1
}

function Get-PythonExe {
    if (Test-Command "python") { return "python" }
    if (Test-Command "py") { return "py" }
    throw "Python executable not found"
}

Ensure-Python
$py = Get-PythonExe

Write-Host ""
Write-Host "[..] Upgrading pip, setuptools, wheel..." -ForegroundColor Cyan
& $py -m pip install --upgrade pip setuptools wheel

Write-Host ""
Write-Host "[..] Installing PyYAML..." -ForegroundColor Cyan
& $py -m pip install "PyYAML>=6.0"

Write-Host ""
Write-Host "[..] Installing weHateTP from GitHub..." -ForegroundColor Cyan
& $py -m pip install --upgrade "git+https://github.com/SlabyLol/weHateTP.git"

Write-Host ""
Write-Host "[..] Verifying install..." -ForegroundColor Cyan
$ver = & $py -c "import weHateTP; print(weHateTP.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!!] Import failed: $ver" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] weHateTP $ver imported" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Install complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  weHateTP start" -ForegroundColor White
Write-Host "  weHateTP inject" -ForegroundColor White
Write-Host "  weHateTP type `"Hello`"" -ForegroundColor White
Write-Host "  weHateTP warn" -ForegroundColor White
Write-Host "  weHateTP connect" -ForegroundColor White
Write-Host ""
Write-Host "If 'weHateTP' is not found in PATH, use:" -ForegroundColor DarkGray
Write-Host "  python -m weHateTP.cli start" -ForegroundColor DarkGray
Write-Host ""
