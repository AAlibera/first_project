@echo off
chcp 65001 >nul
title PCB缺陷检测系统 - Docker启动

echo.
echo ========================================
echo   PCB缺陷检测系统 - Docker启动
echo ========================================
echo.

cd /d "%~dp0"

echo [检查] 检查Docker状态...
docker version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Docker！
    echo 请确保已安装并启动Docker Desktop
    pause
    exit /b 1
)
echo [成功] Docker已安装
echo.

echo [构建] 构建并启动容器...
echo.

docker compose up -d --build

if errorlevel 1 (
    echo.
    echo [错误] 启动失败！
    echo 请检查Docker是否正常运行
    pause
    exit /b 1
)

echo.
echo ========================================
echo [成功] 服务已启动！
echo.
echo   API地址: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo   健康检查: http://localhost:8000/health
echo.
echo   查看日志: docker compose logs -f
echo   停止服务: docker compose down
echo ========================================
echo.

pause
