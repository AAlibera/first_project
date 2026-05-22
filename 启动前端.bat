@echo off
chcp 65001 >nul
title PCB缺陷检测系统 - 前端

echo ========================================
echo   PCB缺陷检测系统 - 启动中...
echo ========================================
echo.

cd /d "%~dp0frontend"

echo [1/3] 刷新环境变量...
set PATH=%PATH%;C:\Program Files\nodejs
echo.

echo [2/3] 检查Node.js...
node --version
if errorlevel 1 (
    echo [错误] 未找到Node.js，请先安装！
    pause
    exit /b 1
)
echo.

echo [3/3] 检查npm...
npm --version
if errorlevel 1 (
    echo [错误] 未找到npm，请检查Node.js安装！
    pause
    exit /b 1
)
echo.

echo ========================================
echo [启动] 正在启动开发服务器...
echo.
echo   请访问: http://localhost:5173
echo   按 Ctrl+C 停止
echo ========================================
echo.

npm run dev
