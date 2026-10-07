param(
    [switch]$NoBrowser,
    [ValidateRange(1,65535)][int]$Port = 8000,
    [switch]$Smoke,
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Python) { $Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe' }
$Python = (Get-Command $Python -ErrorAction Stop).Source
$FrontendRoot = Join-Path $ProjectRoot 'frontend'
if (-not (Test-Path -LiteralPath (Join-Path $FrontendRoot 'node_modules\.bin\vite.cmd'))) { throw '请先运行 scripts/setup.ps1 安装锁定依赖。' }
if (@(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).Count) { throw "端口 $Port 已占用，请关闭旧物生服务或指定 -Port。本次没有停止其他进程。" }
& $Python -c 'import fastapi, sqlalchemy, reportlab'
if ($LASTEXITCODE -ne 0) { throw 'Python 依赖不完整，请运行 scripts/setup.ps1。' }
Push-Location $FrontendRoot
try { & npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw '前端构建失败。' } } finally { Pop-Location }
$env:WUSHENG_SHARE_MODE = 'lan-ready'; $env:WUSHENG_PORT = "$Port"; $env:PYTHONUTF8 = '1'
$LogRoot = Join-Path $ProjectRoot 'logs'
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$BaseUrl = "http://127.0.0.1:$Port"
$Server = $null; $Ready = $false
function Stop-OwnedProcessTree([int]$RootProcessId) {
    foreach ($Child in @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $RootProcessId" -ErrorAction SilentlyContinue)) { Stop-OwnedProcessTree -RootProcessId $Child.ProcessId }
    Stop-Process -Id $RootProcessId -ErrorAction SilentlyContinue
}
try {
    $Server = Start-Process -FilePath $Python -ArgumentList @('-m','uvicorn','backend.main:app','--host','0.0.0.0','--port',"$Port",'--no-proxy-headers','--log-level','warning') -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $LogRoot "server-$Port.stdout.log") -RedirectStandardError (Join-Path $LogRoot "server-$Port.stderr.log")
    $Health = $null
    for ($Attempt = 0; $Attempt -lt 90; $Attempt++) {
        Start-Sleep -Milliseconds 500
        try { $Health = Invoke-RestMethod "$BaseUrl/health" -TimeoutSec 2; break } catch {}
        if ($Server.HasExited) { throw "服务启动失败，请查看 logs/server-$Port.stderr.log。" }
    }
    if ($Health.status -ne 'ok' -or $Health.database -ne 'SQLite') { throw '后端健康检查失败。' }
    $Items = Invoke-RestMethod "$BaseUrl/items"
    if ($Items.Count -gt 0) {
        $Question = @{itemId=$Items[0].id;question='这件物品的本地档案中有什么保修信息？'} | ConvertTo-Json
        $Answer = Invoke-RestMethod "$BaseUrl/generate" -Method Post -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($Question))
        if (-not $Answer.answer) { throw '本地档案问答检查失败。' }
    }
    $Page = Invoke-WebRequest "$BaseUrl/" -UseBasicParsing -TimeoutSec 5
    if ($Page.Content -notmatch 'id="root"') { throw '生产界面未加载。' }
    $Info = Invoke-RestMethod "$BaseUrl/network/share-info" -TimeoutSec 10
    if ($Info.mode -ne 'lan-ready') { throw '分享服务配置不一致。' }
    $Ready = $true
    Write-Host '物生已启动'
    Write-Host "电脑管理地址：$BaseUrl"
    foreach ($Address in $Info.lanAddresses) { Write-Host "手机只读分享网络：$Address"; Write-Host "局域网地址：http://${Address}:$Port" }
    if (-not $Info.reachable) { Write-Warning '当前未检测到可用局域网地址，一物一码只能在本机管理，稍后连接 Wi-Fi 后可重新检测。' }
    Write-Host '手机和电脑必须连接同一 Wi-Fi。请确认 Windows 防火墙允许 Python 在“私人网络”通信，并检查访客网络隔离。'
    Write-Host '手机通过二维码查看只读档案；管理操作限电脑本机。'
    Write-Host "服务进程：$($Server.Id)"
    if ($NoBrowser) { Write-Output "WUSHENG_SERVER_PID=$($Server.Id)" }
    if (-not $NoBrowser -and -not $Smoke) { Start-Process $BaseUrl; Read-Host '按 Enter 停止本次物生服务' | Out-Null }
} finally {
    # -NoBrowser leaves this server running; -Smoke stops only its own server.
    if ($Server -and (-not $Ready -or $Smoke -or -not $NoBrowser)) { Stop-OwnedProcessTree -RootProcessId $Server.Id }
}
