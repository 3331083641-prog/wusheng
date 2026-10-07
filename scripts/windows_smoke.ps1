param([string]$Python = 'python', [int]$Port = 8019)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
foreach ($name in @('setup.ps1','start.ps1','start_lan.ps1','test_ui.ps1')) {
    $tokens = $null; $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $name), [ref]$tokens, [ref]$parseErrors) | Out-Null
    if ($parseErrors.Count) { throw "PowerShell syntax error: $name" }
}
if (@(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).Count) { throw "Port $Port occupied" }
$TestRoot = Join-Path $ProjectRoot ('tmp\windows-smoke-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $TestRoot -Force | Out-Null
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
