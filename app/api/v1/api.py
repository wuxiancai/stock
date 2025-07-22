from fastapi import APIRouter
from app.api.v1.endpoints import stocks, users, auth, market, analysis, favorites

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["股票数据"])
api_router.include_router(market.router, prefix="/market", tags=["市场行情"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["技术分析"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["自选股"])