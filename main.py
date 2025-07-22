import os
import sys
import uvicorn
import psutil
import socket
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.main import app
from utils.port_manager import PortManager

def main():
    """应用程序入口点"""
    print("🚀 启动股票交易系统...")
    print(f"📊 应用名称: {settings.APP_NAME}")
    print(f"🔢 版本: {settings.APP_VERSION}")
    print(f"🌐 端口: {settings.BACKEND_PORT}")
    
    # 确保端口可用
    port_manager = PortManager(settings.BACKEND_PORT)
    try:
        port_manager.ensure_port_available()
    except Exception as e:
        print(f"❌ 端口管理错误: {e}")
        sys.exit(1)
    
    # 创建日志目录
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    print("✅ 系统检查完成，启动服务...")
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        reload_dirs=[str(project_root / "app")] if settings.DEBUG else None
    )

if __name__ == "__main__":
    main()