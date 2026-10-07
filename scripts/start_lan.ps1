param([switch]$NoBrowser, [int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw '请先运行 scripts/setup.ps1。' }
$tcp = [System.Net.Sockets.TcpClient]::new()
try { if ($tcp.ConnectAsync('127.0.0.1',$Port).Wait(500) -and $tcp.Connected) { throw "端口 $Port 已占用，请停止默认服务或指定 -Port。" } } catch [System.AggregateException] {} finally { $tcp.Dispose() }
Push-Location (Join-Path $ProjectRoot 'frontend')
try { & npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw '前端构建失败。' } } finally { Pop-Location }
$env:WUSHENG_SHARE_MODE = 'lan'; $env:WUSHENG_PORT = "$Port"; $env:PYTHONUTF8 = '1'
$logs = Join-Path $ProjectRoot 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$server = Start-Process -FilePath $Python -ArgumentList @('-m','uvicorn','backend.main:app','--host','0.0.0.0','--port',"$Port",'--no-proxy-headers') -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs 'lan.stdout.log') -RedirectStandardError (Join-Path $logs 'lan.stderr.log')
try {
    $base = "http://127.0.0.1:$Port"
    $health = $null
    for ($n=0; $n -lt 90; $n++) { Start-Sleep -Milliseconds 500; try { $health = Invoke-RestMethod "$base/health" -TimeoutSec 2; break } catch {} }
    if (-not $health) { throw '分享服务启动失败，请查看 logs/lan.stderr.log。' }
    $items = Invoke-RestMethod "$base/items"
    if ($items.Count -gt 0) { $body = @{itemId=$items[0].id;question='保修到期了吗？'} | ConvertTo-Json; Invoke-RestMethod "$base/generate" -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) | Out-Null }
    $info = Invoke-RestMethod "$base/network/share-info"
    Write-Host "本机管理地址：$base"
    foreach ($address in $info.lanAddresses) { Write-Host "LAN IP：$address"; Write-Host "手机地址：http://${address}:$Port" }
    if (-not $info.reachable) { Write-Warning '未检测到可用 LAN IP，请连接 Wi-Fi 或有线局域网。' }
    Write-Host '手机与电脑须连接同一 Wi-Fi；检查 Windows 私人网络、防火墙和访客网络隔离。本脚本不修改系统设置。'
    Write-Host '管理功能限电脑本机；手机通过物品二维码查看只读档案。'
    if (-not $NoBrowser) { Start-Process $base; Read-Host '按 Enter 停止本次分享服务' | Out-Null }
} finally { if (-not $NoBrowser -or -not $health) { Stop-Process -Id $server.Id -ErrorAction SilentlyContinue } }
