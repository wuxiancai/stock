# 股票交易系统

基于 FastAPI 的现代化股票数据分析平台，提供实时股票数据获取、技术指标计算、九转序列策略分析等功能。

## 🚀 功能特性

- **实时数据获取**: 支持 Tushare 和 AKShare 数据源
- **技术指标计算**: MA、EMA、MACD、RSI、KDJ、布林带等
- **九转序列策略**: TD Sequential 买卖信号分析
- **WebSocket 推送**: 实时数据推送服务
- **异步任务处理**: 基于 Celery 的后台任务队列
- **缓存优化**: Redis 缓存提升性能
- **API 文档**: 自动生成的 OpenAPI 文档
- **容器化部署**: Docker 和 Docker Compose 支持

## 📋 系统要求

- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- TA-Lib (技术分析库)

## 🛠️ 快速开始

### macOS 环境设置

```bash
# 克隆项目
git clone <repository-url>
cd stock

# 运行自动化设置脚本
chmod +x setup_macos.sh
./setup_macos.sh
```

### 手动安装

1. **安装依赖**
```bash
# 安装 Homebrew (如果未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装系统依赖
brew install postgresql@15 redis ta-lib

# 启动服务
brew services start postgresql@15
brew services start redis
```

2. **设置 Python 环境**
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置必要的配置
# 特别是 TUSHARE_TOKEN
```

4. **初始化数据库**
```bash
# 初始化数据库
./scripts/db_manager.sh init

# 运行数据库迁移
./scripts/db_manager.sh migrate
```

## 🚀 运行应用

### 开发环境

```bash
# 启动开发环境
./start_dev.sh

# 或者分别启动各个服务
python main.py                              # API 服务
./scripts/celery_manager.sh worker          # Celery Worker
./scripts/celery_manager.sh beat            # Celery Beat
./scripts/celery_manager.sh flower          # Flower 监控
```

### 生产环境 (Docker)

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

## 📚 API 文档

启动服务后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## 🔧 管理脚本

### 数据库管理

```bash
./scripts/db_manager.sh init      # 初始化数据库
./scripts/db_manager.sh migrate   # 运行迁移
./scripts/db_manager.sh backup    # 备份数据库
./scripts/db_manager.sh status    # 检查状态
./scripts/db_manager.sh clean     # 清理旧数据
```

### Celery 管理

```bash
./scripts/celery_manager.sh worker   # 启动 Worker
./scripts/celery_manager.sh beat     # 启动 Beat
./scripts/celery_manager.sh flower   # 启动 Flower
./scripts/celery_manager.sh status   # 检查状态
```

## 🧪 测试

```bash
# 运行所有测试
./run_tests.sh

# 或者使用 pytest
pytest tests/ -v --cov=app
```

## 📊 监控

- **Flower (Celery 监控)**: http://localhost:5555
- **系统健康检查**: http://localhost:8080/health
- **WebSocket 测试**: ws://localhost:8080/ws

## 🔄 定时任务

系统包含以下自动化任务：

- **每日 6:00**: 更新股票基础信息
- **工作日 16:00**: 更新日线数据
- **工作日 16:30**: 计算技术指标
- **工作日 17:00**: 计算九转信号
- **每日 2:00**: 清理旧数据
- **每 5 分钟**: 系统健康检查

## 📁 项目结构

```
stock/
├── app/                    # 应用核心代码
│   ├── api.py             # API 路由
│   ├── cache.py           # Redis 缓存
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── data_sources.py    # 数据源管理
│   ├── middleware.py      # 中间件
│   ├── models.py          # 数据模型
│   ├── services.py        # 业务逻辑
│   ├── tasks.py           # Celery 任务
│   ├── technical_analysis.py # 技术分析
│   └── websocket.py       # WebSocket 服务
├── alembic/               # 数据库迁移
├── nginx/                 # Nginx 配置
├── scripts/               # 管理脚本
├── static/                # 静态文件
├── tests/                 # 测试代码
├── docker-compose.yml     # Docker 编排
├── Dockerfile            # Docker 镜像
├── main.py               # 应用入口
└── requirements.txt      # Python 依赖
```

## 🔐 安全配置

1. **环境变量**: 敏感信息通过环境变量配置
2. **CORS**: 配置跨域访问策略
3. **速率限制**: API 请求频率限制
4. **安全头**: HTTP 安全响应头
5. **输入验证**: Pydantic 模型验证

## 🚨 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查 PostgreSQL 状态
   brew services list | grep postgresql
   
   # 重启 PostgreSQL
   brew services restart postgresql@15
   ```

2. **Redis 连接失败**
   ```bash
   # 检查 Redis 状态
   redis-cli ping
   
   # 重启 Redis
   brew services restart redis
   ```

3. **TA-Lib 安装失败**
   ```bash
   # 重新安装 TA-Lib
   brew reinstall ta-lib
   pip install --upgrade --force-reinstall TA-Lib
   ```

4. **权限问题**
   ```bash
   # 给脚本添加执行权限
   chmod +x *.sh scripts/*.sh
   ```

### 日志查看

```bash
# 应用日志
tail -f logs/app.log

# Celery 日志
tail -f logs/celery.log

# Docker 日志
docker-compose logs -f api
```

## 🤝 贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如有问题或建议，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 提交 [Issue](issues)
3. 联系维护者

---

**注意**: 使用本系统前请确保已获得相应的数据源访问权限（如 Tushare Token）。