$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = if ($env:WUSHENG_PYTHON) { $env:WUSHENG_PYTHON } else { Join-Path $ProjectRoot '.venv\Scripts\python.exe' }
$FrontendRoot = Join-Path $ProjectRoot 'frontend'
$TestId = [guid]::NewGuid().ToString('N')
$TestRoot = Join-Path $ProjectRoot "tmp\wusheng-ui-test-$TestId"
if (-not (Test-Path -LiteralPath $Python)) { throw '请先运行 scripts/setup.ps1。' }
foreach ($port in @(8002,5175)) {
    if (@(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).Count -gt 0) {
        throw "测试端口 $port 已被占用；没有停止或修改现有服务。"
    }
}
New-Item -ItemType Directory -Force -Path $TestRoot | Out-Null
$LogRoot = Join-Path $TestRoot 'logs'
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$env:WUSHENG_DATA_DIR = Join-Path $TestRoot 'data'
$env:WUSHENG_TEST_DATA_DIR = $env:WUSHENG_DATA_DIR
$env:WUSHENG_TEST_API_URL = 'http://127.0.0.1:8002'
$env:WUSHENG_TEST_BASE_URL = 'http://127.0.0.1:5175'
$env:WUSHENG_API_TARGET = $env:WUSHENG_TEST_API_URL
$env:WUSHENG_AI_PROVIDER = 'evidence'
$env:WUSHENG_VITE_PORT = '5175'
$env:WUSHENG_PLAYWRIGHT_OUTPUT_DIR = Join-Path $TestRoot 'playwright'
$env:PYTHONUTF8 = '1'
$BackendProcess = $null
$FrontendProcess = $null
$Passed = $false

function Stop-OwnedProcessTree([int]$RootProcessId) {
    $OwnedChildren = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $RootProcessId" -ErrorAction SilentlyContinue)
    foreach ($OwnedChild in $OwnedChildren) { Stop-OwnedProcessTree -RootProcessId $OwnedChild.ProcessId }
    Stop-Process -Id $RootProcessId -ErrorAction SilentlyContinue
}

try {
    # Same verification order as the normal launch: health, generate, dev server, browser tests.
    $BackendProcess = Start-Process -FilePath $Python -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8002','--log-level','warning') -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $LogRoot 'backend.stdout.log') -RedirectStandardError (Join-Path $LogRoot 'backend.stderr.log')
    $Health = $null
    for ($Attempt = 0; $Attempt -lt 90; $Attempt++) {
        Start-Sleep -Milliseconds 500
        try { $Health = Invoke-RestMethod 'http://127.0.0.1:8002/health' -TimeoutSec 2; break } catch {}
    }
    if ($Health.status -ne 'ok' -or $Health.database -ne 'SQLite') { throw '隔离测试后端 /health 检查失败。' }
    $Items = Invoke-RestMethod 'http://127.0.0.1:8002/items'
    if ($Items.Count -lt 10) { throw '隔离数据库未生成 10 件合成 Demo 物品。' }
    $Question = @{ itemId = $Items[0].id; question = '保修信息是什么？' } | ConvertTo-Json
    $Answer = Invoke-RestMethod 'http://127.0.0.1:8002/generate' -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($Question))
    if (-not $Answer.answer) { throw '隔离测试后端 /generate 检查失败。' }

    $NpmCommand = (Get-Command npm.cmd -ErrorAction Stop).Source
    $NpmCli = Join-Path (Split-Path -Parent $NpmCommand) 'node_modules\npm\bin\npm-cli.js'
    if (-not (Test-Path -LiteralPath $NpmCli)) { throw '找不到 npm-cli.js。' }
    $Node = (Get-Command node.exe -ErrorAction Stop).Source
    $NpmCliArgument = '"' + $NpmCli + '"'
    $NpmArguments = @($NpmCliArgument,'run','dev','--','--host','127.0.0.1','--strictPort','--port','5175')
    $FrontendProcess = Start-Process -FilePath $Node -ArgumentList $NpmArguments -WorkingDirectory $FrontendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $LogRoot 'frontend.stdout.log') -RedirectStandardError (Join-Path $LogRoot 'frontend.stderr.log')
    $Ready = $false
    for ($Attempt = 0; $Attempt -lt 60; $Attempt++) {
        Start-Sleep -Milliseconds 500
        try {
            $Page = Invoke-WebRequest 'http://127.0.0.1:5175' -UseBasicParsing -TimeoutSec 2
            if ($Page.Content -match 'id="root"') { $Ready = $true; break }
        } catch {}
    }
    if (-not $Ready) { throw '隔离测试前端未能启动。' }

    Push-Location $FrontendRoot
    try {
        npm.cmd test
        if ($LASTEXITCODE -ne 0) { throw "Playwright 测试失败，退出码 $LASTEXITCODE。" }
    } finally { Pop-Location }
    & node (Join-Path $ProjectRoot 'scripts\verify_item_images.mjs')
    if ($LASTEXITCODE -ne 0) { throw '高清物品图片验收失败。' }
    & node (Join-Path $ProjectRoot 'scripts\verify_consumable_images.mjs')
    if ($LASTEXITCODE -ne 0) { throw '高清耗材图片验收失败。' }
    & $Python (Join-Path $ProjectRoot 'scripts\summarize_ui.py') (Join-Path $env:WUSHENG_PLAYWRIGHT_OUTPUT_DIR 'ui-test-results.json')
    if ($LASTEXITCODE -ne 0) { throw 'UI 证据摘要生成失败。' }
    $Passed = $true
} finally {
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) { Stop-OwnedProcessTree -RootProcessId $FrontendProcess.Id }
    if ($BackendProcess -and -not $BackendProcess.HasExited) { Stop-OwnedProcessTree -RootProcessId $BackendProcess.Id }
    if ($Passed) {
        $ResolvedRoot = (Resolve-Path -LiteralPath $TestRoot).Path
        $ExpectedPrefix = (Join-Path $ProjectRoot 'tmp\wusheng-ui-test-')
        if (-not $ResolvedRoot.StartsWith($ExpectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw '测试数据目录校验失败，拒绝自动删除。' }
        Remove-Item -LiteralPath $ResolvedRoot -Recurse -Force
        Write-Host 'UI 测试通过；仅本次生成的隔离数据库和日志已清理。'
    } else {
        Write-Warning "测试未通过，隔离数据和日志保留供排查：$TestRoot"
    }
}
