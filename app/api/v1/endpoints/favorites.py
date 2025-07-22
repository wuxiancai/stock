from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.schemas.favorite import FavoriteResponse, FavoriteCreate, FavoriteUpdate
from app.services.favorite_service import FavoriteService
from app.api.v1.endpoints.auth import oauth2_scheme
from app.services.auth_service import AuthService

router = APIRouter()

@router.get("/", response_model=List[FavoriteResponse])
async def get_user_favorites(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取用户自选股列表"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        favorite_service = FavoriteService(db)
        favorites = await favorite_service.get_user_favorites(current_user.id)
        return favorites
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取自选股失败: {str(e)}")

@router.post("/", response_model=FavoriteResponse)
async def add_favorite(
    favorite_data: FavoriteCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """添加自选股"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        favorite_service = FavoriteService(db)
        favorite = await favorite_service.add_favorite(current_user.id, favorite_data)
        return favorite
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加自选股失败: {str(e)}")

@router.put("/{favorite_id}", response_model=FavoriteResponse)
async def update_favorite(
    favorite_id: int,
    favorite_update: FavoriteUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新自选股备注"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        favorite_service = FavoriteService(db)
        favorite = await favorite_service.update_favorite(
            favorite_id, current_user.id, favorite_update
        )
        if not favorite:
            raise HTTPException(status_code=404, detail="自选股不存在")
        
        return favorite
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新自选股失败: {str(e)}")

@router.delete("/{favorite_id}")
async def remove_favorite(
    favorite_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除自选股"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        favorite_service = FavoriteService(db)
        success = await favorite_service.remove_favorite(favorite_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="自选股不存在")
        
        return {"message": "自选股删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除自选股失败: {str(e)}")

@router.delete("/stock/{stock_code}")
async def remove_favorite_by_code(
    stock_code: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """根据股票代码删除自选股"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        favorite_service = FavoriteService(db)
        success = await favorite_service.remove_favorite_by_code(
            current_user.id, stock_code
        )
        if not success:
            raise HTTPException(status_code=404, detail="自选股不存在")
        
        return {"message": "自选股删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除自选股失败: {str(e)}")

@router.get("/realtime")
async def get_favorites_realtime(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取自选股实时行情"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        favorite_service = FavoriteService(db)
        realtime_data = await favorite_service.get_favorites_realtime_data(current_user.id)
        return realtime_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实时行情失败: {str(e)}")

@router.post("/batch")
async def batch_add_favorites(
    stock_codes: List[str],
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """批量添加自选股"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        favorite_service = FavoriteService(db)
        result = await favorite_service.batch_add_favorites(current_user.id, stock_codes)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量添加自选股失败: {str(e)}")