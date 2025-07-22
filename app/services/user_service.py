from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext

from app.database.models import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """用户服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """获取用户列表"""
        users = self.db.query(User).offset(skip).limit(limit).all()
        return [UserResponse.from_orm(user) for user in users]
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """根据ID获取用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            return UserResponse.from_orm(user)
        return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    async def create_user(self, user_create: UserCreate) -> UserResponse:
        """创建用户"""
        # 检查用户名和邮箱是否已存在
        existing_user = self.db.query(User).filter(
            or_(User.username == user_create.username, User.email == user_create.email)
        ).first()
        
        if existing_user:
            if existing_user.username == user_create.username:
                raise ValueError("用户名已存在")
            if existing_user.email == user_create.email:
                raise ValueError("邮箱已存在")
        
        # 创建新用户
        hashed_password = pwd_context.hash(user_create.password)
        
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return UserResponse.from_orm(db_user)
    
    async def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[UserResponse]:
        """更新用户信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # 更新字段
        update_data = user_update.dict(exclude_unset=True)
        
        # 如果更新密码，需要加密
        if 'password' in update_data:
            hashed_password = pwd_context.hash(update_data['password'])
            update_data['hashed_password'] = hashed_password
            del update_data['password']
        
        # 检查邮箱唯一性
        if 'email' in update_data:
            existing_user = self.db.query(User).filter(
                and_(User.email == update_data['email'], User.id != user_id)
            ).first()
            if existing_user:
                raise ValueError("邮箱已存在")
        
        # 更新用户信息
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return UserResponse.from_orm(user)
    
    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    async def activate_user(self, user_id: int) -> bool:
        """激活用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    async def deactivate_user(self, user_id: int) -> bool:
        """停用用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户身份"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user