@echo off
chcp 65001 >nul
title PCB缺陷检测系统 - 后端服务

echo ========================================
echo   PCB缺陷检测系统 - 后端服务
echo ========================================
echo.

cd /d "%~dp0"

echo [步骤 1/4] 确认Python环境...
python --version
echo.

echo [步骤 2/4] 安装Python依赖...
python -m pip install -r requirements.txt
echo.

echo [步骤 3/4] 创建目录结构...
if not exist "models" mkdir models
if not exist "static" mkdir "static"
if not exist "static\uploads" mkdir "static\uploads"
if not exist "static\results" mkdir "static\results"
echo.

echo [步骤 4/4] 检查模型文件...
dir models\*.pt 2>nul >nul
if errorlevel 1 (
    echo   未发现.pt模型文件，系统将以模拟模式运行
    echo   提示：将YOLO模型(.pt)放入models文件夹即可启用真实检测
) else (
    echo   发现模型文件！
)
echo.

echo ========================================
echo [启动] 后端服务启动中...
echo.
echo   API文档: http://localhost:8000/docs
echo   健康检查: http://localhost:8000/health
echo.
echo   按 Ctrl+C 停止服务
echo ========================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
