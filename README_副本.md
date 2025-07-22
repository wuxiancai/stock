# 股票交易系统后端

这是一个基于 FastAPI 的股票交易系统后端服务，提供股票数据查询、技术分析、自选股管理等功能。

## 功能特性

- **用户认证与授权**: JWT token 认证，用户注册登录
- **股票数据管理**: 股票基本信息、历史行情数据
- **实时行情**: 获取股票实时价格和行情数据
- **技术分析**: 移动平均线、MACD、RSI、KDJ、布林带等技术指标
- **九转选股**: 九转买卖信号计算和筛选
- **自选股管理**: 添加、删除、查看自选股
- **市场概览**: 市场统计、涨跌榜、成交量榜等
- **行业分析**: 行业表现统计和分析

## 技术栈

- **框架**: FastAPI
- **数据库**: PostgreSQL
- **缓存**: Redis
- **ORM**: SQLAlchemy
- **认证**: JWT
- **数据分析**: Pandas, NumPy
- **数据源**: Tushare, AKShare

## 项目结构

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── api.py              # API路由汇总
│   │       └── endpoints/          # API端点
│   │           ├── auth.py         # 认证相关
│   │           ├── users.py        # 用户管理
│   │           ├── stocks.py       # 股票数据
│   │           ├── market.py       # 市场行情
│   │           ├── analysis.py     # 技术分析
│   │           └── favorites.py    # 自选股
│   ├── core/
│   │   ├── config.py              # 配置管理
│   │   └── exceptions.py          # 异常处理
│   ├── database/
│   │   ├── database.py            # 数据库连接
│   │   ├── models.py              # 数据模型
│   │   └── init_db.py             # 数据库初始化
│   ├── schemas/                   # Pydantic模式
│   ├── services/                  # 业务逻辑服务
│   └── main.py                    # FastAPI应用入口
├── utils/
│   └── port_manager.py            # 端口管理工具
├── main.py                        # 应用启动入口
└── requirements.txt               # 依赖包列表
```

## 安装和运行

### 1. 环境要求

- Python 3.8+
- PostgreSQL 12+
- Redis 6+

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 环境配置

创建 `.env` 文件并配置以下环境变量：

```env
# 应用配置
APP_NAME=股票交易系统
APP_VERSION=1.0.0
DEBUG=true
PORT=8000

# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/stock_db
ASYNC_DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/stock_db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 数据源API配置
TUSHARE_TOKEN=your-tushare-token
```

### 4. 数据库初始化

```bash
# 创建数据库表
python -c "from app.database.init_db import init_database; init_database()"
```

### 5. 启动服务

```bash
# 开发模式
python main.py

# 或使用uvicorn直接启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API 文档

启动服务后，可以通过以下地址访问API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要API端点

### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息
- `POST /api/v1/auth/refresh` - 刷新访问令牌

### 股票数据
- `GET /api/v1/stocks/` - 获取股票列表
- `GET /api/v1/stocks/{ts_code}` - 获取股票详情
- `GET /api/v1/stocks/{ts_code}/history` - 获取历史行情
- `GET /api/v1/stocks/{ts_code}/realtime` - 获取实时行情
- `GET /api/v1/stocks/search` - 搜索股票

### 市场行情
- `GET /api/v1/market/overview` - 市场概览
- `GET /api/v1/market/indices` - 主要指数
- `GET /api/v1/market/hot-stocks` - 热门股票
- `GET /api/v1/market/gainers` - 涨幅榜
- `GET /api/v1/market/losers` - 跌幅榜

### 技术分析
- `GET /api/v1/analysis/nine-turn` - 九转信号
- `POST /api/v1/analysis/nine-turn/calculate` - 计算九转信号
- `POST /api/v1/analysis/nine-turn/screen` - 九转选股
- `GET /api/v1/analysis/technical/{ts_code}` - 技术分析

### 自选股
- `GET /api/v1/favorites/` - 获取自选股列表
- `POST /api/v1/favorites/` - 添加自选股
- `PUT /api/v1/favorites/{favorite_id}` - 更新自选股
- `DELETE /api/v1/favorites/{favorite_id}` - 删除自选股

## 开发说明

### 数据模型

系统包含以下主要数据模型：

- `User`: 用户信息
- `Stock`: 股票基本信息
- `StockDaily`: 股票日线数据
- `TechnicalIndicator`: 技术指标数据
- `NineTurnSignal`: 九转信号数据
- `UserFavorite`: 用户自选股
- `DailyBasic`: 每日基本面数据
- `MoneyFlow`: 资金流向数据

### 服务层

- `AuthService`: 认证服务
- `StockService`: 股票数据服务
- `MarketService`: 市场行情服务
- `TechnicalAnalysisService`: 技术分析服务
- `FavoriteService`: 自选股服务
- `DataSourceService`: 数据源服务

### 配置管理

使用 Pydantic Settings 进行配置管理，支持环境变量和 .env 文件。

## 部署

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

### 生产环境配置

- 使用 Gunicorn + Uvicorn workers
- 配置 Nginx 反向代理
- 设置 SSL 证书
- 配置日志轮转
- 设置监控和告警

## 许可证

MIT License