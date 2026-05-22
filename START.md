# PCB缺陷检测系统 - 启动说明

## 快速启动

### 1. 安装依赖
打开终端，进入前端目录并安装依赖：

```bash
cd G:\BaiduNetdiskDownload\20260519\project\frontend
npm install
```

### 2. 启动开发服务器
依赖安装完成后，运行：

```bash
npm run dev
```

### 3. 访问应用
启动成功后，打开浏览器访问：

- **前端**: http://localhost:5173
- **后端API文档**: http://localhost:8000/docs

## 环境要求

- Node.js 18+ (您已安装 v24.15.0 ✓)
- Python 3.10+ (用于后端)
- Docker (可选，用于后端服务)

## 注意事项

1. 如果遇到命令找不到的问题，请**重新打开终端窗口**
2. 确保 Node.js 已正确添加到系统 PATH
3. 后端需要单独启动才能使用完整功能

## 如果需要重启终端后仍然找不到 npm

可以尝试以下命令检查：

```bash
# Windows PowerShell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 或者使用完整路径（根据实际安装位置）
C:\Program Files\nodejs\npm.cmd install
```
