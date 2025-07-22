#!/usr/bin/env python3
"""
简单的 SQLAlchemy 导入测试
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, '/Users/wuxiancai/stock')

try:
    print("🔍 开始测试 SQLAlchemy 导入...")
    
    # 测试基本的 SQLAlchemy 导入
    from sqlalchemy import Numeric
    print("✅ SQLAlchemy Numeric 导入成功")
    
    # 测试模型导入
    from app.database.models import Stock
    print("✅ Stock 模型导入成功")
    
    from app.database.models import StockDaily
    print("✅ StockDaily 模型导入成功")
    
    from app.database.models import TechnicalIndicator
    print("✅ TechnicalIndicator 模型导入成功")
    
    print("\n🎉 所有测试通过！SQLAlchemy Decimal 问题已修复")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 其他错误: {e}")
    sys.exit(1)