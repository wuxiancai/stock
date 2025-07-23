#!/usr/bin/env python3
"""
简单的 API 启动测试脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试核心模块导入"""
    print("🔍 测试核心模块导入...")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI 导入失败: {e}")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except ImportError as e:
        print(f"❌ Uvicorn 导入失败: {e}")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError as e:
        print(f"❌ SQLAlchemy 导入失败: {e}")
        return False
    
    try:
        import psycopg2
        print(f"✅ psycopg2: {psycopg2.__version__}")
    except ImportError as e:
        print(f"❌ psycopg2 导入失败: {e}")
        return False
    
    return True

def test_app_import():
    """测试应用模块导入"""
    print("\n🔍 测试应用模块导入...")
    
    try:
        from app.api import app
        print("✅ 应用模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 应用模块导入失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 股票交易系统 API 测试")
    print("=" * 40)
    
    # 测试核心依赖
    if not test_imports():
        print("\n❌ 核心依赖测试失败")
        sys.exit(1)
    
    # 测试应用导入
    if not test_app_import():
        print("\n❌ 应用模块测试失败")
        sys.exit(1)
    
    print("\n✅ 所有测试通过！")
    print("🎉 系统已准备就绪，可以启动 API 服务")
    print("\n📋 启动命令:")
    print("  python -m uvicorn app.api:app --host 0.0.0.0 --port 8080 --reload")
    print("\n🔗 服务地址:")
    print("  - API: http://localhost:8080")
    print("  - 文档: http://localhost:8080/docs")

if __name__ == "__main__":
    main()