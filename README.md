# 股票选股系统

基于Flask和Tushare的A股股票数据分析系统，提供实时股票数据获取、存储和Web界面展示功能。

## 功能特性

- 🚀 **自动数据同步**: 每天00:30自动同步A股市场所有股票历史日线数据
- 📊 **实时数据展示**: Web界面实时显示股票行情数据
- 🔍 **智能筛选**: 支持股票代码搜索和多维度排序
- 💾 **轻量存储**: 使用SQLite数据库，轻量高效
- 📱 **响应式设计**: 支持PC和移动端访问
- ⚡ **高性能**: 优化的数据结构和查询性能

## 技术栈

- **后端**: Flask + Python 3.7+
- **数据源**: Tushare Pro API
- **数据库**: SQLite
- **前端**: Bootstrap 5 + JavaScript
- **定时任务**: Schedule

## 快速开始

### 1. 环境要求

- Python 3.7 或更高版本
- pip 包管理器
- Tushare Pro账户和Token

### 2. 安装依赖

```bash
# 克隆项目（如果从Git获取）
git clone <repository-url>
cd stock

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 配置Tushare Token

在 `data_sync.py` 文件中，将您的Tushare Token替换为实际的Token：

```python
self.token = '您的Tushare_Token'
```

### 4. 初始化数据库

```bash
python run.py --init
```

### 5. 启动系统

```bash
# 启动Web服务
python run.py

# 或指定端口和主机
python run.py --host 127.0.0.1 --port 8080

# 开启调试模式
python run.py --debug
```

### 6. 访问系统

打开浏览器访问: http://localhost:5000

## 使用指南

### 命令行选项

```bash
# 显示帮助信息
python run.py --help

# 检查依赖包
python run.py --check

# 初始化数据库
python run.py --init

# 手动同步数据
python run.py --sync

# 显示系统信息
python run.py --info

# 启动Web服务（默认）
python run.py
python run.py --host 0.0.0.0 --port 5000
python run.py --debug
```

### Web界面功能

1. **系统状态监控**
   - 股票总数统计
   - 数据总量显示
   - 最新数据日期
   - 系统运行状态

2. **数据筛选和排序**
   - 股票代码/名称搜索
   - 按涨跌幅、成交量、成交额等排序
   - 升序/降序切换

3. **股票数据展示**
   - 实时行情数据表格
   - 涨跌幅颜色标识
   - 数据格式化显示

4. **股票详情查看**
   - 点击查看按钮查看历史数据
   - 30天历史行情展示

5. **数据同步**
   - 手动触发数据同步
   - 同步进度和结果提示

### API接口

系统提供以下REST API接口：

- `GET /api/stocks` - 获取股票列表
- `GET /api/stock/<ts_code>` - 获取单个股票历史数据
- `GET /api/sync` - 手动触发数据同步
- `GET /api/status` - 获取系统状态

## 数据说明

### 数据字段

根据Tushare官方文档，系统获取的股票数据包含以下字段：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| open | float | 开盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| close | float | 收盘价 |
| pre_close | float | 昨收价【除权价，前复权】 |
| change | float | 涨跌额 |
| pct_chg | float | 涨跌幅【基于除权后的昨收计算】 |
| vol | float | 成交量（手） |
| amount | float | 成交额（千元） |

### 数据更新机制

- **自动同步**: 每天00:30执行全量数据同步
- **增量更新**: 每天09:30和15:30同步最新交易日数据
- **手动同步**: 支持通过Web界面或命令行手动触发

## 系统架构

```
股票选股系统/
├── app.py              # Flask主应用
├── data_sync.py        # 数据同步模块
├── scheduler.py        # 定时任务模块
├── run.py             # 启动脚本
├── requirements.txt    # 依赖包列表
├── README.md          # 项目文档
├── stock_data.db      # SQLite数据库（运行时生成）
├── templates/         # HTML模板
│   └── index.html
└── static/           # 静态资源
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## 性能优化

- **数据库索引**: 为常用查询字段创建索引
- **分页加载**: 大数据量时支持分页显示
- **缓存机制**: 合理使用缓存减少API调用
- **异步处理**: 数据同步采用后台异步处理

## 注意事项

1. **Tushare限制**: 请注意Tushare API的调用频率限制
2. **数据延迟**: 股票数据可能存在15-30分钟延迟
3. **存储空间**: 长期运行需要考虑数据库文件大小
4. **网络连接**: 确保服务器能够访问Tushare API

## 故障排除

### 常见问题

1. **依赖包安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Tushare Token错误**
   - 检查Token是否正确
   - 确认Tushare账户状态

3. **数据库权限问题**
   ```bash
   chmod 755 .
   python run.py --init
   ```

4. **端口被占用**
   ```bash
   python run.py --port 8080
   ```

### 日志查看

系统运行日志会输出到控制台，包含：
- 数据同步进度
- API调用状态
- 错误信息
- 系统状态

## 开发计划

- [ ] 添加更多技术指标计算
- [ ] 实现股票筛选策略
- [ ] 添加数据可视化图表
- [ ] 支持多种数据源
- [ ] 实现用户权限管理
- [ ] 添加邮件通知功能

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和Tushare使用条款。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件

---

**免责声明**: 本系统提供的股票数据仅供参考，不构成投资建议。投资有风险，入市需谨慎。