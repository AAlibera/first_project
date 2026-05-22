@echo off
echo ========================================
echo PCB缺陷检测系统 - 前端启动脚本
echo ========================================
echo.

cd /d "%~dp0frontend"

echo [1/3] 正在检查Node.js版本...
node --version
if errorlevel 1 (
    echo [错误] 未找到Node.js，请先安装！
    pause
    exit /b 1
)

echo.
echo [2/3] 正在安装依赖...
call npm install
if errorlevel 1 (
    echo [错误] 依赖安装失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 正在启动开发服务器...
echo.
echo 启动成功后，请访问: http://localhost:5173
echo 按 Ctrl+C 可以停止服务器
echo.
echo ========================================
echo.

npm run dev

pause
