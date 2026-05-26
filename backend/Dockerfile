# PCB缺陷检测系统 - Docker镜像
FROM python:3.11-slim

WORKDIR /app/backend

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY .pcb_platform ../
COPY backend/app ./app
COPY backend/models ./backend/models
COPY backend/static ./backend/static

RUN mkdir -p backend/models backend/static/uploads backend/static/results backend/logs backend/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
