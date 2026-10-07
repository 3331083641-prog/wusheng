param([string]$Python = 'python', [int]$Port = 8019)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
foreach ($name in @('setup.ps1','start.ps1','start_dev.ps1','start_lan.ps1','test_ui.ps1','launch.ps1')) {
    $tokens = $null; $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $name), [ref]$tokens, [ref]$parseErrors) | Out-Null
    if ($parseErrors.Count) { throw "PowerShell syntax error: $name" }
}
if (@(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).Count) { throw "Port $Port occupied" }
$TestRoot = Join-Path $ProjectRoot ('tmp\windows-smoke-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $TestRoot -Force | Out-Null
# Check CMD expansion from another working directory and a Chinese/space path.
$EntryRoot = Join-Path $TestRoot '中文 启动路径'
New-Item -ItemType Directory -Path (Join-Path $EntryRoot 'scripts') -Force | Out-Null
foreach ($name in @('start-wusheng.cmd','启动物生.cmd')) { Copy-Item -LiteralPath (Join-Path $ProjectRoot $name) -Destination $EntryRoot }
foreach ($name in @('launch.ps1','setup.ps1','start.ps1')) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $EntryRoot 'scripts') }
Push-Location $TestRoot
try {
    foreach ($Entry in @((Join-Path $ProjectRoot 'start-wusheng.cmd'), (Join-Path $EntryRoot '启动物生.cmd'))) {
        $Output = & $Entry -CheckOnly
        if ($LASTEXITCODE -ne 0 -or -not ($Output -match [regex]::Escape((Split-Path -Parent $Entry)))) { throw 'CMD project path smoke failed' }
        $Output | Write-Host
    }
} finally { Pop-Location }
Write-Host 'CMD wrappers: arbitrary working directory + Chinese/space path: PASS'
$env:WUSHENG_DATA_DIR = Join-Path $TestRoot 'data'
Remove-Item Env:WUSHENG_DB_URL -ErrorAction SilentlyContinue
$env:WUSHENG_AI_PROVIDER = 'evidence'; $env:PYTHONUTF8 = '1'
$executable = (Get-Command $Python -ErrorAction Stop).Source
$server = Start-Process -FilePath $executable -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port',"$Port",'--no-proxy-headers') -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $TestRoot 'stdout.log') -RedirectStandardError (Join-Path $TestRoot 'stderr.log')
try {
    $health = $null
    for ($n=0; $n -lt 90; $n++) {
        Start-Sleep -Milliseconds 500
        try { $health = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 2; break } catch {}
    }
    if ($health.status -ne 'ok' -or $health.database -ne 'SQLite') { throw 'Health smoke failed' }
    $items = Invoke-RestMethod "http://127.0.0.1:$Port/items"
    if ($items.Count -ne 10) { throw 'Demo seed smoke failed' }
    Write-Host 'PowerShell syntax + FastAPI health + 10-item Demo: PASS'
} finally { Stop-Process -Id $server.Id -ErrorAction SilentlyContinue }
# Exercise the same production startup used by ordinary Windows users, then stop its own server.
& (Join-Path $PSScriptRoot 'start.ps1') -NoBrowser -Smoke -Python $executable -Port $Port
if ($LASTEXITCODE -ne 0) { throw 'Normal production startup smoke failed' }
Write-Host 'Normal startup: single port + lan-ready + production SPA + generate: PASS'
