#Requires -Version 5.1
# weHateTP installer - school-PC friendly (no admin required)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Root = Join-Path $env:LOCALAPPDATA "weHateTP"
$PyDir = Join-Path $Root "python"
$ScriptsDir = Join-Path $Root "scripts"
$LogFile = Join-Path $Root "install.log"

function Write-Log($Msg, $Color = "White") {
    Write-Host $Msg -ForegroundColor $Color
    try {
        if (-not (Test-Path $Root)) { New-Item -ItemType Directory -Path $Root -Force | Out-Null }
        Add-Content -Path $LogFile -Value ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Msg)
    } catch {}
}

Write-Host ""
Write-Log "========================================" "Red"
Write-Log "  TypeBot · weHateTP  installer" "Red"
Write-Log "  School-PC mode · By DarkFox" "DarkGray"
Write-Log "========================================" "Red"
Write-Host ""

function Test-Cmd($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-PythonWorks($Exe) {
    try {
        $o = & $Exe -c "import sys; print(sys.version_info[0])" 2>$null
        return ($o -eq "3")
    } catch { return $false }
}

function Find-Python {
    $candidates = @()
    if (Test-Cmd "python") { $candidates += (Get-Command python).Source }
    if (Test-Cmd "py") {
        try {
            $py3 = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($py3) { $candidates += $py3.Trim() }
        } catch {}
    }
    $portable = Join-Path $PyDir "python.exe"
    if (Test-Path $portable) { $candidates += $portable }
    $localPaths = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe")
    )
    foreach ($p in $localPaths) {
        if (Test-Path $p) { $candidates += $p }
    }
    foreach ($c in $candidates) {
        if ($c -and (Test-PythonWorks $c)) { return $c }
    }
    return $null
}

function Install-PortablePython {
    Write-Log "[..] No system Python - installing portable Python (user folder, no admin)..." "Yellow"
    New-Item -ItemType Directory -Path $PyDir -Force | Out-Null
    $version = "3.12.7"
    $url = "https://www.python.org/ftp/python/$version/python-$version-embed-amd64.zip"
    $zip = Join-Path $Root "python-embed.zip"
    Write-Log "[..] Downloading Python $version embeddable..." "Cyan"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    } catch {
        Write-Log "[!!] Download failed: $_" "Red"
        Write-Log "     Download Python from python.org (user install) and re-run." "Yellow"
        exit 1
    }
    Write-Log "[..] Extracting..." "Cyan"
    if (Test-Path $PyDir) { Remove-Item $PyDir -Recurse -Force -ErrorAction SilentlyContinue }
    New-Item -ItemType Directory -Path $PyDir -Force | Out-Null
    Expand-Archive -Path $zip -DestinationPath $PyDir -Force
    Remove-Item $zip -Force -ErrorAction SilentlyContinue
    $pth = Get-ChildItem -Path $PyDir -Filter "python*._pth" | Select-Object -First 1
    if ($pth) {
        $content = Get-Content $pth.FullName
        $content = $content | ForEach-Object {
            if ($_ -match '^#\s*import site') { 'import site' } else { $_ }
        }
        if ($content -notcontains 'import site') { $content += 'import site' }
        Set-Content -Path $pth.FullName -Value $content
    }
    $getPip = Join-Path $PyDir "get-pip.py"
    Write-Log "[..] Installing pip into portable Python..." "Cyan"
    try {
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing
        & (Join-Path $PyDir "python.exe") $getPip --no-warn-script-location 2>&1 | Out-Null
    } catch {
        Write-Log "[!!] get-pip failed: $_" "Red"
        exit 1
    }
    $exe = Join-Path $PyDir "python.exe"
    if (-not (Test-PythonWorks $exe)) {
        Write-Log "[!!] Portable Python does not run." "Red"
        exit 1
    }
    Write-Log "[OK] Portable Python ready: $exe" "Green"
    return $exe
}

function Install-UserPythonWinget {
    if (-not (Test-Cmd "winget")) { return $null }
    Write-Log "[..] Trying winget user-scope Python..." "Cyan"
    try {
        winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        return (Find-Python)
    } catch { return $null }
}

New-Item -ItemType Directory -Path $Root -Force | Out-Null
New-Item -ItemType Directory -Path $ScriptsDir -Force | Out-Null

$python = Find-Python
if (-not $python) { $python = Install-UserPythonWinget }
if (-not $python) {
    $python = Install-PortablePython
} else {
    Write-Log "[OK] Python found: $python" "Green"
}

Write-Host ""
Write-Log "[..] Upgrading pip (user)..." "Cyan"
& $python -m pip install --upgrade pip setuptools wheel --user --no-warn-script-location 2>&1 | Out-Null

Write-Log "[..] Installing PyYAML..." "Cyan"
& $python -m pip install "PyYAML>=6.0" --user --no-warn-script-location

Write-Log "[..] Installing weHateTP from GitHub..." "Cyan"
$gitOk = $false
if (Test-Cmd "git") {
    try {
        & $python -m pip install --upgrade --user --no-warn-script-location "git+https://github.com/SlabyLol/weHateTP.git"
        if ($LASTEXITCODE -eq 0) { $gitOk = $true }
    } catch {}
}
if (-not $gitOk) {
    Write-Log "[..] git not available - downloading zip from GitHub..." "Yellow"
    $zipPkg = Join-Path $Root "weHateTP-src.zip"
    $srcDir = Join-Path $Root "src"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri "https://github.com/SlabyLol/weHateTP/archive/refs/heads/main.zip" -OutFile $zipPkg -UseBasicParsing
        if (Test-Path $srcDir) { Remove-Item $srcDir -Recurse -Force }
        Expand-Archive -Path $zipPkg -DestinationPath $srcDir -Force
        $proj = Get-ChildItem $srcDir -Directory | Select-Object -First 1
        & $python -m pip install --user --no-warn-script-location $proj.FullName
    } catch {
        Write-Log "[!!] Install from zip failed: $_" "Red"
        exit 1
    }
}

Write-Host ""
Write-Log "[..] Verifying..." "Cyan"
$ver = & $python -c "import weHateTP; print(weHateTP.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Log "[!!] Import failed: $ver" "Red"
    exit 1
}
Write-Log "[OK] weHateTP $ver" "Green"

$launcher = Join-Path $ScriptsDir "weHateTP.cmd"
@"
@echo off
"$python" -m weHateTP.cli %*
"@ | Set-Content -Path $launcher -Encoding ASCII

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$ScriptsDir*") {
    try {
        [Environment]::SetEnvironmentVariable("Path", "$ScriptsDir;$userPath", "User")
        $env:Path = "$ScriptsDir;$env:Path"
        Write-Log "[OK] Added launcher folder to user PATH" "Green"
    } catch {
        Write-Log "[..] Could not change user PATH (policy). Use full path below." "Yellow"
    }
}

Write-Host ""
Write-Log "========================================" "Green"
Write-Log "  Install complete (school-PC safe)" "Green"
Write-Log "========================================" "Green"
Write-Host ""
Write-Log "Run TypeBot:" "Cyan"
Write-Host "  $launcher start" -ForegroundColor White
Write-Host "  $python -m weHateTP.cli start" -ForegroundColor White
Write-Host ""
Write-Log "Files under: $Root" "DarkGray"
Write-Log "Open a NEW terminal if weHateTP is not found yet." "DarkGray"
Write-Host ""
