#!/bin/bash
set -e

echo "=========================================="
echo "  PCB缺陷检测系统 - 启动脚本"
echo "=========================================="
echo ""

# 显示环境信息
echo "当前目录: $(pwd)"
echo "Docker Compose 版本检查..."
docker-compose --version

echo ""
echo "开始启动服务..."
echo ""

# 启动所有服务
docker-compose up -d

echo ""
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "检查服务状态..."
docker-compose ps

echo ""
echo "=========================================="
echo "  服务启动完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  - 前端界面: http://localhost:5173"
echo "  - 后端API:  http://localhost:8000"
echo "  - API文档:  http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5432"
echo ""
echo "数据库信息："
echo "  - 用户名: pcb_user"
echo "  - 密码: pcb_password"
echo "  - 数据库: pcb_platform"
echo ""
echo "查看日志命令:"
echo "  - 后端日志: docker-compose logs -f backend"
echo "  - 前端日志: docker-compose logs -f frontend"
echo "  - 数据库日志: docker-compose logs -f db"
echo ""
echo "停止服务命令:"
echo "  docker-compose down"
echo ""
echo "停止服务并删除数据命令:"
echo "  docker-compose down -v"
echo ""
