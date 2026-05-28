# ==========================================
# PCB缺陷检测系统 - 启动脚本 (Windows PowerShell)
# ==========================================

Write-Host "==========================================" -ForegroundColor Green
Write-Host "  PCB缺陷检测系统 - 启动脚本" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 显示环境信息
Write-Host "当前目录: $(Get-Location)"
Write-Host "Docker Compose 版本检查..." -ForegroundColor Cyan

# 检查 Docker 是否安装
try {
    docker-compose --version
} catch {
    Write-Host "错误: Docker Compose 未安装或未启动" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "开始启动服务..." -ForegroundColor Cyan
Write-Host ""

# 停止现有服务（如果存在）
Write-Host "停止现有服务..." -ForegroundColor Yellow
docker-compose down 2>$null

# 启动所有服务
docker-compose up -d

Write-Host ""
Write-Host "等待服务启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# 检查服务状态
Write-Host ""
Write-Host "检查服务状态..." -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  服务启动完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址：" -ForegroundColor White
Write-Host "  - 前端界面: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  - 后端API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  - API文档:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor Cyan
Write-Host ""
Write-Host "数据库信息：" -ForegroundColor White
Write-Host "  - 用户名: pcb_user" -ForegroundColor Cyan
Write-Host "  - 密码: pcb_password" -ForegroundColor Cyan
Write-Host "  - 数据库: pcb_platform" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看日志命令:" -ForegroundColor White
Write-Host '  - 后端日志: docker-compose logs -f backend' -ForegroundColor Cyan
Write-Host '  - 前端日志: docker-compose logs -f frontend' -ForegroundColor Cyan
Write-Host '  - 数据库日志: docker-compose logs -f db' -ForegroundColor Cyan
Write-Host ""
Write-Host "停止服务命令:" -ForegroundColor White
Write-Host "  docker-compose down" -ForegroundColor Cyan
Write-Host ""
Write-Host "停止服务并删除数据命令:" -ForegroundColor White
Write-Host "  docker-compose down -v" -ForegroundColor Cyan
Write-Host ""
