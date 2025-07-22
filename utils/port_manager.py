import os
import signal
import psutil
import socket
from typing import Optional

class PortManager:
    """端口管理器，用于处理端口占用问题"""
    
    def __init__(self, port: int = 8080):
        self.port = port
    
    def is_port_in_use(self) -> bool:
        """检查端口是否被占用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', self.port)) == 0
    
    def get_process_on_port(self) -> Optional[psutil.Process]:
        """获取占用端口的进程"""
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                connections = proc.info.get('connections')
                if connections:
                    for conn in connections:
                        if hasattr(conn, 'laddr') and conn.laddr.port == self.port:
                            return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None
    
    def kill_process_on_port(self) -> bool:
        """终结占用端口的进程"""
        process = self.get_process_on_port()
        if process:
            try:
                print(f"🔄 发现进程 {process.pid} ({process.name()}) 占用端口 {self.port}")
                process.terminate()
                
                # 等待进程优雅退出
                try:
                    process.wait(timeout=5)
                    print(f"✅ 进程 {process.pid} 已优雅退出")
                except psutil.TimeoutExpired:
                    # 强制杀死进程
                    process.kill()
                    print(f"⚡ 强制终结进程 {process.pid}")
                
                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"❌ 无法终结进程: {e}")
                return False
        return False
    
    def ensure_port_available(self) -> None:
        """确保端口可用"""
        if not self.is_port_in_use():
            print(f"✅ 端口 {self.port} 可用")
            return
        
        print(f"⚠️  端口 {self.port} 被占用，正在释放...")
        
        if self.kill_process_on_port():
            # 再次检查端口是否已释放
            if not self.is_port_in_use():
                print(f"✅ 端口 {self.port} 已成功释放")
            else:
                raise Exception(f"端口 {self.port} 仍被占用，无法释放")
        else:
            raise Exception(f"无法释放端口 {self.port}")
    
    def get_alternative_port(self, start_port: int = None) -> int:
        """获取可用的替代端口"""
        if start_port is None:
            start_port = self.port + 1
        
        for port in range(start_port, start_port + 100):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        
        raise Exception("无法找到可用的替代端口")