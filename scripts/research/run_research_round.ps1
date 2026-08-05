# Run one research round (invoked by Windows Task Scheduler every 30 minutes)
$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$Root = Split-Path (Split-Path $ScriptDir -Parent) -Parent
Set-Location $Root

$Python = "C:\Python314\python.exe"
$Script = Join-Path $ScriptDir "run_research_round.py"
$LogDir = Join-Path $Root "research\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $LogDir "scheduler-$Stamp.log"

function Write-Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Output $line
}

try {
    Write-Log "START cwd=$Root"
    if (-not (Test-Path $Python)) { throw "Python not found: $Python" }
    if (-not (Test-Path $Script)) { throw "Script not found: $Script" }
    $output = & $Python $Script 2>&1
    $output | ForEach-Object { Write-Log $_ }
    Write-Log "END exit=$LASTEXITCODE"
    exit $LASTEXITCODE
}
catch {
    Write-Log "ERROR $($_.Exception.Message)"
    exit 1
}
