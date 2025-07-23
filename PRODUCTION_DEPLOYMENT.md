# 股票交易系统 - 生产环境部署指南

## 概述

除了Docker部署方式外，股票交易系统还提供了多种生产环境部署方案，适用于不同的服务器环境和需求。

## 🚀 快速部署（推荐）

### Ubuntu系统一键部署

**只需要一个命令**：
```bash
chmod +x deploy_ubuntu.sh
./deploy_ubuntu.sh
```

该脚本已集成所有功能，会自动完成：
- ✅ 安装系统依赖（包括TA-Lib开发库）
- ✅ 自动修复talib-binary等依赖问题
- ✅ 配置PostgreSQL和Redis
- ✅ 创建Python虚拟环境
- ✅ 智能安装Python依赖
- ✅ 配置Nginx反向代理
- ✅ 配置Supervisor进程管理
- ✅ 设置防火墙规则
- ✅ 启动所有服务
- ✅ 验证安装结果

## 部署方案对比

| 部署方案 | 适用场景 | 优点 | 缺点 |
|---------|---------|------|------|
| **Ubuntu一键部署** | Ubuntu服务器 | 全自动配置、零配置部署 | 仅限Ubuntu |
| **Docker** | 容器化环境 | 环境一致性、易于扩展 | 需要Docker知识 |
| **Gunicorn + Nginx** | 传统服务器 | 性能优秀、配置灵活 | 配置复杂 |
| **Systemd服务** | Linux系统服务 | 开机自启、系统集成 | 仅限Linux |
| **Supervisor** | 进程管理 | 进程监控、自动重启 | 需要额外安装 |

## 1. Gunicorn + Nginx 部署

### 1.1 快速启动

```bash
# 启动生产环境
./start_prod.sh

# 后台运行
./start_prod.sh --daemon

# 停止服务
./stop_prod.sh
```

### 1.2 配置说明

- **Gunicorn配置**: `gunicorn.conf.py`
- **工作进程数**: CPU核心数 × 2 + 1
- **端口**: 8080
- **日志目录**: `logs/`

### 1.3 Nginx配置

系统已包含完整的Nginx配置文件：

- **主配置**: `nginx/nginx.conf`
- **站点配置**: `nginx/conf.d/default.conf`

启动Nginx（需要单独安装）：
```bash
# macOS
brew install nginx
brew services start nginx

# Ubuntu/Debian
sudo apt-get install nginx
sudo systemctl start nginx

# CentOS/RHEL
sudo yum install nginx
sudo systemctl start nginx
```

## 2. Systemd 系统服务

### 2.1 安装为系统服务

```bash
# 安装服务（需要root权限）
sudo ./install_service.sh
```

### 2.2 服务管理

```bash
# 启动服务
sudo systemctl start stock-trading

# 停止服务
sudo systemctl stop stock-trading

# 重启服务
sudo systemctl restart stock-trading

# 查看状态
sudo systemctl status stock-trading

# 查看日志
sudo journalctl -u stock-trading -f

# 开机自启
sudo systemctl enable stock-trading

# 禁用自启
sudo systemctl disable stock-trading
```

### 2.3 服务特性

- ✅ 开机自动启动
- ✅ 进程崩溃自动重启
- ✅ 系统日志集成
- ✅ 资源限制控制
- ✅ 安全沙箱运行

## 3. Supervisor 进程管理

### 3.1 安装Supervisor配置

```bash
# 安装Supervisor配置（需要root权限）
sudo ./install_supervisor.sh
```

### 3.2 进程管理

```bash
# 查看所有程序状态
sudo supervisorctl status

# 启动股票交易系统
sudo supervisorctl start stock-trading:*

# 停止股票交易系统
sudo supervisorctl stop stock-trading:*

# 重启股票交易系统
sudo supervisorctl restart stock-trading:*

# 查看实时日志
sudo supervisorctl tail -f stock-api
sudo supervisorctl tail -f stock-celery-worker
sudo supervisorctl tail -f stock-celery-beat
```

### 3.3 管理的进程

- **stock-api**: FastAPI应用服务器
- **stock-celery-worker**: Celery任务处理器
- **stock-celery-beat**: Celery定时任务调度器

## 4. 环境配置

### 4.1 环境变量

确保 `.env` 文件包含生产环境配置：

```bash
# 环境设置
ENVIRONMENT=production

# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/stock_db
DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/stock_db

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API密钥
TUSHARE_TOKEN=your_tushare_token
AKSHARE_TOKEN=your_akshare_token

# 安全配置
SECRET_KEY=your_secure_secret_key_here
```

### 4.2 依赖服务

确保以下服务正在运行：

```bash
# PostgreSQL
sudo systemctl start postgresql

# Redis
sudo systemctl start redis

# 或使用Homebrew (macOS)
brew services start postgresql@14
brew services start redis
```

## 5. 性能优化

### 5.1 Gunicorn优化

编辑 `gunicorn.conf.py`：

```python
# 根据服务器配置调整
workers = 8  # 建议: CPU核心数 × 2 + 1
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# 内存优化
preload_app = True
worker_class = "uvicorn.workers.UvicornWorker"
```

### 5.2 数据库连接池

在 `app/config.py` 中调整：

```python
# 生产环境数据库配置
pool_size = 50
max_overflow = 100
pool_recycle = 3600
```

### 5.3 Redis优化

```bash
# 编辑Redis配置
sudo vim /etc/redis/redis.conf

# 关键配置
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
```

## 6. 监控和日志

### 6.1 日志文件位置

```
logs/
├── access.log          # Gunicorn访问日志
├── error.log           # Gunicorn错误日志
├── gunicorn.log        # Gunicorn主日志
├── supervisor-*.log    # Supervisor进程日志
└── gunicorn.pid        # 进程PID文件
```

### 6.2 健康检查

```bash
# API健康检查
curl http://localhost:8080/api/v1/health

# 服务状态检查
curl -I http://localhost:8080/docs
```

### 6.3 性能监控

可以集成以下监控工具：

- **Prometheus + Grafana**: 指标监控
- **ELK Stack**: 日志分析
- **New Relic**: APM监控
- **Sentry**: 错误追踪

## 7. 安全配置

### 7.1 防火墙设置

```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### 7.2 SSL/TLS配置

如需HTTPS，在Nginx配置中添加SSL证书：

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... 其他配置
}
```

## 8. 故障排除

### 8.1 Ubuntu系统常见问题

#### 问题1: talib-binary安装失败
```
ERROR: Could not find a version that satisfies the requirement talib-binary
ERROR: No matching distribution found for talib-binary
```

**解决方案**:
这个问题已经在 `deploy_ubuntu.sh` 脚本中自动解决了。脚本会：
1. 自动安装 `libta-lib-dev` 系统依赖
2. 清理冲突的 `talib-binary` 包
3. 安装正确的 `TA-Lib` 包
4. 如果失败，自动从源码编译

如果仍有问题，可以手动执行：
```bash
sudo apt-get install libta-lib-dev pkg-config
pip uninstall talib-binary
pip install TA-Lib
```

#### 问题2: systemd服务启动失败
```
Failed to locate executable /home/ubuntu/...
```

**解决方案**:
1. 使用修复后的 `install_service.sh` 脚本
2. 或者直接使用 `deploy_ubuntu.sh` 一键部署
3. 确保虚拟环境和gunicorn配置文件存在

```bash
# 检查虚拟环境
ls -la venv/

# 检查gunicorn
venv/bin/gunicorn --version

# 重新安装服务
sudo ./install_service.sh
```

#### 问题2: 权限问题
```bash
# 确保文件权限正确
sudo chown -R $USER:$USER /path/to/stock/
chmod +x start_prod.sh stop_prod.sh
```

#### 问题3: 数据库连接失败
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 重置数据库
sudo -u postgres psql -c "DROP DATABASE IF EXISTS stock_trading_db;"
sudo -u postgres psql -c "CREATE DATABASE stock_trading_db OWNER stock_user;"
```

### 8.2 通用问题

1. **端口被占用**
   ```bash
   lsof -i :8080
   kill -9 <PID>
   ```

2. **数据库连接失败**
   ```bash
   # 检查PostgreSQL状态
   sudo systemctl status postgresql
   
   # 测试连接
   psql -h localhost -U stock_user -d stock_trading_db
   ```

3. **Redis连接失败**
   ```bash
   # 检查Redis状态
   sudo systemctl status redis
   
   # 测试连接
   redis-cli ping
   ```

### 8.2 日志查看

```bash
# 查看Gunicorn日志
tail -f logs/error.log

# 查看系统服务日志
sudo journalctl -u stock-trading -f

# 查看Supervisor日志
sudo supervisorctl tail -f stock-api
```

## 9. 备份和恢复

### 9.1 数据库备份

```bash
# 创建备份
pg_dump -h localhost -U stock_user stock_trading_db > backup.sql

# 恢复备份
psql -h localhost -U stock_user stock_trading_db < backup.sql
```

### 9.2 配置备份

```bash
# 备份重要配置文件
tar -czf config_backup.tar.gz .env gunicorn.conf.py nginx/
```

## 总结

本系统提供了多种生产环境部署方案，可以根据具体需求选择：

- **简单部署**: 使用 `start_prod.sh`
- **系统集成**: 使用 Systemd 服务
- **进程管理**: 使用 Supervisor
- **高可用**: 结合 Nginx + Gunicorn + Supervisor

每种方案都经过测试，可以在生产环境中稳定运行。