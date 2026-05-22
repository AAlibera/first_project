# PCB缺陷检测系统 - 自动启动脚本
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PCB缺陷检测系统 - 前端启动器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设置工作目录
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $ScriptRoot "frontend"

Write-Host "[步骤 1/3] 切换到前端目录..." -ForegroundColor Yellow
if (Test-Path $FrontendDir) {
    Set-Location $FrontendDir
    Write-Host "  当前目录: $FrontendDir" -ForegroundColor Gray
} else {
    Write-Host "  [错误] 前端目录不存在: $FrontendDir" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Write-Host ""

Write-Host "[步骤 2/3] 检查Node.js环境..." -ForegroundColor Yellow
# 刷新环境变量
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

try {
    $nodeVersion = node --version
    Write-Host "  Node.js版本: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [错误] 未找到Node.js！" -ForegroundColor Red
    Write-Host "  请确保Node.js已添加到系统PATH" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}

try {
    $npmVersion = npm --version
    Write-Host "  npm版本: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "  [错误] 未找到npm！" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Write-Host ""

Write-Host "[步骤 3/3] 安装依赖..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "  正在安装npm依赖..." -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [错误] 依赖安装失败！" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
} else {
    Write-Host "  依赖已安装" -ForegroundColor Green
}
Write-Host ""

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  服务器启动成功！" -ForegroundColor Green
Write-Host ""
Write-Host "  请在浏览器中访问:" -ForegroundColor Cyan
Write-Host "  http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "  按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 启动开发服务器
npm run dev
