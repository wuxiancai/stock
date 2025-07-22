#!/usr/bin/env python3
"""
股票交易系统后端启动脚本
"""

import os
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.port_manager import PortManager


def main():
    """主启动函数"""
    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # 检查端口是否可用
    port_manager = PortManager()
    if not port_manager.is_port_available(port):
        print(f"端口 {port} 已被占用，正在寻找可用端口...")
        port = port_manager.find_available_port(port)
        print(f"使用端口: {port}")
    
    # 创建必要的目录
    os.makedirs("logs", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    print(f"🚀 启动股票交易系统后端服务...")
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        reload_dirs=["app"] if debug else None,
        log_level="info" if not debug else "debug",
        access_log=True,
        use_colors=True,
    )


if __name__ == "__main__":
    main()