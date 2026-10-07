param([switch]$NoBrowser, [ValidateRange(1,65535)][int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Write-Host '当前 start.ps1 已默认支持安全局域网只读分享；start_lan.ps1 是兼容入口。'
& (Join-Path $PSScriptRoot 'start.ps1') -NoBrowser:$NoBrowser -Port $Port
