from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService
from app.api.v1.endpoints.auth import oauth2_scheme
from app.services.auth_service import AuthService

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取用户列表（需要管理员权限）"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        user_service = UserService(db)
        users = await user_service.get_users(skip=skip, limit=limit)
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取指定用户信息"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        # 只能查看自己的信息或管理员可以查看所有用户
        if current_user.id != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        # 只能更新自己的信息或管理员可以更新所有用户
        if current_user.id != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        user_service = UserService(db)
        user = await user_service.update_user(user_id, user_update)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户信息失败: {str(e)}")

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除用户（需要管理员权限）"""
    try:
        auth_service = AuthService(db)
        current_user = await auth_service.get_current_user(token)
        
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="不能删除自己")
        
        user_service = UserService(db)
        success = await user_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {"message": "用户删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")