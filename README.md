# PCB缺陷检测系统

基于深度学习的PCB（印制电路板）缺陷检测系统，支持单图检测、批量处理、视频检测和实时摄像头监控。

## 项目结构

```
project/
├── backend/                    # 后端代码 (Python + FastAPI)
│   ├── app/
│   │   ├── api/               # API路由
│   │   ├── services/          # 业务服务
│   │   ├── models/            # 数据模型
│   │   └── config.py
│   ├── data/                  # 数据目录
│   ├── models/                # AI模型
│   ├── docker-compose.yml
│   └── requirements.txt
└── frontend/                  # 前端代码 (Vue 3 + TypeScript)
    ├── src/
    │   ├── components/        # 组件
    │   ├── views/            # 页面
    │   ├── utils/            # 工具函数
    │   └── types/            # 类型定义
    └── package.json
```

## 功能特性

### 1. 单图检测
- 支持上传单张PCB图片
- 实时缺陷检测和标注
- 检测结果可视化展示

### 2. 文件夹检测
- 支持批量上传多张图片
- 批量处理和结果统计
- 进度显示和报告

### 3. 视频检测
- 支持上传视频文件
- 逐帧检测和结果汇总
- 检测统计信息

### 4. 摄像头检测
- 实时摄像头采集
- 实时检测和反馈
- 截图保存功能

## 技术栈

### 后端
- **FastAPI**: 高性能Web框架
- **SQLAlchemy**: ORM框架
- **PostgreSQL**: 数据库
- **MinIO**: 对象存储
- **YOLOv11**: 目标检测模型

### 前端
- **Vue 3**: 前端框架
- **TypeScript**: 类型安全
- **Tailwind CSS**: 样式框架
- **Vite**: 构建工具
- **Lucide**: 图标库

## 快速开始

### 环境要求
- Node.js 18+
- Python 3.10+
- Docker (推荐)

### 启动后端

#### 使用 Docker (推荐)
```bash
cd backend
docker-compose up -d
```

#### 手动启动
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 即可使用。

## 检测目标类型

系统支持检测以下PCB缺陷类型：

| 类型 | 中文 | 说明 |
|------|------|------|
| scratch | 划痕 | PCB表面划痕 |
| crack | 裂纹 | PCB表面裂纹 |
| hole | 孔洞 | 不应该存在的孔洞 |
| deformation | 变形 | PCB变形问题 |
| missing | 缺失 | 元器件缺失 |
| solder | 焊点异常 | 焊接质量问题 |

## 配置说明

后端配置通过 `.env` 文件进行，主要配置项：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=pcb_user
DB_PASSWORD=pcb_password
DB_DATABASE=pcb_detection

# MinIO配置
MINIO_HOST=localhost
MINIO_PORT=9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=minio_password

# 模型配置
YOLO_MODEL_PATH=models/yolo11n.pt
CONFIDENCE_THRESHOLD=0.5
```

## 部署说明

### 使用 Docker Compose

项目已配置好完整的 Docker Compose 配置，一键启动所有服务：

```bash
cd backend
docker-compose up -d
```

这将启动：
- FastAPI后端服务
- PostgreSQL数据库
- MinIO对象存储
- Redis缓存

### 前端构建

```bash
cd frontend
npm run build
```

构建产物位于 `frontend/dist` 目录，可以部署到 Nginx 或其他静态文件服务器。

## API文档

后端启动后访问 http://localhost:8000/docs 可以查看完整的API文档。

## 开发说明

### 添加新的检测类型

1. 在 `backend/app/config.py` 中更新配置
2. 在模型训练数据中添加新类型的标注
3. 在前端 `src/types/index.ts` 更新类型定义
4. 在前端 `src/views/HomeView.vue` 更新展示

### 自定义模型

将训练好的模型文件放到 `backend/models/` 目录，然后修改 `.env` 文件中的 `YOLO_MODEL_PATH` 配置。

## 许可证

MIT License
