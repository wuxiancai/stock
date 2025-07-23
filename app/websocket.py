"""
WebSocket模块
提供实时数据推送服务
"""

import asyncio
import json
from typing import Dict, List, Set, Any, Optional
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.routing import APIRouter
from loguru import logger
import uuid

from app.data_sources import data_source_manager
from app.services import stock_data_service
from app.cache import StockDataCache
from app.config import settings


# WebSocket路由器
ws_router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接
        self.active_connections: Dict[str, WebSocket] = {}
        # 订阅关系 {connection_id: {subscriptions}}
        self.subscriptions: Dict[str, Set[str]] = {}
        # 股票订阅者 {ts_code: {connection_ids}}
        self.stock_subscribers: Dict[str, Set[str]] = {}
        # 市场数据订阅者
        self.market_subscribers: Set[str] = set()
        # 九转信号订阅者
        self.nine_turn_subscribers: Set[str] = set()
    
    async def connect(self, websocket: WebSocket) -> str:
        """接受WebSocket连接"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()
        
        logger.info(f"WebSocket连接建立: {connection_id}")
        
        # 发送连接成功消息
        await self.send_personal_message(connection_id, {
            "type": "connection",
            "status": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        if connection_id in self.active_connections:
            # 清理订阅关系
            self._cleanup_subscriptions(connection_id)
            
            # 移除连接
            del self.active_connections[connection_id]
            del self.subscriptions[connection_id]
            
            logger.info(f"WebSocket连接断开: {connection_id}")
    
    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """发送个人消息"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"发送消息失败 {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_to_subscribers(self, subscriber_set: Set[str], message: Dict[str, Any]):
        """向订阅者广播消息"""
        if not subscriber_set:
            return
        
        disconnected = set()
        for connection_id in subscriber_set:
            try:
                if connection_id in self.active_connections:
                    websocket = self.active_connections[connection_id]
                    await websocket.send_text(json.dumps(message, ensure_ascii=False))
                else:
                    disconnected.add(connection_id)
            except Exception as e:
                logger.error(f"广播消息失败 {connection_id}: {e}")
                disconnected.add(connection_id)
        
        # 清理断开的连接
        for connection_id in disconnected:
            subscriber_set.discard(connection_id)
    
    async def subscribe_stock(self, connection_id: str, ts_code: str):
        """订阅股票数据"""
        if connection_id not in self.active_connections:
            return False
        
        # 添加订阅关系
        self.subscriptions[connection_id].add(f"stock:{ts_code}")
        
        if ts_code not in self.stock_subscribers:
            self.stock_subscribers[ts_code] = set()
        self.stock_subscribers[ts_code].add(connection_id)
        
        logger.info(f"订阅股票 {ts_code}: {connection_id}")
        
        # 发送确认消息
        await self.send_personal_message(connection_id, {
            "type": "subscription",
            "action": "subscribe",
            "target": "stock",
            "ts_code": ts_code,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def unsubscribe_stock(self, connection_id: str, ts_code: str):
        """取消订阅股票数据"""
        if connection_id not in self.active_connections:
            return False
        
        # 移除订阅关系
        self.subscriptions[connection_id].discard(f"stock:{ts_code}")
        
        if ts_code in self.stock_subscribers:
            self.stock_subscribers[ts_code].discard(connection_id)
            if not self.stock_subscribers[ts_code]:
                del self.stock_subscribers[ts_code]
        
        logger.info(f"取消订阅股票 {ts_code}: {connection_id}")
        
        # 发送确认消息
        await self.send_personal_message(connection_id, {
            "type": "subscription",
            "action": "unsubscribe",
            "target": "stock",
            "ts_code": ts_code,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def subscribe_market(self, connection_id: str):
        """订阅市场数据"""
        if connection_id not in self.active_connections:
            return False
        
        self.subscriptions[connection_id].add("market")
        self.market_subscribers.add(connection_id)
        
        logger.info(f"订阅市场数据: {connection_id}")
        
        await self.send_personal_message(connection_id, {
            "type": "subscription",
            "action": "subscribe",
            "target": "market",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def unsubscribe_market(self, connection_id: str):
        """取消订阅市场数据"""
        if connection_id not in self.active_connections:
            return False
        
        self.subscriptions[connection_id].discard("market")
        self.market_subscribers.discard(connection_id)
        
        logger.info(f"取消订阅市场数据: {connection_id}")
        
        await self.send_personal_message(connection_id, {
            "type": "subscription",
            "action": "unsubscribe",
            "target": "market",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def subscribe_nine_turn(self, connection_id: str):
        """订阅九转信号"""
        if connection_id not in self.active_connections:
            return False
        
        self.subscriptions[connection_id].add("nine_turn")
        self.nine_turn_subscribers.add(connection_id)
        
        logger.info(f"订阅九转信号: {connection_id}")
        
        await self.send_personal_message(connection_id, {
            "type": "subscription",
            "action": "subscribe",
            "target": "nine_turn",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def unsubscribe_nine_turn(self, connection_id: str):
        """取消订阅九转信号"""
        if connection_id not in self.active_connections:
            return False
        
        self.subscriptions[connection_id].discard("nine_turn")
        self.nine_turn_subscribers.discard(connection_id)
        
        logger.info(f"取消订阅九转信号: {connection_id}")
        
        await self.send_personal_message(connection_id, {
            "type": "subscription",
            "action": "unsubscribe",
            "target": "nine_turn",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    def _cleanup_subscriptions(self, connection_id: str):
        """清理连接的所有订阅"""
        if connection_id not in self.subscriptions:
            return
        
        subscriptions = self.subscriptions[connection_id]
        
        for subscription in subscriptions:
            if subscription.startswith("stock:"):
                ts_code = subscription[6:]  # 移除 "stock:" 前缀
                if ts_code in self.stock_subscribers:
                    self.stock_subscribers[ts_code].discard(connection_id)
                    if not self.stock_subscribers[ts_code]:
                        del self.stock_subscribers[ts_code]
            elif subscription == "market":
                self.market_subscribers.discard(connection_id)
            elif subscription == "nine_turn":
                self.nine_turn_subscribers.discard(connection_id)
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self.active_connections)
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """获取订阅统计"""
        return {
            "total_connections": len(self.active_connections),
            "stock_subscriptions": len(self.stock_subscribers),
            "market_subscribers": len(self.market_subscribers),
            "nine_turn_subscribers": len(self.nine_turn_subscribers)
        }


# 全局连接管理器
manager = ConnectionManager()


class DataBroadcaster:
    """数据广播器"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
        self._running = False
        self._tasks = []
    
    async def start(self):
        """启动数据广播"""
        if self._running:
            return
        
        self._running = True
        logger.info("启动WebSocket数据广播服务")
        
        # 启动各种数据推送任务
        self._tasks = [
            asyncio.create_task(self._broadcast_realtime_quotes()),
            asyncio.create_task(self._broadcast_market_data()),
            asyncio.create_task(self._broadcast_nine_turn_signals()),
        ]
    
    async def stop(self):
        """停止数据广播"""
        if not self._running:
            return
        
        self._running = False
        logger.info("停止WebSocket数据广播服务")
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
    
    async def _broadcast_realtime_quotes(self):
        """广播实时行情"""
        while self._running:
            try:
                if not self.manager.stock_subscribers:
                    await asyncio.sleep(5)
                    continue
                
                # 获取实时行情数据
                df = await data_source_manager.get_realtime_quotes(use_cache=True)
                
                if not df.empty:
                    # 为每个订阅的股票发送数据
                    for ts_code, subscribers in self.manager.stock_subscribers.items():
                        if not subscribers:
                            continue
                        
                        # 查找对应股票的数据
                        stock_data = df[df['代码'] == ts_code.split('.')[0]] if '代码' in df.columns else pd.DataFrame()
                        
                        if not stock_data.empty:
                            row = stock_data.iloc[0]
                            message = {
                                "type": "realtime_quote",
                                "ts_code": ts_code,
                                "data": {
                                    "name": row.get('名称', ''),
                                    "price": row.get('最新价', 0),
                                    "change": row.get('涨跌额', 0),
                                    "pct_chg": row.get('涨跌幅', 0),
                                    "volume": row.get('成交量', 0),
                                    "amount": row.get('成交额', 0),
                                    "high": row.get('最高', 0),
                                    "low": row.get('最低', 0),
                                    "open": row.get('今开', 0),
                                    "pre_close": row.get('昨收', 0),
                                },
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            await self.manager.broadcast_to_subscribers(subscribers, message)
                
                await asyncio.sleep(3)  # 每3秒更新一次
                
            except Exception as e:
                logger.error(f"广播实时行情失败: {e}")
                await asyncio.sleep(10)
    
    async def _broadcast_market_data(self):
        """广播市场数据"""
        while self._running:
            try:
                if not self.manager.market_subscribers:
                    await asyncio.sleep(30)
                    continue
                
                # 获取市场情绪数据
                sentiment_data = await data_source_manager.get_market_sentiment()
                
                # 获取热门股票
                hot_stocks = await data_source_manager.get_hot_stocks("volume")
                
                message = {
                    "type": "market_data",
                    "data": {
                        "sentiment": {
                            "limit_up_count": len(sentiment_data.get("limit_up", [])),
                            "limit_down_count": len(sentiment_data.get("limit_down", [])),
                            "strong_stocks_count": len(sentiment_data.get("strong_stocks", [])),
                            "new_stocks_count": len(sentiment_data.get("new_stocks", [])),
                        },
                        "hot_stocks": hot_stocks.head(10).to_dict('records') if not hot_stocks.empty else [],
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.manager.broadcast_to_subscribers(
                    self.manager.market_subscribers, 
                    message
                )
                
                await asyncio.sleep(60)  # 每分钟更新一次
                
            except Exception as e:
                logger.error(f"广播市场数据失败: {e}")
                await asyncio.sleep(60)
    
    async def _broadcast_nine_turn_signals(self):
        """广播九转信号"""
        while self._running:
            try:
                if not self.manager.nine_turn_subscribers:
                    await asyncio.sleep(300)
                    continue
                
                # 获取最新九转信号
                signals = await stock_data_service.get_nine_turn_stocks(
                    signal_type="all",
                    days=1,
                    limit=20
                )
                
                if signals:
                    message = {
                        "type": "nine_turn_signals",
                        "data": signals,
                        "count": len(signals),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await self.manager.broadcast_to_subscribers(
                        self.manager.nine_turn_subscribers,
                        message
                    )
                
                await asyncio.sleep(300)  # 每5分钟检查一次
                
            except Exception as e:
                logger.error(f"广播九转信号失败: {e}")
                await asyncio.sleep(300)


# 全局数据广播器
broadcaster = DataBroadcaster(manager)


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    connection_id = await manager.connect(websocket)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(connection_id, message)
            except json.JSONDecodeError:
                await manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": "无效的JSON格式",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
                await manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": "处理消息失败",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
        manager.disconnect(connection_id)


async def handle_websocket_message(connection_id: str, message: Dict[str, Any]):
    """处理WebSocket消息"""
    message_type = message.get("type")
    action = message.get("action")
    
    if message_type == "subscription":
        target = message.get("target")
        
        if target == "stock":
            ts_code = message.get("ts_code")
            if not ts_code:
                await manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": "缺少股票代码",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            if action == "subscribe":
                await manager.subscribe_stock(connection_id, ts_code)
            elif action == "unsubscribe":
                await manager.unsubscribe_stock(connection_id, ts_code)
        
        elif target == "market":
            if action == "subscribe":
                await manager.subscribe_market(connection_id)
            elif action == "unsubscribe":
                await manager.unsubscribe_market(connection_id)
        
        elif target == "nine_turn":
            if action == "subscribe":
                await manager.subscribe_nine_turn(connection_id)
            elif action == "unsubscribe":
                await manager.unsubscribe_nine_turn(connection_id)
        
        else:
            await manager.send_personal_message(connection_id, {
                "type": "error",
                "message": f"不支持的订阅目标: {target}",
                "timestamp": datetime.now().isoformat()
            })
    
    elif message_type == "ping":
        # 心跳检测
        await manager.send_personal_message(connection_id, {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
    
    elif message_type == "get_stats":
        # 获取统计信息
        stats = manager.get_subscription_stats()
        await manager.send_personal_message(connection_id, {
            "type": "stats",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        })
    
    else:
        await manager.send_personal_message(connection_id, {
            "type": "error",
            "message": f"不支持的消息类型: {message_type}",
            "timestamp": datetime.now().isoformat()
        })


# 启动和停止函数
async def start_websocket_service():
    """启动WebSocket服务"""
    await broadcaster.start()


async def stop_websocket_service():
    """停止WebSocket服务"""
    await broadcaster.stop()


# 导出
__all__ = [
    "ws_router",
    "manager",
    "broadcaster",
    "start_websocket_service",
    "stop_websocket_service",
]