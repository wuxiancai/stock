# Ubuntu 环境部署指南

## 中文字符显示问题解决方案

在Ubuntu环境下部署股票行情系统时，可能会遇到中文字符显示异常的问题。本文档提供了完整的解决方案。

### 问题现象
- 股票名称显示为股票代码而非中文名称
- "行业"和"地域"字段显示为空
- 数据库中的中文字符乱码

### 解决方案

#### 方法一：自动修复脚本（推荐）

使用提供的自动修复脚本：

```bash
# 运行自动修复脚本
./fix_ubuntu_encoding.sh

# 重新加载环境变量
source ~/.bashrc

# 重启应用程序
python3 app.py
```

#### 方法二：手动配置

如果需要手动配置，请按以下步骤操作：

```bash
# 检查当前locale设置
locale

# 如果没有UTF-8支持，安装语言包
sudo apt-get update
sudo apt-get install language-pack-zh-hans language-pack-en locales

# 生成locale
sudo locale-gen en_US.UTF-8
sudo locale-gen zh_CN.UTF-8

# 设置环境变量
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export PYTHONIOENCODING=utf-8

# 将环境变量添加到 ~/.bashrc
echo 'export LANG=en_US.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=en_US.UTF-8' >> ~/.bashrc
echo 'export PYTHONIOENCODING=utf-8' >> ~/.bashrc

# 重新加载配置
source ~/.bashrc
```

#### 2. Python环境配置

代码中已经包含了以下修复：

- 在`app.py`和`data_sync.py`文件开头添加了UTF-8编码声明
- 设置了环境变量以确保正确处理UTF-8编码
- 配置了Pandas显示选项以正确处理中文字符
- 为SQLite数据库连接添加了`text_factory = str`设置
- 在数据保存时添加了编码处理函数

#### 3. 数据库重新同步

在应用修复后，需要重新同步股票基础信息：

```bash
# 进入项目目录
cd /path/to/your/stock/project

# 重新同步股票基础信息
python3 run.py sync_stock_basic_info

# 验证数据
curl -s "http://localhost:8888/api/favorites" | python3 -m json.tool
```

#### 4. 编码问题诊断

使用提供的编码测试工具进行诊断：

```bash
# 运行编码测试脚本
python3 test_encoding.py
```

该脚本会检查：
- 系统环境变量设置
- Python编码配置
- Tushare API返回的数据编码
- 数据库中存储的数据编码

#### 5. 验证修复效果

1. 检查数据库中的中文字符：
```bash
sqlite3 stock_data.db "SELECT ts_code, name, area, industry FROM stock_basic_info LIMIT 5;"
```

2. 检查API返回的数据：
```bash
curl -s "http://localhost:8888/api/favorites" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))"
```

3. 在浏览器中访问自选股页面，确认中文字符正常显示

### 注意事项

1. **字符编码一致性**：确保从数据获取、处理到存储的整个流程都使用UTF-8编码
2. **环境变量设置**：在系统启动脚本中设置正确的环境变量
3. **数据重新同步**：修复编码问题后必须重新同步数据
4. **日志检查**：注意查看同步过程中的日志，确认没有编码相关的错误

### 常见问题

**Q: 修复后仍然显示乱码怎么办？**
A: 检查系统locale设置，确保安装了中文语言包，并重启应用程序。

**Q: 部分股票显示正常，部分显示异常？**
A: 可能是数据源问题，建议清空数据库后重新同步所有数据。

**Q: 在Docker容器中部署需要注意什么？**
A: 确保Docker镜像包含UTF-8支持，在Dockerfile中设置正确的环境变量。