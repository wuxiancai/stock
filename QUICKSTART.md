# 🚀 快速启动指南

欢迎使用股票交易系统！这是一个基于 FastAPI 的现代化股票数据分析平台。

## ⚡ 一键启动 (推荐)

```bash
# 1. 运行自动化设置脚本
./setup_macos.sh

# 2. 配置环境变量 (可选，但推荐)
cp .env.example .env
# 编辑 .env 文件，设置 TUSHARE_TOKEN

# 3. 启动开发环境
./start_dev.sh
```

## 🎯 核心功能演示

```bash
# 运行功能演示
./demo.sh
```

## 📚 访问服务

启动成功后，访问以下地址：

- **系统主页**: http://localhost:8080/
- **API 文档**: http://localhost:8080/docs
- **ReDoc 文档**: http://localhost:8080/redoc
- **健康检查**: http://localhost:8080/health

## 🛠️ 管理命令

### 数据库管理
```bash
./scripts/db_manager.sh init      # 初始化数据库
./scripts/db_manager.sh migrate   # 运行迁移
./scripts/db_manager.sh status    # 检查状态
./scripts/db_manager.sh backup    # 备份数据库
```

### Celery 任务管理
```bash
./scripts/celery_manager.sh worker   # 启动 Worker
./scripts/celery_manager.sh beat     # 启动定时任务
./scripts/celery_manager.sh flower   # 启动监控界面
./scripts/celery_manager.sh status   # 检查状态
```

### 测试
```bash
./run_tests.sh                    # 运行所有测试
```

### 停止服务
```bash
./stop_dev.sh                     # 停止开发环境
```

## 🐳 Docker 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

## 🔧 故障排除

### 常见问题

1. **权限问题**
   ```bash
   chmod +x *.sh scripts/*.sh
   ```

2. **PostgreSQL 连接失败**
   ```bash
   brew services restart postgresql@15
   ```

3. **Redis 连接失败**
   ```bash
   brew services restart redis
   ```

4. **TA-Lib 安装失败**
   ```bash
   brew reinstall ta-lib
   pip install --upgrade --force-reinstall TA-Lib
   ```

### 检查服务状态

```bash
# 检查 PostgreSQL
pg_isready -h localhost -p 5432

# 检查 Redis
redis-cli ping

# 检查 Python 环境
python --version
pip list | grep -E "(fastapi|sqlalchemy|redis)"
```

## 📊 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Server    │    │   Database      │
│   (Static)      │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Cache         │    │   Task Queue    │
                       │   (Redis)       │    │   (Celery)      │
                       └─────────────────┘    └─────────────────┘
```

## 🔑 环境变量配置

重要的环境变量：

```bash
# 数据源配置
TUSHARE_TOKEN=your_tushare_token_here

# 数据库配置
DATABASE_URL=postgresql://stock_user:stock_password@localhost:5432/stock_trading_db

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# API 配置
API_HOST=0.0.0.0
API_PORT=8080
```

## 📞 获取帮助

- 查看 [README.md](README.md) 了解详细信息
- 运行 `./demo.sh` 查看功能演示
- 访问 http://localhost:8080/docs 查看 API 文档

---

🎉 **祝您使用愉快！** 如有问题，请查看日志文件或提交 Issue。