# ==========================================
# PCB缺陷检测系统 - 数据库初始化脚本 (Windows PowerShell)
# ==========================================

Write-Host "==========================================" -ForegroundColor Green
Write-Host "  PCB缺陷检测系统 - 数据库初始化" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 等待数据库完全启动
Write-Host "等待数据库服务启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# 检查数据库是否就绪
Write-Host "检查数据库连接..." -ForegroundColor Cyan
$maxRetries = 30
$retryCount = 0

while ($retryCount -lt $maxRetries) {
    try {
        $result = docker-compose exec -T db pg_isready -U pcb_user -d pcb_platform 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "数据库已就绪！" -ForegroundColor Green
            break
        }
    } catch {
        # 继续重试
    }
    
    Write-Host "等待数据库连接... ($($retryCount + 1)/$maxRetries)" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    $retryCount++
    
    if ($retryCount -eq $maxRetries) {
        Write-Host "错误: 数据库连接超时" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "检查管理员账户..." -ForegroundColor Cyan

# 检查管理员是否存在
$adminExists = docker-compose exec -T db psql -U pcb_user -d pcb_platform -t -c "SELECT COUNT(*) FROM users WHERE username='admin';" 2>$null

if ($adminExists -match "0") {
    Write-Host "创建默认管理员账户..." -ForegroundColor Yellow
    
    docker-compose exec -T db psql -U pcb_user -d pcb_platform -c "
    INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at)
    VALUES (
        gen_random_uuid()::text,
        'admin',
        'admin@example.com',
        'pbkdf2_sha256`$870000`$placeholder`$placeholder',
        'admin',
        true,
        NOW(),
        NOW()
    );
    " 2>$null
    
    Write-Host "✅ 管理员账户创建成功！" -ForegroundColor Green
    Write-Host "⚠️  请通过前端界面设置管理员密码" -ForegroundColor Yellow
} else {
    Write-Host "管理员账户已存在，跳过创建。" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  数据库初始化完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
