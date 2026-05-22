# PCB缺陷检测系统 - 后端启动脚本
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PCB缺陷检测系统 - 后端服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切换到backend目录
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $BackendDir

Write-Host "[步骤 1/4] 检查Python环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "  $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [错误] 未找到Python！" -ForegroundColor Red
    Write-Host "  请先安装Python 3.10+ : https://www.python.org/downloads/" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Write-Host ""

Write-Host "[步骤 2/4] 安装Python依赖..." -ForegroundColor Yellow
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [警告] 部分依赖可能安装失败，继续启动..." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "[步骤 3/4] 创建目录结构..." -ForegroundColor Yellow
$directories = @("models", "static", "static/uploads", "static/results")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "  创建: $dir" -ForegroundColor Gray
    }
}
Write-Host ""

Write-Host "[步骤 4/4] 检查模型文件..." -ForegroundColor Yellow
$modelFiles = Get-ChildItem "models\*.pt" -ErrorAction SilentlyContinue
if ($modelFiles) {
    Write-Host "  发现 $($modelFiles.Count) 个模型文件:" -ForegroundColor Green
    foreach ($model in $modelFiles) {
        Write-Host "    - $($model.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "  未发现.pt模型文件，系统将以模拟模式运行" -ForegroundColor Yellow
    Write-Host "  提示：将YOLO模型(.pt)放入models文件夹即可启用真实检测" -ForegroundColor Gray
}
Write-Host ""

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  后端服务启动中..." -ForegroundColor Green
Write-Host ""
Write-Host "  API文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  健康检查: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "  按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
