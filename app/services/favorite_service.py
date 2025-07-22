from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.database.models import UserFavorite, Stock, StockDaily
from app.schemas.favorite import FavoriteCreate, FavoriteUpdate, FavoriteRealtimeData
from app.services.stock_service import StockService

class FavoriteService:
    def __init__(self, db: Session):
        self.db = db
        self.stock_service = StockService(db)

    async def get_user_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户自选股列表"""
        favorites = self.db.query(UserFavorite).filter(
            UserFavorite.user_id == user_id
        ).order_by(desc(UserFavorite.created_at)).all()
        
        result = []
        for favorite in favorites:
            # 获取股票基本信息
            stock = self.db.query(Stock).filter(Stock.ts_code == favorite.ts_code).first()
            
            # 获取最新价格信息
            latest_data = self.db.query(StockDaily).filter(
                StockDaily.ts_code == favorite.ts_code
            ).order_by(desc(StockDaily.trade_date)).first()
            
            favorite_data = {
                "id": favorite.id,
                "user_id": favorite.user_id,
                "ts_code": favorite.ts_code,
                "note": favorite.note,
                "stock_name": stock.name if stock else None,
                "current_price": latest_data.close if latest_data else None,
                "change": latest_data.change if latest_data else None,
                "pct_chg": latest_data.pct_chg if latest_data else None,
                "created_at": favorite.created_at,
                "updated_at": favorite.updated_at
            }
            result.append(favorite_data)
        
        return result

    async def add_favorite(self, user_id: int, favorite_data: FavoriteCreate) -> Dict[str, Any]:
        """添加自选股"""
        # 检查股票是否存在
        stock = self.db.query(Stock).filter(Stock.ts_code == favorite_data.ts_code).first()
        if not stock:
            raise ValueError("股票不存在")
        
        # 检查是否已经添加过
        existing = self.db.query(UserFavorite).filter(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.ts_code == favorite_data.ts_code
            )
        ).first()
        
        if existing:
            raise ValueError("该股票已在自选股中")
        
        # 创建自选股记录
        db_favorite = UserFavorite(
            user_id=user_id,
            ts_code=favorite_data.ts_code,
            note=favorite_data.note
        )
        
        self.db.add(db_favorite)
        self.db.commit()
        self.db.refresh(db_favorite)
        
        # 返回完整信息
        latest_data = self.db.query(StockDaily).filter(
            StockDaily.ts_code == favorite_data.ts_code
        ).order_by(desc(StockDaily.trade_date)).first()
        
        return {
            "id": db_favorite.id,
            "user_id": db_favorite.user_id,
            "ts_code": db_favorite.ts_code,
            "note": db_favorite.note,
            "stock_name": stock.name,
            "current_price": latest_data.close if latest_data else None,
            "change": latest_data.change if latest_data else None,
            "pct_chg": latest_data.pct_chg if latest_data else None,
            "created_at": db_favorite.created_at,
            "updated_at": db_favorite.updated_at
        }

    async def update_favorite(self, favorite_id: int, user_id: int, 
                            favorite_update: FavoriteUpdate) -> Optional[Dict[str, Any]]:
        """更新自选股备注"""
        favorite = self.db.query(UserFavorite).filter(
            and_(
                UserFavorite.id == favorite_id,
                UserFavorite.user_id == user_id
            )
        ).first()
        
        if not favorite:
            return None
        
        # 更新备注
        if favorite_update.note is not None:
            favorite.note = favorite_update.note
        
        favorite.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(favorite)
        
        # 获取股票信息
        stock = self.db.query(Stock).filter(Stock.ts_code == favorite.ts_code).first()
        latest_data = self.db.query(StockDaily).filter(
            StockDaily.ts_code == favorite.ts_code
        ).order_by(desc(StockDaily.trade_date)).first()
        
        return {
            "id": favorite.id,
            "user_id": favorite.user_id,
            "ts_code": favorite.ts_code,
            "note": favorite.note,
            "stock_name": stock.name if stock else None,
            "current_price": latest_data.close if latest_data else None,
            "change": latest_data.change if latest_data else None,
            "pct_chg": latest_data.pct_chg if latest_data else None,
            "created_at": favorite.created_at,
            "updated_at": favorite.updated_at
        }

    async def remove_favorite(self, favorite_id: int, user_id: int) -> bool:
        """删除自选股"""
        favorite = self.db.query(UserFavorite).filter(
            and_(
                UserFavorite.id == favorite_id,
                UserFavorite.user_id == user_id
            )
        ).first()
        
        if not favorite:
            return False
        
        self.db.delete(favorite)
        self.db.commit()
        return True

    async def remove_favorite_by_code(self, user_id: int, ts_code: str) -> bool:
        """根据股票代码删除自选股"""
        favorite = self.db.query(UserFavorite).filter(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.ts_code == ts_code
            )
        ).first()
        
        if not favorite:
            return False
        
        self.db.delete(favorite)
        self.db.commit()
        return True

    async def get_favorites_realtime_data(self, user_id: int) -> List[FavoriteRealtimeData]:
        """获取自选股实时行情"""
        favorites = self.db.query(UserFavorite).filter(
            UserFavorite.user_id == user_id
        ).all()
        
        if not favorites:
            return []
        
        # 获取所有自选股的实时行情
        ts_codes = [fav.ts_code for fav in favorites]
        realtime_quotes = await self.stock_service.get_multiple_realtime_quotes(ts_codes)
        
        # 构建返回数据
        result = []
        favorite_notes = {fav.ts_code: fav.note for fav in favorites}
        
        for quote in realtime_quotes:
            realtime_data = FavoriteRealtimeData(
                ts_code=quote.ts_code,
                name=quote.name,
                note=favorite_notes.get(quote.ts_code),
                price=quote.price,
                change=quote.change,
                pct_chg=quote.pct_chg,
                volume=quote.volume,
                amount=quote.amount,
                high=quote.high,
                low=quote.low,
                open=quote.open,
                pre_close=quote.pre_close,
                timestamp=quote.timestamp
            )
            result.append(realtime_data)
        
        return result

    async def batch_add_favorites(self, user_id: int, stock_codes: List[str]) -> Dict[str, Any]:
        """批量添加自选股"""
        success_count = 0
        failed_codes = []
        
        for ts_code in stock_codes:
            try:
                favorite_data = FavoriteCreate(ts_code=ts_code)
                await self.add_favorite(user_id, favorite_data)
                success_count += 1
            except Exception as e:
                failed_codes.append({"ts_code": ts_code, "error": str(e)})
        
        return {
            "success_count": success_count,
            "failed_count": len(failed_codes),
            "failed_codes": failed_codes,
            "total": len(stock_codes)
        }

    def is_favorite(self, user_id: int, ts_code: str) -> bool:
        """检查是否为自选股"""
        favorite = self.db.query(UserFavorite).filter(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.ts_code == ts_code
            )
        ).first()
        
        return favorite is not None

    def get_favorite_count(self, user_id: int) -> int:
        """获取用户自选股数量"""
        return self.db.query(UserFavorite).filter(
            UserFavorite.user_id == user_id
        ).count()