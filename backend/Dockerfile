# PCB缺陷检测系统 - Docker镜像
FROM python:3.11-slim

WORKDIR /app/backend

# 使用清华镜像源加速安装
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --upgrade pip

# 安装系统依赖（OpenCV需要）
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .

# 先安装基础依赖
RUN pip install --no-cache-dir -r requirements.txt

# 尝试安装AI模型（可选，失败不影响基本功能）
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu || true
RUN pip install --no-cache-dir ultralytics || true

COPY .pcb_platform ../
COPY backend/app ./app
COPY backend/models ./backend/models
COPY backend/static ./backend/static

RUN mkdir -p backend/models backend/static/uploads backend/static/results backend/logs backend/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
