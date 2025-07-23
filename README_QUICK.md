# 股票交易系统 - 快速启动指南

## 🚀 快速启动（推荐）

### 方法1：一键启动（最简单）

```bash
# 给启动脚本执行权限
chmod +x run_dev.sh

# 启动前端和后端服务
./run_dev.sh
```

启动后访问：
- 🌐 前端页面: http://localhost:3000
- 🔧 后端API: http://localhost:8080
- 📊 指数数据: http://localhost:8080/api/v1/market/indices

### 方法2：分别启动

#### 启动后端API服务器
```bash
python3 simple_api.py
```

#### 启动前端服务器（新终端窗口）
```bash
cd frontend
python3 -m http.server 3000
```

### 方法3：直接打开HTML文件
```bash
# 在浏览器中直接打开
open frontend/standalone.html
```

## 📋 系统要求

- macOS 系统
- Python 3.7+ （通常macOS自带）
- 现代浏览器（Chrome、Safari、Firefox等）

## 🔧 功能特性

### 前端功能
- ✅ 显示A股主要指数
- ✅ 实时数据更新（每30秒）
- ✅ 响应式设计
- ✅ 加载状态显示
- ✅ 错误处理
- ✅ 手动刷新功能

### 后端功能
- ✅ RESTful API
- ✅ CORS支持
- ✅ 模拟实时数据
- ✅ 健康检查端点

## 📊 API接口

### 获取指数数据
```
GET http://localhost:8080/api/v1/market/indices
```

响应示例：
```json
{
  "success": true,
  "data": [
    {
      "code": "000001",
      "name": "上证指数",
      "current_price": 3045.67,
      "change": 12.34,
      "change_percent": 0.41,
      "volume": 234567890,
      "turnover": 287.45,
      "high": 3067.89,
      "low": 3021.45,
      "open": 3033.22,
      "prev_close": 3033.33
    }
  ],
  "timestamp": "2024-01-15T10:30:00",
  "message": "获取指数数据成功"
}
```

### 健康检查
```
GET http://localhost:8080/health
```

## 🛠️ 开发说明

### 项目结构
```
stock/
├── frontend/           # 前端文件
│   ├── index.html     # 主页面
│   ├── styles.css     # 样式文件
│   ├── script.js      # JavaScript逻辑
│   └── standalone.html # 独立版本（包含模拟数据）
├── simple_api.py      # 简化的API服务器
├── run_dev.sh         # 一键启动脚本
└── README_QUICK.md    # 本文件
```

### 自定义配置

#### 修改端口
编辑 `simple_api.py` 文件：
```python
# 修改API服务器端口（默认8080）
start_api_server(port=8080)
```

编辑 `run_dev.sh` 文件：
```bash
# 修改前端服务器端口（默认3000）
python3 -m http.server 3000
```

#### 修改数据
编辑 `simple_api.py` 中的 `handle_indices` 方法来自定义指数数据。

## 🐛 常见问题

### 端口被占用
```bash
# 查看端口占用
lsof -i :8080
lsof -i :3000

# 杀死占用进程
kill -9 <PID>
```

### Python命令不存在
```bash
# 检查Python安装
which python3

# 如果没有安装，使用Homebrew安装
brew install python@3.11
```

### 权限问题
```bash
# 给脚本执行权限
chmod +x run_dev.sh
```

## 🔄 停止服务

在运行 `./run_dev.sh` 的终端中按 `Ctrl+C` 即可停止所有服务。

## 📈 下一步

1. 查看完整的开发环境设置：`SETUP_GUIDE.md`
2. 了解完整的后端API：查看 `app/` 目录
3. 配置真实的数据库和数据源

---

💡 **提示**: 这是一个快速演示版本，使用Python内置服务器和模拟数据。生产环境请使用完整的FastAPI后端和真实数据源。