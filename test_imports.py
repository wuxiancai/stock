#!/usr/bin/env python3
"""
测试所有schema导入是否正常
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/wuxiancai/stock')

def test_imports():
    """测试所有关键导入"""
    try:
        print("🔍 测试schema导入...")
        
        # 测试stock schemas
        from app.schemas.stock import StockResponse, StockDailyResponse, StockListResponse
        print("✅ stock schemas 导入成功")
        
        # 测试user schemas
        from app.schemas.user import UserCreate, UserResponse, UserUpdate
        print("✅ user schemas 导入成功")
        
        # 测试auth schemas
        from app.schemas.auth import Token, TokenData, LoginRequest
        print("✅ auth schemas 导入成功")
        
        # 测试favorite schemas
        from app.schemas.favorite import FavoriteResponse, FavoriteCreate, FavoriteUpdate
        print("✅ favorite schemas 导入成功")
        
        # 测试endpoints导入
        print("\n🔍 测试endpoints导入...")
        from app.api.v1.endpoints import stocks, users, auth, market, analysis, favorites
        print("✅ endpoints 导入成功")
        
        # 测试services导入
        print("\n🔍 测试services导入...")
        from app.services.stock_service import StockService
        from app.services.user_service import UserService
        from app.services.auth_service import AuthService
        from app.services.technical_analysis_service import TechnicalAnalysisService
        print("✅ services 导入成功")
        
        print("\n🎉 所有导入测试通过！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)