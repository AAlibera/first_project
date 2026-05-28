@echo off
echo ==========================================
echo    PCB缺陷检测系统 - 启动脚本
echo ==========================================
echo.

cd /d "G:\BaiduNetdiskDownload\20260519\first_project"

echo 正在启动服务...
echo.

rem 使用 Docker Compose 启动所有服务
docker-compose up -d --build

echo.
echo 服务启动完成！
echo.
echo 访问地址：
echo   - 前端界面: http://localhost:5173
echo   - 后端API:  http://localhost:8000
echo   - API文档:  http://localhost:8000/docs
echo.
echo 按任意键退出...
pause >nul
