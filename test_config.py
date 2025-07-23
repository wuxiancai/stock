#!/usr/bin/env python3
"""
测试配置加载是否正常
"""

try:
    print("🔍 测试配置加载...")
    from app.config import settings
    print("✅ 配置加载成功!")
    print(f"📱 应用名称: {settings.app_name}")
    print(f"🌍 环境: {settings.environment}")
    print(f"🔧 调试模式: {settings.debug}")
    print(f"🗄️ 数据库URL: {settings.database_url[:50]}...")
    print("🎉 所有配置项加载正常!")
    
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    import traceback
    traceback.print_exc()