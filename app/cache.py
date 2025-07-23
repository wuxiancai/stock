"""
Redis缓存管理模块
支持异步操作和连接池
"""

import json
import pickle
from typing import Any, Optional, Union, List, Dict
from datetime import timedelta
import aioredis
from aioredis import Redis
from loguru import logger

from app.config import settings, RedisConfig

# Redis连接实例
redis_client: Optional[Redis] = None


async def init_redis():
    """初始化Redis连接"""
    global redis_client
    
    try:
        redis_client = aioredis.from_url(
            settings.redis_url,
            **RedisConfig.get_connection_config()
        )
        
        # 测试连接
        await redis_client.ping()
        logger.info("Redis连接初始化成功")
        
    except Exception as e:
        logger.error(f"Redis连接初始化失败: {e}")
        raise


async def close_redis():
    """关闭Redis连接"""
    global redis_client
    
    try:
        if redis_client:
            await redis_client.close()
            logger.info("Redis连接已关闭")
    except Exception as e:
        logger.error(f"关闭Redis连接时出错: {e}")


class CacheManager:
    """缓存管理器"""
    
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """获取缓存值"""
        if not redis_client:
            return None
        
        try:
            value = await redis_client.get(key)
            if value is None:
                return None
            
            # 尝试JSON解析，失败则返回原始字符串
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    @staticmethod
    async def set(
        key: str, 
        value: Any, 
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """设置缓存值"""
        if not redis_client:
            return False
        
        try:
            # 序列化值
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, (int, float, str, bool)):
                serialized_value = json.dumps(value)
            else:
                # 对于复杂对象使用pickle
                serialized_value = pickle.dumps(value)
            
            # 设置过期时间
            if expire is None:
                expire = settings.cache_ttl_seconds
            
            await redis_client.set(key, serialized_value, ex=expire)
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    @staticmethod
    async def delete(key: str) -> bool:
        """删除缓存"""
        if not redis_client:
            return False
        
        try:
            result = await redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    @staticmethod
    async def exists(key: str) -> bool:
        """检查缓存是否存在"""
        if not redis_client:
            return False
        
        try:
            result = await redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {e}")
            return False
    
    @staticmethod
    async def expire(key: str, seconds: int) -> bool:
        """设置缓存过期时间"""
        if not redis_client:
            return False
        
        try:
            result = await redis_client.expire(key, seconds)
            return result
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 {key}: {e}")
            return False
    
    @staticmethod
    async def ttl(key: str) -> int:
        """获取缓存剩余时间"""
        if not redis_client:
            return -1
        
        try:
            return await redis_client.ttl(key)
        except Exception as e:
            logger.error(f"获取缓存TTL失败 {key}: {e}")
            return -1
    
    @staticmethod
    async def keys(pattern: str) -> List[str]:
        """获取匹配的键列表"""
        if not redis_client:
            return []
        
        try:
            keys = await redis_client.keys(pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.error(f"获取键列表失败 {pattern}: {e}")
            return []
    
    @staticmethod
    async def clear_pattern(pattern: str) -> int:
        """清除匹配模式的所有缓存"""
        if not redis_client:
            return 0
        
        try:
            keys = await CacheManager.keys(pattern)
            if keys:
                return await redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"清除缓存模式失败 {pattern}: {e}")
            return 0
    
    @staticmethod
    async def increment(key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not redis_client:
            return 0
        
        try:
            return await redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"递增计数器失败 {key}: {e}")
            return 0
    
    @staticmethod
    async def decrement(key: str, amount: int = 1) -> int:
        """递减计数器"""
        if not redis_client:
            return 0
        
        try:
            return await redis_client.decrby(key, amount)
        except Exception as e:
            logger.error(f"递减计数器失败 {key}: {e}")
            return 0


class StockDataCache:
    """股票数据专用缓存"""
    
    # 缓存键前缀
    STOCK_BASIC_PREFIX = "stock:basic:"
    DAILY_QUOTE_PREFIX = "stock:quote:"
    TECHNICAL_INDICATOR_PREFIX = "stock:indicator:"
    NINE_TURN_SIGNAL_PREFIX = "stock:nine_turn:"
    MARKET_DATA_PREFIX = "market:data:"
    REALTIME_QUOTE_PREFIX = "realtime:quote:"
    
    @staticmethod
    def _get_stock_key(prefix: str, ts_code: str, date: str = None) -> str:
        """生成股票缓存键"""
        if date:
            return f"{prefix}{ts_code}:{date}"
        return f"{prefix}{ts_code}"
    
    @staticmethod
    async def get_stock_basic(ts_code: str) -> Optional[Dict]:
        """获取股票基础信息缓存"""
        key = StockDataCache._get_stock_key(StockDataCache.STOCK_BASIC_PREFIX, ts_code)
        return await CacheManager.get(key)
    
    @staticmethod
    async def set_stock_basic(ts_code: str, data: Dict, expire: int = 3600) -> bool:
        """设置股票基础信息缓存"""
        key = StockDataCache._get_stock_key(StockDataCache.STOCK_BASIC_PREFIX, ts_code)
        return await CacheManager.set(key, data, expire)
    
    @staticmethod
    async def get_daily_quote(ts_code: str, date: str) -> Optional[Dict]:
        """获取日线行情缓存"""
        key = StockDataCache._get_stock_key(StockDataCache.DAILY_QUOTE_PREFIX, ts_code, date)
        return await CacheManager.get(key)
    
    @staticmethod
    async def set_daily_quote(ts_code: str, date: str, data: Dict, expire: int = 1800) -> bool:
        """设置日线行情缓存"""
        key = StockDataCache._get_stock_key(StockDataCache.DAILY_QUOTE_PREFIX, ts_code, date)
        return await CacheManager.set(key, data, expire)
    
    @staticmethod
    async def get_realtime_quote(ts_code: str) -> Optional[Dict]:
        """获取实时行情缓存"""
        key = StockDataCache._get_stock_key(StockDataCache.REALTIME_QUOTE_PREFIX, ts_code)
        return await CacheManager.get(key)
    
    @staticmethod
    async def set_realtime_quote(ts_code: str, data: Dict, expire: int = 60) -> bool:
        """设置实时行情缓存"""
        key = StockDataCache._get_stock_key(StockDataCache.REALTIME_QUOTE_PREFIX, ts_code)
        return await CacheManager.set(key, data, expire)
    
    @staticmethod
    async def get_technical_indicators(ts_code: str, date: str) -> Optional[Dict]:
        """获取技术指标缓存"""
        key = StockDataCache._get_stock_key(StockDataCache.TECHNICAL_INDICATOR_PREFIX, ts_code, date)
        return await CacheManager.get(key)
    
    @staticmethod
    async def set_technical_indicators(ts_code: str, date: str, data: Dict, expire: int = 1800) -> bool:
        """设置技术指标缓存"""
        key = StockDataCache._get_stock_key(StockDataCache.TECHNICAL_INDICATOR_PREFIX, ts_code, date)
        return await CacheManager.set(key, data, expire)
    
    @staticmethod
    async def get_nine_turn_signals(ts_code: str, date: str = None) -> Optional[Dict]:
        """获取九转信号缓存"""
        if date:
            key = StockDataCache._get_stock_key(StockDataCache.NINE_TURN_SIGNAL_PREFIX, ts_code, date)
        else:
            key = f"{StockDataCache.NINE_TURN_SIGNAL_PREFIX}{ts_code}:latest"
        return await CacheManager.get(key)
    
    @staticmethod
    async def set_nine_turn_signals(ts_code: str, data: Dict, date: str = None, expire: int = 900) -> bool:
        """设置九转信号缓存"""
        if date:
            key = StockDataCache._get_stock_key(StockDataCache.NINE_TURN_SIGNAL_PREFIX, ts_code, date)
        else:
            key = f"{StockDataCache.NINE_TURN_SIGNAL_PREFIX}{ts_code}:latest"
        return await CacheManager.set(key, data, expire)
    
    @staticmethod
    async def clear_stock_cache(ts_code: str) -> int:
        """清除指定股票的所有缓存"""
        patterns = [
            f"{StockDataCache.STOCK_BASIC_PREFIX}{ts_code}*",
            f"{StockDataCache.DAILY_QUOTE_PREFIX}{ts_code}*",
            f"{StockDataCache.TECHNICAL_INDICATOR_PREFIX}{ts_code}*",
            f"{StockDataCache.NINE_TURN_SIGNAL_PREFIX}{ts_code}*",
            f"{StockDataCache.REALTIME_QUOTE_PREFIX}{ts_code}*",
        ]
        
        total_cleared = 0
        for pattern in patterns:
            cleared = await CacheManager.clear_pattern(pattern)
            total_cleared += cleared
        
        return total_cleared
    
    @staticmethod
    async def health_check() -> Dict[str, Any]:
        """股票数据缓存健康检查"""
        try:
            # 检查Redis连接
            redis_healthy = await RedisHealthCheck.check_connection()
            
            if not redis_healthy:
                return {
                    "status": "unhealthy",
                    "redis_connection": False,
                    "error": "Redis连接失败"
                }
            
            # 获取Redis信息
            redis_info = await RedisHealthCheck.get_info()
            
            # 检查缓存键数量
            cache_stats = {}
            for prefix in [
                StockDataCache.STOCK_BASIC_PREFIX,
                StockDataCache.DAILY_QUOTE_PREFIX,
                StockDataCache.TECHNICAL_INDICATOR_PREFIX,
                StockDataCache.NINE_TURN_SIGNAL_PREFIX,
                StockDataCache.REALTIME_QUOTE_PREFIX
            ]:
                keys = await CacheManager.keys(f"{prefix}*")
                cache_stats[prefix.rstrip(":")] = len(keys)
            
            return {
                "status": "healthy",
                "redis_connection": True,
                "redis_info": redis_info,
                "cache_stats": cache_stats
            }
            
        except Exception as e:
            logger.error(f"股票数据缓存健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "redis_connection": False,
                "error": str(e)
            }


class RateLimitCache:
    """限流缓存"""
    
    @staticmethod
    async def check_rate_limit(key: str, limit: int, window: int) -> bool:
        """检查是否超过限流"""
        if not redis_client:
            return True  # 如果Redis不可用，允许通过
        
        try:
            current = await redis_client.get(key)
            if current is None:
                await redis_client.setex(key, window, 1)
                return True
            
            current_count = int(current)
            if current_count >= limit:
                return False
            
            await redis_client.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"检查限流失败 {key}: {e}")
            return True  # 出错时允许通过
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """检查是否允许请求（与check_rate_limit相同的逻辑）"""
        return await self.check_rate_limit(key, limit, window)
    
    async def get_reset_time(self, key: str, window: int) -> int:
        """获取限流重置时间"""
        if not redis_client:
            return window
        
        try:
            ttl = await redis_client.ttl(key)
            if ttl > 0:
                return ttl
            return window
        except Exception as e:
            logger.error(f"获取重置时间失败 {key}: {e}")
            return window
    
    async def get_current_usage(self, key: str) -> int:
        """获取当前使用次数"""
        if not redis_client:
            return 0
        
        try:
            current = await redis_client.get(key)
            return int(current) if current else 0
        except Exception as e:
            logger.error(f"获取当前使用次数失败 {key}: {e}")
            return 0


class RedisHealthCheck:
    """Redis健康检查"""
    
    @staticmethod
    async def check_connection() -> bool:
        """检查Redis连接"""
        if not redis_client:
            return False
        
        try:
            await redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis连接检查失败: {e}")
            return False
    
    @staticmethod
    async def get_info() -> Dict:
        """获取Redis信息"""
        if not redis_client:
            return {}
        
        try:
            info = await redis_client.info()
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            }
        except Exception as e:
            logger.error(f"获取Redis信息失败: {e}")
            return {}


# 导出
__all__ = [
    "init_redis",
    "close_redis",
    "CacheManager",
    "StockDataCache",
    "RateLimitCache",
    "RedisHealthCheck",
    "redis_client",
]