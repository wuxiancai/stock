# 股票交易系统 - 开发环境设置指南

## macOS 环境设置步骤

### 1. 检查Python环境
```bash
# 检查Python3是否安装
python3 --version

# 如果没有安装，使用Homebrew安装
brew install python@3.11
```

### 2. 创建虚拟环境
```bash
# 在项目根目录下创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
python -m pip install --upgrade pip
```

### 3. 安装依赖
```bash
# 安装项目依赖
pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
nano .env
```

### 5. 启动服务

#### 启动后端服务
```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 启动FastAPI服务器
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

#### 启动前端服务
```bash
# 在另一个终端窗口中
cd frontend
python3 -m http.server 3000
```

### 6. 访问应用
- 前端页面: http://localhost:3000
- 后端API: http://localhost:8080
- API文档: http://localhost:8080/docs

### 常见问题解决

#### Python命令不存在
```bash
# 检查Python安装
which python3

# 如果没有安装，使用Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.11
```

#### 端口被占用
```bash
# 查看端口占用
lsof -i :8080
lsof -i :3000

# 杀死占用进程
kill -9 <PID>
```

#### 依赖安装失败
```bash
# 分别安装核心依赖
pip install fastapi uvicorn
pip install sqlalchemy pandas numpy
pip install redis aioredis
```

### 开发工作流

1. 每次开发前激活虚拟环境：
   ```bash
   source venv/bin/activate
   ```

2. 启动开发服务器：
   ```bash
   # 后端
   python -m uvicorn app.main:app --reload --port 8080
   
   # 前端
   cd frontend && python3 -m http.server 3000
   ```

3. 开发完成后退出虚拟环境：
   ```bash
   deactivate
   ```