# 建桌面入口.ps1  --  generate desktop shortcuts from 入口清单.json
#
# ASCII only on purpose: this script must survive any console codepage.
# All Chinese text (shortcut names, notes) comes from 入口清单.json, read as UTF-8.
#
# Usage: right-click -> Run with PowerShell, or double-click 建桌面入口.bat

$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifest = Join-Path $here '入口清单.json'
if (-not (Test-Path -LiteralPath $manifest)) {
    Write-Host "[FAIL] manifest not found: $manifest" -ForegroundColor Red
    exit 1
}

$json = Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
$desktop = [Environment]::GetFolderPath('Desktop')
$dest = Join-Path $desktop $json.folderName

New-Item -ItemType Directory -Path $dest -Force | Out-Null

$shell = New-Object -ComObject WScript.Shell
$made = 0
$missing = @()

foreach ($e in $json.items) {
    if (-not (Test-Path -LiteralPath $e.target)) {
        $missing += $e.target
        continue
    }
    $lnkPath = Join-Path $dest ($e.name + '.lnk')
    $sc = $shell.CreateShortcut($lnkPath)
    $sc.TargetPath = $e.target
    $sc.WorkingDirectory = Split-Path -Parent $e.target
    $sc.Description = $e.note
    $sc.WindowStyle = 1   # normal window: these scripts pause and show output
    $sc.Save()
    $made++
}

# 说明书 copy alongside
$doc = Join-Path $here '说明.html'
if (Test-Path -LiteralPath $doc) {
    Copy-Item -LiteralPath $doc -Destination (Join-Path $dest '说明.html') -Force
}

Write-Host ""
Write-Host ("  shortcuts created : " + $made) -ForegroundColor Green
Write-Host ("  desktop folder    : " + $dest)
if ($missing.Count -gt 0) {
    Write-Host ("  MISSING targets   : " + $missing.Count) -ForegroundColor Yellow
    foreach ($m in $missing) { Write-Host ("    - " + $m) -ForegroundColor Yellow }
}
Write-Host ""
