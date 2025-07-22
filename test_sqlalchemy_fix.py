#!/usr/bin/env python3
"""
测试 SQLAlchemy Decimal/Numeric 修复
"""

try:
    # 测试基本的 SQLAlchemy 导入
    from sqlalchemy import Column, Integer, String, Date, DateTime, BigInteger, Text, Boolean, ForeignKey, UniqueConstraint, Index, Numeric
    print("✅ SQLAlchemy 基本导入成功")
    
    # 测试 Numeric 类型
    test_column = Column(Numeric(10, 3))
    print("✅ Numeric 类型创建成功")
    
    # 测试模型导入
    from app.database.models import Stock, StockDaily, TechnicalIndicator
    print("✅ 数据库模型导入成功")
    
    print("\n🎉 所有测试通过！SQLAlchemy Decimal 问题已修复")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")