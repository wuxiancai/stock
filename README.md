# 股票交易系统

一个功能完整的股票交易系统，提供股票数据获取、技术分析、自选股管理等功能。

## 🚀 快速开始

### 方式一：本地部署（推荐开发）
```bash
# 一键部署
bash deploy.sh

# 启动应用
python3 main.py
```

### 方式二：Docker部署（推荐生产）
```bash
# 一键Docker部署
bash start_docker.sh
```

就这么简单！

## 📖 访问地址

- **应用首页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Docker部署**: http://localhost

## ⚙️ 配置说明

部署后会自动创建 `.env` 文件，根据需要修改以下配置：

```env
# 数据库连接（必须配置）
DATABASE_URL=postgresql://postgres:password@localhost:5432/stock_db

# Redis连接
REDIS_URL=redis://localhost:6379/0

# 数据源API（可选）
TUSHARE_TOKEN=your_token_here
```

## 🛠️ 管理命令

### 本地部署
```bash
# 重新部署
bash deploy.sh

# 启动应用
python3 main.py

# 查看日志
tail -f logs/app.log
```

### Docker部署
```bash
# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart

# 停止服务
docker-compose down
```

## 📋 功能特性

### 🔐 用户系统
- 用户注册、登录、JWT认证
- 用户权限管理
- 个人信息管理

### 📊 股票数据
- 股票基本信息查询
- 实时行情数据
- 历史K线数据
- 股票搜索功能

### 📈 技术分析
- 移动平均线（MA、EMA）
- MACD、RSI、KDJ指标
- 布林带（Bollinger Bands）
- 九转买卖信号
- 支撑阻力位分析

### ⭐ 自选股管理
- 添加/删除自选股
- 自选股实时行情
- 自选股技术分析
- 批量操作

### 🏪 市场行情
- 市场概览
- 涨跌幅排行榜
- 成交量/成交额排行
- 行业表现分析
- 资金流向统计

### 🔍 选股功能
- 九转信号选股
- 自定义条件选股
- 技术形态识别
- 多维度筛选

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL
- **缓存**: Redis
- **ORM**: SQLAlchemy
- **认证**: JWT
- **数据分析**: Pandas, NumPy

### 数据源
- **Tushare**: 专业金融数据接口
- **AKShare**: 开源财经数据接口

### 部署
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **进程管理**: Uvicorn

## 📁 项目结构

```
stock/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API路由
│   │   ├── core/              # 核心配置
│   │   ├── database/          # 数据库相关
│   │   ├── schemas/           # 数据模型
│   │   └── services/          # 业务逻辑
│   ├── utils/                 # 工具函数
│   ├── main.py               # 应用入口
│   ├── start.py              # 启动脚本
│   ├── deploy.sh             # 部署脚本
│   ├── Dockerfile            # Docker配置
│   └── requirements.txt      # 依赖包
├── docker-compose.yml         # Docker编排
├── start.sh                  # 快速启动脚本
├── init.sql                  # 数据库初始化
├── .env.example              # 环境变量示例
└── README.md                 # 项目说明
```

## ⚙️ 配置说明

### 环境变量

复制 `.env.example` 为 `.env` 并配置以下关键参数：

```env
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/stock_db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT密钥（生产环境必须修改）
SECRET_KEY=your-secret-key-here

# 数据源API Token
TUSHARE_TOKEN=your_tushare_token_here
```

### 数据源配置

1. **Tushare Token**: 
   - 注册 [Tushare](https://tushare.pro/) 账户
   - 获取API Token
   - 配置到环境变量 `TUSHARE_TOKEN`

2. **AKShare**: 
   - 无需注册，开箱即用
   - 部分接口有频率限制

## 🔧 开发指南

### 本地开发

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env
# 编辑 .env 文件

# 启动数据库和Redis（使用Docker）
docker-compose up postgres redis -d

# 初始化数据库
python -c "from app.database.init_db import init_database; init_database()"

# 启动开发服务器
python start.py
```

### API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 数据库管理

```bash
# 查看数据库状态
docker-compose exec postgres psql -U stock_user -d stock_db

# 备份数据库
docker-compose exec postgres pg_dump -U stock_user stock_db > backup.sql

# 恢复数据库
docker-compose exec -T postgres psql -U stock_user -d stock_db < backup.sql
```

## 📊 API接口

### 认证接口
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取用户信息

### 股票接口
- `GET /api/v1/stocks/` - 股票列表
- `GET /api/v1/stocks/{ts_code}` - 股票详情
- `GET /api/v1/stocks/{ts_code}/history` - 历史数据
- `GET /api/v1/stocks/search` - 股票搜索

### 市场接口
- `GET /api/v1/market/overview` - 市场概览
- `GET /api/v1/market/gainers` - 涨幅榜
- `GET /api/v1/market/losers` - 跌幅榜

### 分析接口
- `GET /api/v1/analysis/nine-turn` - 九转信号
- `POST /api/v1/analysis/nine-turn/screen` - 九转选股
- `GET /api/v1/analysis/technical/{ts_code}` - 技术分析

### 自选股接口
- `GET /api/v1/favorites/` - 自选股列表
- `POST /api/v1/favorites/` - 添加自选股
- `DELETE /api/v1/favorites/{id}` - 删除自选股

## 🚀 部署指南

### Docker部署（推荐）

```bash
# 使用快速启动脚本
./start.sh

# 或手动启动
docker-compose up -d
```

### 生产环境部署

1. **配置环境变量**
   ```bash
   # 修改生产环境配置
   cp .env.example .env
   # 编辑 .env，设置生产环境参数
   ```

2. **配置SSL证书**
   ```bash
   # 将SSL证书放到 nginx/ssl/ 目录
   mkdir -p nginx/ssl
   # 修改 nginx/nginx.conf 启用HTTPS
   ```

3. **启动服务**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### 监控和维护

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart backend

# 更新服务
docker-compose pull
docker-compose up -d
```

## 🔒 安全注意事项

1. **修改默认密钥**: 生产环境必须修改 `SECRET_KEY`
2. **数据库安全**: 使用强密码，限制访问权限
3. **API限流**: 配置合适的请求频率限制
4. **HTTPS**: 生产环境启用SSL证书
5. **防火墙**: 只开放必要的端口

## 📝 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 完整的股票数据查询功能
- 技术分析指标计算
- 九转选股功能
- 用户认证和自选股管理

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目地址: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 邮箱: your-email@example.com

## 🙏 致谢

- [Tushare](https://tushare.pro/) - 专业的金融数据接口
- [AKShare](https://github.com/akfamily/akshare) - 开源财经数据接口
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架