param([string]$PythonIndexUrl = 'https://pypi.org/simple')

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvRoot = Join-Path $ProjectRoot '.venv'
$Python = Join-Path $VenvRoot 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    $DetectedPython = ''
    if (Get-Command python.exe -ErrorAction SilentlyContinue) {
        $PreviousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try { $DetectedPython = & python.exe -c 'import sys; print(sys.version_info.major, sys.version_info.minor, sep=chr(46))' 2>$null } finally { $ErrorActionPreference = $PreviousPreference }
    }
    if ($DetectedPython -eq '3.12') {
        & python.exe -m venv $VenvRoot
    } elseif (Get-Command py.exe -ErrorAction SilentlyContinue) {
        & py.exe -3.12 -m venv $VenvRoot
    } else {
        throw '需要先安装 Python 3.12。'
    }
    if ($LASTEXITCODE -ne 0) { throw '无法建立 Python 虚拟环境。' }
}

& $Python -m pip install --index-url $PythonIndexUrl --upgrade pip
if ($LASTEXITCODE -ne 0) { throw '升级 pip 失败。' }
& $Python -m pip install --index-url $PythonIndexUrl -r (Join-Path $ProjectRoot 'backend\requirements-lock.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python 依赖安装失败。' }

Push-Location (Join-Path $ProjectRoot 'frontend')
try {
    npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw '前端依赖安装失败。' }
} finally {
    Pop-Location
}

Write-Host '安装完成。运行 scripts/start.ps1 启动物生。'
