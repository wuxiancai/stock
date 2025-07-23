# 依赖安装策略文档

## 概述

本项目采用智能依赖安装策略，解决了版本固定导致的安装失败问题，特别是针对 `talib-binary` 等包的版本兼容性问题。

## 安装策略

### 1. 核心依赖（必须安装）

使用最新版本，确保基本功能可用：

```bash
# 核心依赖列表
fastapi          # Web 框架
uvicorn[standard] # ASGI 服务器
sqlalchemy       # ORM 数据库
alembic          # 数据库迁移
redis            # 缓存和消息队列
python-dotenv    # 环境变量管理
```

### 2. 可选依赖（安装失败不影响核心功能）

```bash
# 可选依赖列表
talib-binary     # 技术分析（优先）
pandas           # 数据处理
numpy            # 数值计算
matplotlib       # 图表绘制
plotly           # 交互式图表
yfinance         # 股票数据获取
tushare          # 中国股票数据
```

### 3. 特殊处理

#### talib-binary 安装策略
1. 首先尝试安装 `talib-binary`（预编译版本）
2. 如果失败，回退到 `TA-Lib`（需要系统编译）
3. 如果都失败，跳过技术分析功能

#### Python 3.13 兼容性
- 自动检测 Python 版本
- 对问题包使用 `--no-cache-dir` 参数
- 优先安装最新版本（可能已支持 Python 3.13）

## 安装流程

### 1. 智能 Python 版本选择
```bash
# 优先级顺序
Python 3.12 > 3.11 > 3.10 > 3.9 > 3.13
```

### 2. 分层安装
1. **核心依赖**：必须成功安装
2. **可选依赖**：失败时跳过并继续
3. **其他依赖**：从 requirements.txt 安装剩余包

### 3. 超时和重试机制
- 单个包安装超时：5分钟
- 批量安装超时：10分钟
- 失败时自动切换到逐个安装模式

## 版本管理优势

### 解决的问题
1. **版本不存在**：`talib-binary==0.4.26` 版本不存在
2. **Python 兼容性**：某些固定版本不支持新 Python 版本
3. **安装超时**：大包安装时间过长

### 新策略优势
1. **灵活性**：使用最新兼容版本
2. **容错性**：可选依赖失败不影响核心功能
3. **效率**：智能跳过已安装的包
4. **兼容性**：自动处理 Python 版本差异

## 使用方法

### 自动安装（推荐）
```bash
./setup_macos.sh
```

### 手动安装特定包
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装核心依赖
pip install fastapi uvicorn[standard] sqlalchemy alembic redis python-dotenv

# 尝试安装 talib
pip install talib-binary || pip install TA-Lib

# 安装其他可选依赖
pip install pandas numpy matplotlib plotly yfinance tushare
```

## 故障排除

### talib 安装失败
```bash
# 方法1：安装系统依赖
brew install ta-lib
pip install TA-Lib

# 方法2：跳过技术分析功能
# 系统会自动跳过，不影响其他功能
```

### Python 3.13 兼容性问题
```bash
# 安装 Python 3.12（推荐）
./install_python312.sh

# 或手动安装
brew install python@3.12
```

### 依赖验证
安装完成后，脚本会自动验证：
- ✅ 核心依赖状态
- ✅ 可选功能可用性
- ⚠️ 不可用功能列表

## 配置文件

### requirements.txt（主要文件）
- **已更新**：移除所有版本限制
- **优势**：自动使用最新兼容版本
- **解决问题**：避免版本不存在错误（如 `akshare==1.12.80`）
- **示例**：
  ```
  # 旧版本（固定版本）
  akshare==1.12.80  # ❌ 版本不存在
  talib-binary==0.4.26  # ❌ 版本不存在
  
  # 新版本（灵活版本）
  akshare  # ✅ 自动选择最新版本（如 1.17.25）
  talib-binary  # ✅ 自动选择可用版本
  ```

### requirements.fixed.txt（备份文件）
- **用途**：保留原始固定版本配置
- **使用场景**：需要精确版本控制时
- **注意**：已注释掉不存在的版本
- **使用方法**：`pip install -r requirements.fixed.txt`

### 环境变量
```bash
# Python 3.13 优化
export CFLAGS="-Wno-error=incompatible-function-pointer-types"
export CXXFLAGS="-Wno-error=incompatible-function-pointer-types"
export PIP_NO_BUILD_ISOLATION=1
export PIP_USE_PEP517=0
```

## 最佳实践

1. **优先使用脚本安装**：自动处理所有兼容性问题
2. **定期更新依赖**：使用最新版本获得更好兼容性
3. **检查安装日志**：关注可选依赖的安装状态
4. **测试核心功能**：确保必要依赖正常工作

## 更新日志

- **v2.0**: 引入智能依赖管理
- **v1.9**: 添加 talib-binary 特殊处理
- **v1.8**: 优化 Python 3.13 兼容性
- **v1.7**: 实现分层安装策略