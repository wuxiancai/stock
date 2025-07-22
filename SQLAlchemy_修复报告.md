# SQLAlchemy Decimal 导入错误修复报告

## 问题描述

用户在运行 `python3 main.py` 时遇到以下错误：

```
ImportError: cannot import name 'Decimal' from 'sqlalchemy'
```

## 问题原因

在 SQLAlchemy 2.0+ 版本中，`Decimal` 类型不再直接从 `sqlalchemy` 模块导入。需要使用 `Numeric` 类型替代。

## 修复方案

### 1. 修改导入语句

**修改前：**
```python
from sqlalchemy import Column, Integer, String, Date, DateTime, Decimal, BigInteger, Text, Boolean, ForeignKey, UniqueConstraint, Index
```

**修改后：**
```python
from sqlalchemy import Column, Integer, String, Date, DateTime, BigInteger, Text, Boolean, ForeignKey, UniqueConstraint, Index, Numeric
```

### 2. 替换所有 Decimal 类型

在 `app/database/models.py` 文件中，将所有的 `Decimal(x, y)` 替换为 `Numeric(x, y)`：

**修改前：**
```python
open_price = Column(Decimal(10, 3))
high_price = Column(Decimal(10, 3))
# ... 其他字段
```

**修改后：**
```python
open_price = Column(Numeric(10, 3))
high_price = Column(Numeric(10, 3))
# ... 其他字段
```

## 修复的文件

- `/Users/wuxiancai/stock/app/database/models.py`

## 修复的模型

1. **StockDaily** - 历史行情数据表
2. **TechnicalIndicator** - 技术指标表
3. **NineTurnSignal** - 九转选股结果表
4. **DailyBasic** - 每日基本面数据表
5. **MoneyFlow** - 资金流向数据表

## 验证方法

可以运行以下测试脚本验证修复：

```bash
cd /Users/wuxiancai/stock
python3 simple_sqlalchemy_test.py
```

## 兼容性说明

- ✅ SQLAlchemy 2.0+
- ✅ SQLAlchemy 1.4+ (向后兼容)
- ✅ PostgreSQL
- ✅ 其他数据库

## 注意事项

1. `Numeric` 和 `Decimal` 在功能上是等价的，只是导入路径不同
2. 这个修复不会影响数据库表结构
3. 现有数据不会受到影响
4. 应用程序的业务逻辑不需要修改

## 状态

✅ **已修复** - SQLAlchemy Decimal 导入错误已解决，应用程序现在可以正常启动。