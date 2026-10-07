param([switch]$NoBrowser, [switch]$Smoke, [switch]$CheckOnly, [int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
function Get-PythonVersion([string]$Executable, [string[]]$Prefix = @()) {
    $PreviousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $Detected = & $Executable @Prefix -c 'import sys; print(sys.version_info.major, sys.version_info.minor, sep=chr(46))' 2>$null
        if ($LASTEXITCODE -eq 0) { return $Detected }
        return ''
    } finally { $ErrorActionPreference = $PreviousPreference }
}
try {
    foreach ($Script in @('setup.ps1', 'start.ps1')) {
        if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $Script))) { throw "找不到 scripts/$Script，请重新获取完整仓库。" }
    }
    $Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
    $PythonReady = $false
    if (Test-Path -LiteralPath $Python) {
        $Version = Get-PythonVersion $Python
        $PythonReady = $Version -eq '3.12'
        if (-not $PythonReady) { throw '当前 .venv 不是 Python 3.12 环境，请保留用户 data 并按 README 重新安装依赖。' }
    } else {
        if (Get-Command py.exe -ErrorAction SilentlyContinue) {
            $Version = Get-PythonVersion 'py.exe' @('-3.12')
            $PythonReady = $Version -eq '3.12'
        }
        if (-not $PythonReady -and (Get-Command python.exe -ErrorAction SilentlyContinue)) {
            $Version = Get-PythonVersion 'python.exe'
            $PythonReady = $Version -eq '3.12'
        }
    }
    if (-not $PythonReady) { throw '未检测到 Python 3.12。请安装 Python 3.12 后重新双击“启动物生.cmd”。' }
    if (-not (Get-Command node.exe -ErrorAction SilentlyContinue) -or -not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw '未检测到 Node.js 22 LTS。请安装后重新运行。' }
    $NodeMajor = & node.exe -p 'process.versions.node.match(/^[0-9]+/)[0]'
    if ($LASTEXITCODE -ne 0 -or [int]$NodeMajor -lt 22) { throw '未检测到 Node.js 22 LTS 或更新版本。请安装后重新运行。' }
    Write-Host "物生项目目录：$ProjectRoot"
    if ($CheckOnly) { Write-Host '启动入口、Python 3.12、Node.js 与脚本路径检查通过。'; exit 0 }
    $NeedsInstall = -not (Test-Path -LiteralPath $Python) -or -not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'frontend\node_modules\.bin\vite.cmd'))
    if (-not $NeedsInstall) {
        $PreviousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $Python -c 'import fastapi, sqlalchemy, reportlab, rapidocr_onnxruntime' 2>$null
            $NeedsInstall = $LASTEXITCODE -ne 0
        } finally { $ErrorActionPreference = $PreviousPreference }
    }
    if ($NeedsInstall) {
        Write-Host '首次运行需要安装项目依赖，将自动执行 setup.ps1。首次安装需要联网；不会安装 Ollama 或下载大模型。'
        & (Join-Path $PSScriptRoot 'setup.ps1')
        if ($LASTEXITCODE -ne 0) { throw '依赖安装未完成，请检查网络和上方错误后重试。' }
    }
    # Preserve the caller's provider settings; the backend defaults to EvidenceProvider.
    & (Join-Path $PSScriptRoot 'start.ps1') -NoBrowser:$NoBrowser -Smoke:$Smoke -Port $Port
    if ($LASTEXITCODE -ne 0) { throw '启动未完成，请查看上方提示。' }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    exit 1
}
