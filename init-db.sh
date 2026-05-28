#!/bin/bash
set -e

echo "=========================================="
echo "  PCB缺陷检测系统 - 数据库初始化"
echo "=========================================="
echo ""

# 等待数据库完全启动
echo "等待数据库服务启动..."
sleep 5

# 检查数据库是否就绪
until PGPASSWORD=pcb_password psql -h localhost -U pcb_user -d pcb_platform -c '\q' 2>/dev/null; do
    echo "等待数据库连接..."
    sleep 2
done

echo "数据库已就绪！"
echo ""

# 创建管理员账户（如果不存在）
echo "检查管理员账户..."
ADMIN_EXISTS=$(PGPASSWORD=pcb_password psql -h localhost -U pcb_user -d pcb_platform -t -c "SELECT COUNT(*) FROM users WHERE username='admin';")

if [ "$ADMIN_EXISTS" -eq 0 ]; then
    echo "创建默认管理员账户..."
    # 这里的密码会在应用启动时由后端哈希处理
    # 但我们先创建一个占位符，实际密码将在首次登录后设置
    PGPASSWORD=pcb_password psql -h localhost -U pcb_user -d pcb_platform -c "
    INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at)
    VALUES (
        gen_random_uuid()::text,
        'admin',
        'admin@example.com',
        'pbkdf2_sha256\$870000\$placeholder\$placeholder',
        'admin',
        true,
        NOW(),
        NOW()
    );
    "
    echo "✅ 管理员账户创建成功！"
    echo "⚠️  请通过前端界面设置管理员密码"
else
    echo "管理员账户已存在，跳过创建。"
fi

echo ""
echo "=========================================="
echo "  数据库初始化完成！"
echo "=========================================="
echo ""
