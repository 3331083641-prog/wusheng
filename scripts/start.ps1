param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$FrontendRoot = Join-Path $ProjectRoot 'frontend'
$LogRoot = Join-Path $ProjectRoot 'logs'
$BackendUrl = 'http://127.0.0.1:8000'
$FrontendUrl = 'http://127.0.0.1:5173'
if (-not (Test-Path -LiteralPath $Python)) { throw '请先运行 scripts/setup.ps1。' }
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$env:PYTHONUTF8 = '1'
$BackendProcess = $null
$FrontendProcess = $null

function Stop-OwnedProcessTree([int]$RootProcessId) {
    $OwnedChildren = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $RootProcessId" -ErrorAction SilentlyContinue)
    foreach ($OwnedChild in $OwnedChildren) { Stop-OwnedProcessTree -RootProcessId $OwnedChild.ProcessId }
    Stop-Process -Id $RootProcessId -ErrorAction SilentlyContinue
}

function Get-WushengHealth {
    try {
        $health = Invoke-RestMethod "$BackendUrl/health" -TimeoutSec 2
        $openapi = Invoke-RestMethod "$BackendUrl/openapi.json" -TimeoutSec 2
        if ($health.status -eq 'ok' -and $health.database -eq 'SQLite' -and $openapi.info.title -like '*Wusheng*') { return $health }
        throw '8000 端口上的服务不是 Wusheng。'
    } catch {
        if ($_.Exception.Message -like '*不是 Wusheng*') { throw }
        return $null
    }
}

function Test-PortClosed([int]$Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $async = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if ($async.AsyncWaitHandle.WaitOne(400) -and $client.Connected) { return $false }
        return $true
    } finally { $client.Dispose() }
}

try {
    # Required local verification order: /health -> /generate -> frontend dev server -> browser.
    $ExistingHealth = Get-WushengHealth
    if (-not $ExistingHealth) {
        if (-not (Test-PortClosed 8000)) { throw '8000 端口已被其他服务占用；为避免覆盖其他项目，请先停止该服务或更换端口。' }
        $BackendProcess = Start-Process -FilePath $Python -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000','--log-level','warning') -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $LogRoot 'backend.stdout.log') -RedirectStandardError (Join-Path $LogRoot 'backend.stderr.log')
        for ($Attempt = 0; $Attempt -lt 90; $Attempt++) {
            Start-Sleep -Milliseconds 500
            $ExistingHealth = Get-WushengHealth
            if ($ExistingHealth) { break }
        }
    }
    if (-not $ExistingHealth) { throw '后端健康检查失败，查看 logs/backend.stderr.log。' }
    if ($ExistingHealth.status -ne 'ok' -or $ExistingHealth.database -ne 'SQLite') { throw '后端健康检查未通过。' }

    $AvailableItems = Invoke-RestMethod "$BackendUrl/items"
    if ($AvailableItems.Count -eq 0) { throw '当前没有可用于验证的物品。' }
    $QuestionBody = @{ itemId = $AvailableItems[0].id; question = '这件物品的本地档案中有什么保修信息？' } | ConvertTo-Json
    $Answer = Invoke-RestMethod "$BackendUrl/generate" -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($QuestionBody))
    if (-not $Answer.answer) { throw '本地档案回答验证失败。' }

    $HasFrontend = $false
    try {
        $Page = Invoke-WebRequest $FrontendUrl -UseBasicParsing -TimeoutSec 2
        if ($Page.Content -match 'id="root"') { $HasFrontend = $true }
        else { throw '5173 端口上的网页不是 Wusheng 前端。' }
    } catch {
        if ($_.Exception.Message -like '*不是 Wusheng*') { throw }
    }
    if (-not $HasFrontend) {
        if (-not (Test-PortClosed 5173)) { throw '5173 端口已被其他服务占用；为避免覆盖其他项目，请先停止该服务或更换端口。' }
        $NpmCommand = (Get-Command npm.cmd -ErrorAction Stop).Source
        $NodeRoot = Split-Path -Parent $NpmCommand
        $NpmCli = Join-Path $NodeRoot 'node_modules\npm\bin\npm-cli.js'
        if (-not (Test-Path -LiteralPath $NpmCli)) { throw '找不到 npm-cli.js，请检查 Node.js/npm 安装。' }
        $Node = (Get-Command node.exe -ErrorAction Stop).Source
        $FrontendProcess = Start-Process -FilePath $Node -ArgumentList @($NpmCli,'run','dev','--','--host','127.0.0.1','--strictPort') -WorkingDirectory $FrontendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $LogRoot 'frontend.stdout.log') -RedirectStandardError (Join-Path $LogRoot 'frontend.stderr.log')
    }
    for ($Attempt = 0; $Attempt -lt 60; $Attempt++) {
        Start-Sleep -Milliseconds 500
        try {
            $Page = Invoke-WebRequest $FrontendUrl -UseBasicParsing -TimeoutSec 2
            if ($Page.Content -match 'id="root"') { $HasFrontend = $true; break }
        } catch {}
    }
    if (-not $HasFrontend) { throw '前端启动失败，查看 logs/frontend.stderr.log。' }

    if (-not $NoBrowser) { Start-Process $FrontendUrl }
    Write-Host "物生已启动：$FrontendUrl"
    if ($NoBrowser) { return }
    Write-Host '按 Enter 停止本脚本启动的服务；已存在的服务保持运行。'
    Read-Host | Out-Null
} finally {
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) { Stop-OwnedProcessTree -RootProcessId $FrontendProcess.Id }
    if ($BackendProcess -and -not $BackendProcess.HasExited) { Stop-OwnedProcessTree -RootProcessId $BackendProcess.Id }
}
